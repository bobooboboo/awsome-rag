#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用程序主入口
运行示例：python main.py
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os

from app.api.query import init_query_routes
from app.api.data import init_data_routes
from app.api.integration.dify import init_dify_integration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """
    创建Flask应用实例
    
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 启用CORS支持
    CORS(app)
    
    # 配置应用
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON响应
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # 注册查询API路由
    try:
        query_api = init_query_routes(app)
        logger.info("查询API路由注册成功")
    except Exception as e:
        logger.error(f"查询API路由注册失败: {str(e)}")
        raise
    
    # 注册数据API路由
    try:
        data_api = init_data_routes(app)
        logger.info("数据API路由注册成功")
    except Exception as e:
        logger.error(f"数据API路由注册失败: {str(e)}")
        raise
    
    # 注册Dify集成API路由
    try:
        if query_api:  # 只有在QueryAPI成功初始化时才初始化Dify集成
            dify_api_key = os.getenv('DIFY_API_KEY', 'your-dify-api-key')
            init_dify_integration(app, dify_api_key, query_api)
            logger.info("Dify集成API路由注册成功")
        else:
            logger.warning("QueryAPI未成功初始化，跳过Dify集成")
    except Exception as e:
        logger.error(f"Dify集成API路由注册失败: {str(e)}")
        # Dify集成失败不应该阻止整个应用启动
        logger.warning("Dify集成不可用，应用将继续运行")
    
    # 添加健康检查接口
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            "status": "healthy",
            "message": "RAG查询服务运行正常",
            "version": "1.0.0"
        })
    
    # 添加根路径接口
    @app.route('/', methods=['GET'])
    def root():
        """根路径接口"""
        return jsonify({
            "message": "欢迎使用RAG查询服务",
            "version": "1.0.0",
            "endpoints": {
                "查询": {
                    "POST /api/query": "执行详细查询",
                    "GET /api/query": "执行简单查询",
                    "GET /api/query/modes": "获取可用查询模式"
                },
                "数据管理": {
                    "POST /api/data/upload": "上传单个文档",
                    "POST /api/data/batch_upload": "批量上传文档",
                    "POST /api/data/import": "从目录导入文档",
                    "DELETE /api/data/delete": "删除文档",
                    "GET /api/data/list": "查询文档列表",
                    "GET /api/data/stats": "获取数据统计",
                    "GET /api/data/document/{file_id}": "获取文档信息",
                    "GET /api/data/download/{file_id}": "下载文档"
                },
                "Dify集成": {
                    "POST /retrieval": "Dify外部知识库检索接口",
                    "GET /dify/health": "Dify集成健康检查"
                },
                "系统": {
                    "GET /health": "健康检查",
                    "GET /": "服务信息"
                }
            },
            "usage_examples": {
                "内部查询示例": {
                    "url": "/api/query",
                    "method": "POST",
                    "body": {
                        "query": "什么是人工智能？",
                        "top_k": 5,
                        "mode": "vector",
                        "enable_pre_processing": True,
                        "enable_post_processing": True
                    }
                },
                "Dify集成示例": {
                    "url": "/retrieval",
                    "method": "POST",
                    "headers": {
                        "Authorization": "Bearer your-api-key",
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "knowledge_id": "AAA-BBB-CCC",
                        "query": "什么是人工智能？",
                        "retrieval_setting": {
                            "top_k": 5,
                            "score_threshold": 0.5
                        }
                    }
                },
                "GET查询示例": {
                    "url": "/api/query?q=人工智能&top_k=5&mode=vector",
                    "method": "GET"
                },
                "文档上传示例": {
                    "url": "/api/data/upload",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "multipart/form-data"
                    },
                    "body": {
                        "file": "文件对象",
                        "split_strategy": "sentence",
                        "chunk_size": "500",
                        "chunk_overlap": "50",
                        "metadata": "{\"category\": \"技术文档\"}"
                    }
                },
                "目录导入示例": {
                    "url": "/api/data/import",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "directory_path": "/path/to/documents",
                        "recursive": True,
                        "file_pattern": "*.pdf",
                        "split_strategy": "sentence",
                        "chunk_size": 500,
                        "chunk_overlap": 50,
                        "metadata": {"source": "external_docs"}
                    }
                }
            }
        })
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return jsonify({
            "success": False,
            "message": "请求的资源不存在",
            "error_code": 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        logger.error(f"内部服务器错误: {str(error)}")
        return jsonify({
            "success": False,
            "message": "内部服务器错误",
            "error_code": 500
        }), 500
    
    return app

def main():
    """主函数"""
    try:
        # 创建应用
        app = create_app()
        
        # 获取配置
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 5001))
        debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        logger.info(f"启动RAG查询服务...")
        logger.info(f"服务地址: http://{host}:{port}")
        logger.info(f"调试模式: {debug}")
        logger.info(f"主要接口:")
        logger.info(f"  查询接口:")
        logger.info(f"    - POST http://{host}:{port}/api/query")
        logger.info(f"    - GET  http://{host}:{port}/api/query?q=查询内容")
        logger.info(f"    - GET  http://{host}:{port}/api/query/modes")
        logger.info(f"  数据管理接口:")
        logger.info(f"    - POST http://{host}:{port}/api/data/upload")
        logger.info(f"    - POST http://{host}:{port}/api/data/batch_upload")
        logger.info(f"    - POST http://{host}:{port}/api/data/import")
        logger.info(f"    - DELETE http://{host}:{port}/api/data/delete")
        logger.info(f"    - GET  http://{host}:{port}/api/data/list")
        logger.info(f"    - GET  http://{host}:{port}/api/data/stats")
        logger.info(f"    - GET  http://{host}:{port}/api/data/document/{{file_id}}")
        logger.info(f"    - GET  http://{host}:{port}/api/data/download/{{file_id}}")
        logger.info(f"  集成接口:")
        logger.info(f"    - POST http://{host}:{port}/retrieval (Dify集成)")
        logger.info(f"    - GET  http://{host}:{port}/dify/health")
        logger.info(f"  系统接口:")
        logger.info(f"    - GET  http://{host}:{port}/health")
        
        # 启动服务
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True  # 启用多线程支持
        )
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise

if __name__ == '__main__':
    main() 