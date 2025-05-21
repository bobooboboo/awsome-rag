import os
from flask import Flask, jsonify
from pathlib import Path

# 创建Flask应用
app = Flask(__name__)

# 加载配置
from app.config.config import DATA_DIR, VECTOR_STORE_TYPE, FULLTEXT_STORE_TYPE
from app.config.env import check_required_env_vars

# 导入API
from app.api.data import data_api, vector_retrieval
from app.api.query import query_api

# 注册蓝图
app.register_blueprint(data_api)
app.register_blueprint(query_api)

# 创建必要的目录
DATA_DIR.mkdir(exist_ok=True, parents=True)

# 首页路由
@app.route('/')
def index():
    # 检查数据库连接状态
    db_status = "运行中" if vector_retrieval.initialized else "未连接"
    
    return jsonify({
        "status": "OK",
        "message": "RAG系统API服务运行中",
        "database_status": db_status,
        "endpoints": [
            {"url": "/api/data/upload", "method": "POST", "description": "上传文档"},
            {"url": "/api/data/documents", "method": "GET", "description": "列出所有文档"},
            {"url": "/api/data/documents/<document_id>", "method": "DELETE", "description": "删除文档"},
            {"url": "/api/data/query", "method": "POST", "description": "查询文档"},
            {"url": "/api/query", "method": "POST", "description": "执行查询"},
            {"url": "/health", "method": "GET", "description": "健康检查"},
            {"url": "/system-info", "method": "GET", "description": "获取系统配置信息"}
        ]
    })

# 健康检查端点
@app.route('/health')
def health_check():
    """
    健康检查端点，返回系统各组件的状态
    """
    health_data = {
        "status": "healthy",
        "components": {
            "api": "运行中",
            "database": "运行中" if vector_retrieval.initialized else "未连接",
            "file_storage": "可用" if DATA_DIR.exists() and os.access(DATA_DIR, os.W_OK) else "不可用"
        },
        "details": {
            "database_message": "数据库连接正常" if vector_retrieval.initialized else "数据库连接失败，请检查配置",
        }
    }
    
    # 如果任何关键组件不可用，则整体状态为不健康
    if not vector_retrieval.initialized or not (DATA_DIR.exists() and os.access(DATA_DIR, os.W_OK)):
        health_data["status"] = "unhealthy"
    
    return jsonify(health_data)

# 系统信息端点
@app.route('/system-info')
def system_info():
    """获取系统配置信息"""
    try:
        from app.data_indexing.index_creator import IndexCreatorFactory
        from app.data_source.vector.factory import VectorStoreFactory 
        from app.data_source.full_text.factory import FullTextStoreFactory
        
        factories = {
            "vector_store_type": VECTOR_STORE_TYPE,
            "fulltext_store_type": FULLTEXT_STORE_TYPE,
            "vector_store": VectorStoreFactory.create().__class__.__name__,
            "fulltext_store": FullTextStoreFactory.create().__class__.__name__,
        }
        
        # 尝试创建索引创建器，如果可能
        try:
            factories.update({
                "vector_creator": IndexCreatorFactory.create("vector").__class__.__name__,
                "fulltext_creator": IndexCreatorFactory.create("fulltext").__class__.__name__,
                "hybrid_creator": IndexCreatorFactory.create("hybrid").__class__.__name__,
            })
        except Exception as e:
            factories["creator_error"] = str(e)
            
        return jsonify({
            "vector_store_type": VECTOR_STORE_TYPE,
            "fulltext_store_type": FULLTEXT_STORE_TYPE,
            "data_dir": str(DATA_DIR),
            "factories": factories
        })
        
    except Exception as e:
        return jsonify({
            "error": f"获取系统信息失败: {str(e)}"
        }), 500

# 处理404错误
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "请求的端点不存在"}), 404

# 处理500错误
@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "服务器内部错误"}), 500

# 启动应用
if __name__ == "__main__":
    # 检查环境变量
    check_required_env_vars()
    
    # 获取端口
    port = int(os.environ.get("PORT", 5000))
    
    # 数据库连接状态
    if not vector_retrieval.initialized:
        print("\n警告: 数据库连接失败。")
        print("将在没有向量检索功能的情况下启动服务。")
        print("提示: 请检查数据库配置并确保数据库服务已启动。\n")
    else:
        print("\n数据库连接成功，所有功能正常运行。\n")
    
    # 启动服务
    app.run(host="0.0.0.0", port=port, debug=True) 