import logging
import os
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import Flask, request, jsonify, send_file
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.config.config import STORING_CONFIG
from app.data_indexing.file.document_loader.local_file import LocalFileLoader
from app.data_indexing.file.document_splitter.document_splitter_factory import DocumentSplitterFactory
from app.data_source.vector.factory import VectorStoreFactory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAPI:
    """
    数据API类，提供文档的上传、删除、查询和批量导入功能
    """

    def __init__(self, app: Flask = None):
        """
        初始化数据API
        
        Args:
            app: Flask应用实例
        """
        self.app: Flask = app
        self.file_loader = None
        self.vector_store = None
        
        # 文档存储配置
        self.upload_dir = Path(STORING_CONFIG.get("upload_dir", "~/storage/uploads"))
        
        # 支持的文件类型
        self.allowed_extensions = {
            'txt', 'pdf', 'doc', 'docx', 'html', 'htm', 
            'md', 'markdown', 'csv', 'xls', 'xlsx'
        }
        
        # 文件类型与MIME类型的映射
        self.mime_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'html': 'text/html',
            'htm': 'text/html',
            'md': 'text/markdown',
            'markdown': 'text/markdown',
            'csv': 'text/csv',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """
        初始化Flask应用和相关组件
        
        Args:
            app: Flask应用实例
        """
        self.app = app
        
        # 创建存储目录
        self._ensure_storage_directories()
        
        # 初始化文档加载器
        self.file_loader = LocalFileLoader()
        
        # 初始化存储实例
        try:
            self.vector_store = VectorStoreFactory.create()
            logger.info("数据存储组件初始化成功")
        except Exception as e:
            logger.error(f"数据存储组件初始化失败: {str(e)}")
            raise
        
        # 注册路由
        self._register_routes()

    def _ensure_storage_directories(self):
        """确保存储目录存在"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"上传目录配置: {self.upload_dir}")

    def _allowed_file(self, filename: str) -> bool:
        """
        检查文件类型是否允许
        
        Args:
            filename: 文件名
            
        Returns:
            是否允许的文件类型
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def _get_file_info_by_id(self, file_id: str) -> Dict[str, Any] | None:
        """
        根据文件ID获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件信息字典，如果未找到返回None
        """
        try:
            # 从向量库查询文件信息
            nodes = self.vector_store.get_data(filters={"file_id": file_id})
            
            if not nodes:
                return None
            
            # 从第一个节点获取文件元数据
            first_node = nodes[0]
            if not first_node.metadata:
                return None
            
            metadata = first_node.metadata
            file_path = metadata.get('file_path')
            
            # 检查物理文件是否存在
            if not file_path or not os.path.exists(file_path):
                return None
            
            # 获取文件信息
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            
            # 格式化文件大小
            if file_size > 1024 * 1024 * 1024:
                file_size_str = f"{file_size / (1024 * 1024 * 1024):.2f}GB"
            elif file_size > 1024 * 1024:
                file_size_str = f"{file_size / (1024 * 1024):.2f}MB"
            elif file_size > 1024:
                file_size_str = f"{file_size / 1024:.2f}KB"
            else:
                file_size_str = f"{file_size}B"
            
            # 获取文件类型
            file_name = metadata.get('file_name', '')
            file_ext = file_name.split('.')[-1].lower() if '.' in file_name else 'unknown'
            
            return {
                "file_id": file_id,
                "file_name": metadata.get('file_name', 'unknown'),
                "file_path": file_path,
                "file_size": file_size_str,
                "file_size_bytes": file_size,
                "file_type": file_ext,
                "upload_time": metadata.get('upload_time', ''),
                "node_count": len(nodes),
                "metadata": {k: v for k, v in metadata.items() 
                           if k not in ['file_path']}  # 不暴露文件路径
            }
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return None

    def _get_mime_type(self, filename: str) -> str:
        """
        根据文件名获取MIME类型
        
        Args:
            filename: 文件名
            
        Returns:
            MIME类型字符串
        """
        if '.' not in filename:
            return 'application/octet-stream'
        
        ext = filename.split('.')[-1].lower()
        return self.mime_types.get(ext, 'application/octet-stream')

    def _save_uploaded_file(self, file: FileStorage, custom_filename: str = None) -> tuple:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件对象
            custom_filename: 自定义文件名
            
        Returns:
            (文件路径, 文件ID, 原始文件名)
        """
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        
        # 获取文件扩展名
        if file.filename:
            file_ext = Path(file.filename).suffix
            original_filename = file.filename
        else:
            file_ext = ""
            original_filename = "unknown"
        
        # 确定最终文件名
        if custom_filename:
            final_filename = secure_filename(custom_filename) + file_ext
        else:
            final_filename = f"{file_id}{file_ext}"
        
        # 保存文件
        file_path = self.upload_dir / final_filename
        file.save(str(file_path))
        
        logger.info(f"文件保存成功: {file_path}")
        return str(file_path), file_id, original_filename

    def _process_document(
        self, 
        file_path: str, 
        file_id: str, 
        original_filename: str,
        split_strategy: str = "sentence",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        处理文档：加载、解析、拆分、存储
        
        Args:
            file_path: 文件路径
            file_id: 文件ID
            original_filename: 原始文件名
            split_strategy: 拆分策略
            chunk_size: 块大小
            chunk_overlap: 块重叠
            metadata: 额外元数据
            
        Returns:
            处理结果信息
        """
        start_time = time.time()
        
        try:
            # 1. 加载文档
            logger.info(f"开始加载文档: {file_path}")
            documents = self.file_loader.load_documents(file_path)
            logger.info(f"文档加载完成，共 {len(documents)} 个文档")
            
            # 2. 创建文档拆分器
            splitter = DocumentSplitterFactory.create(
                split_strategy=split_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # 3. 拆分文档
            logger.info("开始拆分文档")
            nodes = splitter.get_nodes_from_documents(documents, show_progress=True)
            logger.info(f"文档拆分完成，共 {len(nodes)} 个节点")
            
            # 4. 添加元数据
            base_metadata = {
                "file_id": file_id,
                "file_name": original_filename,
                "file_path": file_path,
                "upload_time": datetime.now().isoformat(),
                "split_strategy": split_strategy,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
            
            if metadata:
                base_metadata.update(metadata)
            
            # 为每个节点添加元数据
            for node in nodes:
                if node.metadata is None:
                    node.metadata = {}
                node.metadata.update(base_metadata)
            
            # 5. 存储到向量库
            logger.info("开始存储到向量库")
            self.vector_store.add_data(nodes)
            logger.info("向量库存储完成")
            
            processing_time = time.time() - start_time
            
            return {
                "file_id": file_id,
                "file_name": original_filename,
                "file_path": file_path,
                "document_count": len(documents),
                "node_count": len(nodes),
                "processing_time": processing_time,
                "metadata": base_metadata
            }
            
        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
            # 清理已保存的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    def _register_routes(self):
        """注册API路由"""

        @self.app.route('/api/data/upload', methods=['POST'])
        def upload_document():
            """
            上传单个文档
            
            请求参数:
            - file: 文件对象 (form-data)
            - filename: 自定义文件名 (可选)
            - split_strategy: 拆分策略 (可选，默认: sentence)
            - chunk_size: 块大小 (可选，默认: 500)
            - chunk_overlap: 块重叠 (可选，默认: 50)
            - metadata: JSON格式的额外元数据 (可选)
            
            返回格式:
            {
                "success": true,
                "data": {
                    "file_id": "uuid",
                    "file_name": "document.pdf",
                    "document_count": 1,
                    "node_count": 10,
                    "processing_time": 1.23
                },
                "message": "文档上传成功"
            }
            """
            return self._handle_upload()

        @self.app.route('/api/data/batch_upload', methods=['POST'])
        def batch_upload_documents():
            """
            批量上传文档
            
            请求参数:
            - files: 多个文件对象 (form-data)
            - split_strategy: 拆分策略 (可选，默认: sentence)
            - chunk_size: 块大小 (可选，默认: 500)
            - chunk_overlap: 块重叠 (可选，默认: 50)
            - metadata: JSON格式的额外元数据 (可选)
            
            返回格式:
            {
                "success": true,
                "data": {
                    "uploaded_files": [...],
                    "failed_files": [...],
                    "total_files": 5,
                    "success_count": 4,
                    "fail_count": 1,
                    "total_processing_time": 12.34
                },
                "message": "批量上传完成"
            }
            """
            return self._handle_batch_upload()

        @self.app.route('/api/data/import', methods=['POST'])
        def import_from_directory():
            """
            从目录批量导入文档
            
            请求体格式:
            {
                "directory_path": "/path/to/documents",
                "recursive": true,
                "file_pattern": "*.pdf",
                "split_strategy": "sentence",
                "chunk_size": 500,
                "chunk_overlap": 50,
                "metadata": {}
            }
            
            返回格式:
            {
                "success": true,
                "data": {
                    "imported_files": [...],
                    "failed_files": [...],
                    "total_files": 10,
                    "success_count": 9,
                    "fail_count": 1,
                    "total_processing_time": 45.67
                },
                "message": "目录导入完成"
            }
            """
            return self._handle_directory_import()

        @self.app.route('/api/data/delete', methods=['DELETE'])
        def delete_documents():
            """
            删除文档
            
            请求体格式:
            {
                "file_ids": ["uuid1", "uuid2"],  // 按文件ID删除
                "filters": {                     // 或按条件删除
                    "file_name": "document.pdf",
                    "upload_time": "2024-01-01"
                },
                "delete_files": true             // 是否同时删除物理文件
            }
            
            返回格式:
            {
                "success": true,
                "data": {
                    "deleted_file_ids": [...],
                    "deleted_count": 5,
                    "physical_files_deleted": 3
                },
                "message": "文档删除成功"
            }
            """
            return self._handle_delete()

        @self.app.route('/api/data/list', methods=['GET'])
        def list_documents():
            """
            查询文档列表
            
            查询参数:
            - page: 页码 (默认: 1)
            - page_size: 每页大小 (默认: 20)
            - file_name: 文件名过滤
            - file_id: 文件ID过滤
            - upload_time_start: 上传时间开始
            - upload_time_end: 上传时间结束
            
            返回格式:
            {
                "success": true,
                "data": {
                    "documents": [...],
                    "total": 100,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 5
                },
                "message": "查询成功"
            }
            """
            return self._handle_list()

        @self.app.route('/api/data/stats', methods=['GET'])
        def get_stats():
            """
            获取数据统计信息
            
            返回格式:
            {
                "success": true,
                "data": {
                    "total_files": 100,
                    "total_nodes": 5000,
                    "storage_size": "1.2GB",
                    "file_types": {
                        "pdf": 50,
                        "docx": 30,
                        "txt": 20
                    },
                    "upload_timeline": {...}
                },
                "message": "统计信息获取成功"
            }
            """
            return self._handle_stats()

        @self.app.route('/api/data/document/<file_id>', methods=['GET'])
        def get_document_info(file_id):
            """
            获取文档信息
            
            路径参数:
            - file_id: 文件ID
            
            返回格式:
            {
                "success": true,
                "data": {
                    "file_id": "uuid-string",
                    "file_name": "document.pdf",
                    "file_size": "1.2MB",
                    "file_type": "pdf",
                    "upload_time": "2024-01-01T10:00:00",
                    "node_count": 15,
                    "download_url": "/api/data/download/uuid-string",
                    "metadata": {...}
                },
                "message": "文档信息获取成功"
            }
            """
            return self._handle_get_document_info(file_id)

        @self.app.route('/api/data/download/<file_id>', methods=['GET'])
        def download_document(file_id):
            """
            下载文档
            
            路径参数:
            - file_id: 文件ID
            
            返回:
            - 成功时返回文件流
            - 失败时返回JSON错误信息
            """
            return self._handle_download_document(file_id)

    def _handle_upload(self) -> tuple:
        """处理单个文档上传"""
        try:
            # 检查文件
            if 'file' not in request.files:
                return jsonify({
                    "success": False,
                    "message": "未找到上传文件"
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    "success": False,
                    "message": "未选择文件"
                }), 400
            
            if not self._allowed_file(file.filename):
                return jsonify({
                    "success": False,
                    "message": f"不支持的文件类型，支持的类型: {', '.join(self.allowed_extensions)}"
                }), 400
            
            # 获取参数
            custom_filename = request.form.get('filename')
            split_strategy = request.form.get('split_strategy', 'sentence')
            chunk_size = int(request.form.get('chunk_size', 500))
            chunk_overlap = int(request.form.get('chunk_overlap', 50))
            
            # 解析元数据
            metadata = {}
            if 'metadata' in request.form:
                import json
                try:
                    metadata = json.loads(request.form['metadata'])
                except json.JSONDecodeError:
                    return jsonify({
                        "success": False,
                        "message": "元数据格式错误，请使用有效的JSON格式"
                    }), 400
            
            # 保存文件
            file_path, file_id, original_filename = self._save_uploaded_file(file, custom_filename)
            
            # 处理文档
            result = self._process_document(
                file_path, file_id, original_filename,
                split_strategy, chunk_size, chunk_overlap, metadata
            )
            
            return jsonify({
                "success": True,
                "data": result,
                "message": "文档上传成功"
            }), 200
            
        except Exception as e:
            logger.error(f"文档上传失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"文档上传失败: {str(e)}"
            }), 500

    def _handle_batch_upload(self) -> tuple:
        """处理批量文档上传"""
        try:
            # 检查文件
            if 'files' not in request.files:
                return jsonify({
                    "success": False,
                    "message": "未找到上传文件"
                }), 400
            
            files = request.files.getlist('files')
            if not files or len(files) == 0:
                return jsonify({
                    "success": False,
                    "message": "未选择文件"
                }), 400
            
            # 获取参数
            split_strategy = request.form.get('split_strategy', 'sentence')
            chunk_size = int(request.form.get('chunk_size', 500))
            chunk_overlap = int(request.form.get('chunk_overlap', 50))
            
            # 解析元数据
            metadata = {}
            if 'metadata' in request.form:
                import json
                try:
                    metadata = json.loads(request.form['metadata'])
                except json.JSONDecodeError:
                    return jsonify({
                        "success": False,
                        "message": "元数据格式错误，请使用有效的JSON格式"
                    }), 400
            
            uploaded_files = []
            failed_files = []
            total_time = time.time()
            
            for file in files:
                try:
                    if file.filename == '' or not self._allowed_file(file.filename):
                        failed_files.append({
                            "filename": file.filename,
                            "error": "不支持的文件类型或文件名为空"
                        })
                        continue
                    
                    # 保存文件
                    file_path, file_id, original_filename = self._save_uploaded_file(file)
                    
                    # 处理文档
                    result = self._process_document(
                        file_path, file_id, original_filename,
                        split_strategy, chunk_size, chunk_overlap, metadata
                    )
                    
                    uploaded_files.append(result)
                    
                except Exception as e:
                    failed_files.append({
                        "filename": file.filename,
                        "error": str(e)
                    })
                    logger.error(f"处理文件 {file.filename} 失败: {str(e)}")
            
            total_time = time.time() - total_time
            
            return jsonify({
                "success": True,
                "data": {
                    "uploaded_files": uploaded_files,
                    "failed_files": failed_files,
                    "total_files": len(files),
                    "success_count": len(uploaded_files),
                    "fail_count": len(failed_files),
                    "total_processing_time": total_time
                },
                "message": "批量上传完成"
            }), 200
            
        except Exception as e:
            logger.error(f"批量上传失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"批量上传失败: {str(e)}"
            }), 500

    def _handle_directory_import(self) -> tuple:
        """处理目录导入"""
        try:
            data = request.get_json()
            
            if not data or 'directory_path' not in data:
                return jsonify({
                    "success": False,
                    "message": "请提供directory_path参数"
                }), 400
            
            directory_path = Path(data['directory_path'])
            if not directory_path.exists() or not directory_path.is_dir():
                return jsonify({
                    "success": False,
                    "message": "指定的目录不存在"
                }), 400
            
            # 获取参数
            recursive = data.get('recursive', True)
            file_pattern = data.get('file_pattern', '*')
            split_strategy = data.get('split_strategy', 'sentence')
            chunk_size = data.get('chunk_size', 500)
            chunk_overlap = data.get('chunk_overlap', 50)
            metadata = data.get('metadata', {})
            
            # 查找文件
            if recursive:
                files = list(directory_path.rglob(file_pattern))
            else:
                files = list(directory_path.glob(file_pattern))
            
            # 过滤支持的文件类型
            supported_files = [f for f in files if f.is_file() and self._allowed_file(f.name)]
            
            if not supported_files:
                return jsonify({
                    "success": False,
                    "message": "目录中未找到支持的文件类型"
                }), 400
            
            imported_files = []
            failed_files = []
            total_time = time.time()
            
            for file_path in supported_files:
                try:
                    # 生成文件ID
                    file_id = str(uuid.uuid4())
                    
                    # 复制文件到存储目录
                    dest_path = self.upload_dir / f"{file_id}{file_path.suffix}"
                    shutil.copy2(str(file_path), str(dest_path))
                    
                    # 处理文档
                    result = self._process_document(
                        str(dest_path), file_id, file_path.name,
                        split_strategy, chunk_size, chunk_overlap, metadata
                    )
                    
                    result['source_path'] = str(file_path)
                    imported_files.append(result)
                    
                except Exception as e:
                    failed_files.append({
                        "filename": file_path.name,
                        "source_path": str(file_path),
                        "error": str(e)
                    })
                    logger.error(f"导入文件 {file_path} 失败: {str(e)}")
            
            total_time = time.time() - total_time
            
            return jsonify({
                "success": True,
                "data": {
                    "imported_files": imported_files,
                    "failed_files": failed_files,
                    "total_files": len(supported_files),
                    "success_count": len(imported_files),
                    "fail_count": len(failed_files),
                    "total_processing_time": total_time
                },
                "message": "目录导入完成"
            }), 200
            
        except Exception as e:
            logger.error(f"目录导入失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"目录导入失败: {str(e)}"
            }), 500

    def _handle_delete(self) -> tuple:
        """处理文档删除"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "success": False,
                    "message": "请提供删除条件"
                }), 400
            
            file_ids = data.get('file_ids', [])
            filters = data.get('filters', {})
            delete_files = data.get('delete_files', False)
            
            if not file_ids and not filters:
                return jsonify({
                    "success": False,
                    "message": "请提供file_ids或filters参数"
                }), 400
            
            deleted_file_ids = []
            physical_files_deleted = 0
            
            # 如果提供了file_ids，按ID删除
            if file_ids:
                # 先获取要删除的节点信息，用于删除物理文件
                if delete_files:
                    try:
                        nodes = self.vector_store.get_data(filters={"file_id": file_ids})
                        file_paths = set()
                        for node in nodes:
                            if node.metadata and 'file_path' in node.metadata:
                                file_paths.add(node.metadata['file_path'])
                        
                        # 删除物理文件
                        for file_path in file_paths:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                physical_files_deleted += 1
                                logger.info(f"已删除物理文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除物理文件时出错: {str(e)}")
                
                # 从向量库删除
                self.vector_store.delete_data(filters={"file_id": file_ids})
                
                deleted_file_ids = file_ids
            
            # 按过滤条件删除
            elif filters:
                # 先获取要删除的节点信息
                try:
                    nodes = self.vector_store.get_data(filters=filters)
                    file_ids_to_delete = set()
                    file_paths = set()
                    
                    for node in nodes:
                        if node.metadata:
                            if 'file_id' in node.metadata:
                                file_ids_to_delete.add(node.metadata['file_id'])
                            if delete_files and 'file_path' in node.metadata:
                                file_paths.add(node.metadata['file_path'])
                    
                    # 删除物理文件
                    if delete_files:
                        for file_path in file_paths:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                physical_files_deleted += 1
                                logger.info(f"已删除物理文件: {file_path}")
                    
                    deleted_file_ids = list(file_ids_to_delete)
                    
                except Exception as e:
                    logger.warning(f"获取删除节点信息时出错: {str(e)}")
                
                # 从向量库删除
                self.vector_store.delete_data(filters=filters)
            
            return jsonify({
                "success": True,
                "data": {
                    "deleted_file_ids": deleted_file_ids,
                    "deleted_count": len(deleted_file_ids),
                    "physical_files_deleted": physical_files_deleted
                },
                "message": "文档删除成功"
            }), 200
            
        except Exception as e:
            logger.error(f"文档删除失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"文档删除失败: {str(e)}"
            }), 500

    def _handle_list(self) -> tuple:
        """处理文档列表查询"""
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 20))
            file_name = request.args.get('file_name')
            file_id = request.args.get('file_id')
            upload_time_start = request.args.get('upload_time_start')
            # upload_time_end = request.args.get('upload_time_end')
            
            # 构建过滤条件
            filters = {}
            if file_name:
                filters['file_name'] = f"%{file_name}%"
            if file_id:
                filters['file_id'] = file_id
            if upload_time_start:
                # 这里简化处理，实际可能需要更复杂的时间范围查询
                filters['upload_time'] = f"%{upload_time_start}%"
            
            # 获取数据
            nodes = self.vector_store.get_data(filters=filters if filters else None)
            
            # 按文件分组
            files_dict = {}
            for node in nodes:
                if node.metadata and 'file_id' in node.metadata:
                    file_id = node.metadata['file_id']
                    if file_id not in files_dict:
                        files_dict[file_id] = {
                            "file_id": file_id,
                            "file_name": node.metadata.get('file_name', 'unknown'),
                            "file_path": node.metadata.get('file_path', ''),
                            "upload_time": node.metadata.get('upload_time', ''),
                            "split_strategy": node.metadata.get('split_strategy', ''),
                            "chunk_size": node.metadata.get('chunk_size', 0),
                            "chunk_overlap": node.metadata.get('chunk_overlap', 0),
                            "node_count": 0
                        }
                    files_dict[file_id]["node_count"] += 1
            
            # 转换为列表并分页
            documents = list(files_dict.values())
            total = len(documents)
            total_pages = (total + page_size - 1) // page_size
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_documents = documents[start_idx:end_idx]
            
            return jsonify({
                "success": True,
                "data": {
                    "documents": page_documents,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages
                },
                "message": "查询成功"
            }), 200
            
        except Exception as e:
            logger.error(f"文档列表查询失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"文档列表查询失败: {str(e)}"
            }), 500

    def _handle_stats(self) -> tuple:
        """处理统计信息查询"""
        try:
            # 获取所有节点
            nodes = self.vector_store.get_data()
            
            # 统计信息
            total_nodes = len(nodes)
            files_dict = {}
            file_types = {}
            
            for node in nodes:
                if node.metadata:
                    # 文件统计
                    file_id = node.metadata.get('file_id')
                    if file_id and file_id not in files_dict:
                        files_dict[file_id] = True
                        
                        # 文件类型统计
                        file_name = node.metadata.get('file_name', '')
                        if '.' in file_name:
                            ext = file_name.split('.')[-1].lower()
                            file_types[ext] = file_types.get(ext, 0) + 1
            
            total_files = len(files_dict)
            
            # 计算存储大小（简化版本）
            storage_size = "未知"
            try:
                if self.upload_dir.exists():
                    total_size = sum(f.stat().st_size for f in self.upload_dir.rglob('*') if f.is_file())
                    if total_size > 1024 * 1024 * 1024:
                        storage_size = f"{total_size / (1024 * 1024 * 1024):.2f}GB"
                    elif total_size > 1024 * 1024:
                        storage_size = f"{total_size / (1024 * 1024):.2f}MB"
                    else:
                        storage_size = f"{total_size / 1024:.2f}KB"
            except Exception as e:
                logger.warning(f"计算存储大小失败: {str(e)}")
            
            return jsonify({
                "success": True,
                "data": {
                    "total_files": total_files,
                    "total_nodes": total_nodes,
                    "storage_size": storage_size,
                    "file_types": file_types,
                    "upload_timeline": "暂未实现"  # 可以后续实现按时间统计
                },
                "message": "统计信息获取成功"
            }), 200
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"获取统计信息失败: {str(e)}"
            }), 500

    def _handle_get_document_info(self, file_id: str) -> tuple:
        """处理获取文档信息请求"""
        try:
            # 验证file_id格式
            if not file_id or not file_id.strip():
                return jsonify({
                    "success": False,
                    "message": "文件ID不能为空"
                }), 400
            
            # 获取文件信息
            file_info = self._get_file_info_by_id(file_id)
            
            if not file_info:
                return jsonify({
                    "success": False,
                    "message": "文档不存在或已被删除"
                }), 404
            
            # 添加下载链接
            file_info["download_url"] = f"/api/data/download/{file_id}"
            
            return jsonify({
                "success": True,
                "data": file_info,
                "message": "文档信息获取成功"
            }), 200
            
        except Exception as e:
            logger.error(f"获取文档信息失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"获取文档信息失败: {str(e)}"
            }), 500

    def _handle_download_document(self, file_id: str):
        """处理文档下载请求"""
        try:
            # 验证file_id格式
            if not file_id or not file_id.strip():
                return jsonify({
                    "success": False,
                    "message": "文件ID不能为空"
                }), 400
            
            # 获取文件信息
            file_info = self._get_file_info_by_id(file_id)
            
            if not file_info:
                return jsonify({
                    "success": False,
                    "message": "文档不存在或已被删除"
                }), 404
            
            file_path = file_info["file_path"]
            file_name = file_info["file_name"]
            
            # 再次确认文件存在
            if not os.path.exists(file_path):
                return jsonify({
                    "success": False,
                    "message": "文档文件不存在"
                }), 404
            
            # 获取MIME类型
            mime_type = self._get_mime_type(file_name)
            
            # 使用Flask的send_file发送文件
            try:
                return send_file(
                    file_path,
                    mimetype=mime_type,
                    as_attachment=True,
                    download_name=file_name
                )
            except Exception as send_error:
                logger.error(f"发送文件失败: {str(send_error)}")
                return jsonify({
                    "success": False,
                    "message": "文件下载失败"
                }), 500
            
        except Exception as e:
            logger.error(f"文档下载失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"文档下载失败: {str(e)}"
            }), 500


def init_data_routes(app: Flask) -> DataAPI:
    """
    初始化数据API路由
    
    Args:
        app: Flask应用实例
        
    Returns:
        DataAPI实例
    """
    data_api = DataAPI(app)
    logger.info("数据API路由注册成功")
    return data_api
