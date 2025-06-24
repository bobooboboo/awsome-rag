import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

from flask import Flask, request, jsonify, Response
from llama_index.core.schema import NodeWithScore

from app.query_construction.service import QueryService
from app.query_processing.query_post.post_processor_chain import PostProcessorChain
from app.query_processing.query_post.rerank_processor import RerankProcessor
from app.query_processing.query_pre.pre_query_chain import PreQueryProcessorChain
from app.query_processing.query_pre.question_optimization_processor import QuestionOptimizerProcessor
from app.query_processing.query_pre.sensitive_word_processor import SensitiveWordProcessor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryAPI:
    """
    查询API类，提供完整的查询功能
    """

    def __init__(self, app: Flask = None):
        """
        初始化查询API
        
        Args:
            app: Flask应用实例
        """
        self.app: Flask = app
        self.query_service = None
        self.pre_processor_chain = None
        self.post_processor_chain = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """
        初始化Flask应用和相关组件
        
        Args:
            app: Flask应用实例
        """
        self.app = app

        # 初始化查询服务
        self.query_service = QueryService()

        # 初始化查询前处理链
        pre_processors = [
            SensitiveWordProcessor(),  # 敏感词处理
            QuestionOptimizerProcessor()  # 问题优化
        ]
        self.pre_processor_chain = PreQueryProcessorChain(pre_processors)

        # 初始化查询后处理链
        post_processors = [
            RerankProcessor()  # 重排序处理
        ]
        self.post_processor_chain = PostProcessorChain(post_processors)

        # 注册路由
        self._register_routes()

    def execute_query(
            self,
            query_text: str,
            top_k: int = 5,
            filters: Dict[str, Any] = None,
            enable_pre_processing: bool = True,
            enable_post_processing: bool = True,
            params: Dict[str, Any] = None
    ) -> List:
        """
        执行查询的核心逻辑，不涉及Flask请求处理
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            enable_pre_processing: 是否启用查询前处理
            enable_post_processing: 是否启用查询后处理
            params: 查询参数
            
        Returns:
            NodeWithScore结果列表
        """
        if filters is None:
            filters = {}
        if params is None:
            params = {}

        return self._query(query_text, top_k, filters, params, enable_pre_processing, enable_post_processing)

    def _query(self, query_text: str, top_k: int = 5, filters: Dict[str, Any] = None,
               params: Dict[str, Any] = None,
               enable_pre_processing: bool = True,
               enable_post_processing: bool = True) -> List[NodeWithScore]:
        logger.info(f"执行查询: {query_text[:50]}...")

        # 查询前处理
        processed_query = query_text
        if enable_pre_processing and self.pre_processor_chain:
            try:
                processed_query = self.pre_processor_chain.postprocess_nodes(query_text)
                logger.info(f"查询前处理完成: {processed_query[:50]}...")
            except Exception as e:
                logger.warning(f"查询前处理失败: {str(e)}")
                # 即使前处理失败，也继续使用原始查询
                processed_query = query_text

        # 执行查询
        results = self.query_service.query(
            query_text=processed_query,
            top_k=top_k,
            filters=filters,
            params=params
        )

        # 查询后处理
        if enable_post_processing and self.post_processor_chain:
            try:
                results = self.post_processor_chain.postprocess_nodes(results, processed_query)
                logger.info("查询后处理完成")
            except Exception as e:
                logger.warning(f"查询后处理失败: {str(e)}")
                # 即使后处理失败，也返回原始结果

        return results

    def _register_routes(self):
        """注册API路由"""

        @self.app.route('/api/query', methods=['POST'])
        def query():
            """
            执行查询
            
            请求体格式:
            {
                "query": "查询文本",
                "top_k": 5,
                "mode": "vector",  // 可选: vector, text, hybrid, sparse, semantic_hybrid
                "filters": {},     // 可选: 元数据过滤条件
                "enable_pre_processing": true,   // 可选: 是否启用查询前处理
                "enable_post_processing": true,  // 可选: 是否启用查询后处理
                "alpha": 0.7,      // 可选: 混合检索权重参数
                "include_metadata": true  // 可选: 是否包含元数据
            }
            
            返回格式:
            {
                "success": true,
                "data": {
                    "results": [...],
                    "processed_query": "处理后的查询文本",
                    "total_results": 5,
                    "search_mode": "vector",
                    "execution_time": 0.123
                },
                "message": "查询成功"
            }
            """
            return self._handle_query()

        @self.app.route('/api/query/modes', methods=['GET'])
        def get_available_modes():
            """获取可用的查询模式"""
            return jsonify({
                "success": True,
                "data": {
                    "modes": [
                        {
                            "name": "vector",
                            "description": "向量检索，基于语义相似度"
                        },
                        {
                            "name": "text",
                            "description": "全文检索，基于关键词匹配"
                        },
                        {
                            "name": "hybrid",
                            "description": "混合检索，结合向量和全文检索"
                        },
                        {
                            "name": "sparse",
                            "description": "稀疏向量检索"
                        },
                        {
                            "name": "semantic_hybrid",
                            "description": "语义混合检索"
                        }
                    ]
                },
                "message": "获取查询模式成功"
            })

    def _handle_query(self) -> Tuple[Response, int]:
        """处理POST查询请求"""
        try:
            start_time = time.time()

            # 获取请求数据
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "message": "请求体不能为空"
                }), 400

            # 验证必需参数
            query_text = data.get('query')
            if not query_text or not query_text.strip():
                return jsonify({
                    "success": False,
                    "message": "查询文本不能为空"
                }), 400

            # 解析参数
            top_k = int(data.get('top_k', 5))
            if top_k <= 0 or top_k > 100:
                return jsonify({
                    "success": False,
                    "message": "top_k参数必须在1-100之间"
                }), 400

            filters = data.get('filters', {})
            enable_pre_processing = data.get('enable_pre_processing', True)
            enable_post_processing = data.get('enable_post_processing', True)
            include_metadata = data.get('include_metadata', True)

            # 构建查询参数
            params = {}
            if 'mode' in data:
                params['mode'] = data['mode']
            if 'alpha' in data:
                params['alpha'] = data['alpha']



            # 执行查询
            results = self._query(query_text, top_k, filters, params, enable_pre_processing, enable_post_processing)

            # 直接返回NodeWithScore结果，进行简单的序列化处理
            formatted_results = self._serialize_node_with_score(results, include_metadata)

            execution_time = time.time() - start_time

            # 确定使用的搜索模式
            search_mode = self.query_service.router.determine_mode(params)

            response_data = {
                "results": formatted_results,
                # "processed_query": processed_query if enable_pre_processing else query_text,
                "original_query": query_text,
                "total_results": len(formatted_results),
                "search_mode": search_mode,
                "execution_time": round(execution_time, 4),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"查询完成，返回{len(formatted_results)}个结果，耗时{execution_time:.4f}秒")

            return jsonify({
                "success": True,
                "data": response_data,
                "message": "查询成功"
            }), 200

        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "message": f"查询处理失败: {str(e)}"
            }), 500

    @staticmethod
    def _serialize_node_with_score(results: List, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        将NodeWithScore结果序列化为可JSON化的格式
        
        Args:
            results: NodeWithScore结果列表
            include_metadata: 是否包含元数据
            
        Returns:
            序列化后的结果列表
        """
        serialized_results = []

        for result in results:
            # 基本的序列化信息
            serialized_result = {
                "node_id": getattr(result.node, 'id_', None),
                "text": getattr(result.node, 'text', str(result.node)),
                "score": float(result.score) if hasattr(result, 'score') else 0.0,
            }

            # 可选的元数据
            if include_metadata and hasattr(result.node, 'metadata') and result.node.metadata:
                serialized_result["metadata"] = result.node.metadata

            # 可选的其他NodeWithScore属性
            if hasattr(result, 'node') and result.node:
                # 如果有embedding信息
                if hasattr(result.node, 'embedding') and result.node.embedding:
                    # 只返回embedding的维度信息，不返回具体数值（避免响应过大）
                    serialized_result["embedding_dim"] = len(result.node.embedding)

                # 如果有relationships信息
                if hasattr(result.node, 'relationships') and result.node.relationships:
                    serialized_result["has_relationships"] = True
                    serialized_result["relationship_count"] = len(result.node.relationships)

            serialized_results.append(serialized_result)

        return serialized_results


# def create_query_api(app: Flask = None) -> QueryAPI:
#     """
#     创建查询API实例
#
#     Args:
#         app: Flask应用实例
#
#     Returns:
#         QueryAPI实例
#     """
#     return QueryAPI(app)


# 为了兼容性，提供直接函数接口
def init_query_routes(app: Flask) -> QueryAPI:
    """
    初始化查询路由（函数式接口）
    
    Args:
        app: Flask应用实例
        
    Returns:
        QueryAPI实例
    """
    query_api = QueryAPI(app)
    return query_api
