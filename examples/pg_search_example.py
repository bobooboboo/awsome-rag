#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL向量库多模式检索示例

演示如何使用PostgreSQL向量库进行:
1. 向量检索(vector)
2. 全文检索(text)
3. 混合检索(hybrid)

运行前请确保:
1. PostgreSQL已安装pgvector扩展
2. 配置文件中的PG_CONFIG配置正确
"""

import logging
import random
import sys
from pathlib import Path
from typing import List

from llama_index.core.schema import TextNode, NodeWithScore

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from app.config.config import PG_CONFIG
from app.data_source.vector.factory import VectorStoreFactory
from app.model import get_embedding_model
from app.query_construction.service import QueryService

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

# 测试文档和查询
SAMPLE_TEXTS = [
    "Python是一种高级编程语言，具有简洁、易读的语法特点。它被广泛应用于Web开发、数据分析和人工智能领域。",
    "机器学习是人工智能的一个分支，它使用统计技术使计算机系统能够从数据中学习和改进，而无需显式编程。",
    "自然语言处理(NLP)是计算机科学和人工智能的一个领域，研究如何使计算机理解和生成人类语言。",
    "检索增强生成(RAG)是一种将文档检索与大型语言模型相结合的技术，可以提高生成内容的准确性和可靠性。",
    "向量数据库是一种专门存储和检索向量嵌入的数据库系统，使用向量相似度计算进行搜索，广泛用于AI和搜索引擎领域。",
    "PostgreSQL是一种功能强大的开源关系型数据库系统，支持SQL标准的同时，又提供了许多高级功能，如pgvector扩展实现向量检索。",
    "全文检索是一种搜索技术，它对文档内容进行索引，允许用户快速搜索包含特定单词或短语的文档。",
    "混合检索结合了语义搜索和关键词搜索的优点，可以根据上下文理解和关键词匹配找到最相关的信息。"
]

SAMPLE_QUERIES = [
    # 向量检索更适合的查询
    "编程语言有哪些用途",
    # 全文检索更适合的查询
    "PostgreSQL pgvector",
    # 混合检索适合的查询
    "如何在NLP中使用机器学习技术"
]

def prepare_database():
    """检查并准备数据库，确保pgvector扩展已启用"""
    logger.info("准备数据库环境...")
    
    try:
        import psycopg2
        
        # 连接数据库
        conn = psycopg2.connect(
            host=PG_CONFIG["host"],
            port=PG_CONFIG["port"],
            user=PG_CONFIG["user"],
            password=PG_CONFIG["password"],
            database=PG_CONFIG["database"]
        )
        
        cursor = conn.cursor()
        
        # 检查pgvector扩展是否已安装
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
        if not cursor.fetchone():
            logger.info("创建pgvector扩展...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
        
        logger.info("数据库准备完成")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"数据库准备失败: {str(e)}")
        logger.error("请确保PostgreSQL已安装并正确配置，且pgvector扩展可用")
        return False

def create_sample_nodes() -> List[TextNode]:
    """创建示例文本节点"""
    nodes = []

    # 获取嵌入模型
    embed_model = get_embedding_model()
    logger.info("为测试节点生成嵌入向量...")
    
    for i, text in enumerate(SAMPLE_TEXTS):
        embedding = embed_model.get_text_embedding(text)

        # 创建TextNode
        node = TextNode(
            text=text,
            metadata={
                "source": "sample",
                "doc_id": f"doc_{i}",
                "category": random.choice(["programming", "ai", "database"]),
                "language": "zh",
                "created_at": "2023-09-01"
            },
            embedding=embedding
        )
        nodes.append(node)
    
    return nodes

def add_sample_data_to_vector_store():
    """添加示例数据到向量库"""
    logger.info("创建向量库实例...")
    vector_store = VectorStoreFactory.create(vector_store_type="pg_vector")

    logger.info("创建示例文本节点...")
    nodes = create_sample_nodes()
    
    logger.info(f"向向量库添加{len(nodes)}个文本节点...")
    vector_store.add_data(nodes)
    
    logger.info(f"成功添加节点")
    return vector_store

def run_search_examples():
    """执行各种检索示例"""
    logger.info("创建查询服务...")
    query_service = QueryService()
    
    # 对每个查询，使用不同的检索模式
    for query in SAMPLE_QUERIES:
        logger.info(f"\n{'='*80}\n查询: {query}\n{'='*80}")
        
        # 向量检索
        logger.info("\n1. 向量检索结果:")
        vector_results = query_service.query(
            query_text=query,
            top_k=3,
            params={"mode": "vector"}
        )
        display_results(vector_results)
        
        try:
            # 全文检索
            logger.info("\n2. 全文检索结果:")
            text_results = query_service.query(
                query_text=query,
                top_k=3,
                params={"mode": "text"}
            )
            display_results(text_results)
            
            # 混合检索
            logger.info("\n3. 混合检索结果:")
            hybrid_results = query_service.query(
                query_text=query,
                top_k=3,
                params={"mode": "hybrid", "alpha": 0.5}  # alpha=0.5表示向量和关键词权重相等
            )
            display_results(hybrid_results)
        except Exception as e:
            logger.error(f"执行检索出错：{str(e)}")

def display_results(results: List[NodeWithScore]):
    """显示检索结果"""
    for i, node_with_score in enumerate(results):
        node = node_with_score.node
        score = node_with_score.score
        
        logger.info(f"结果 {i+1} (相似度: {score:.4f}):")
        logger.info(f"ID: {node.node_id}")
        logger.info(f"内容: {node.get_content()}")
        logger.info(f"元数据: {node.metadata}")
        logger.info("-" * 40)

def clear_sample_data(vector_store):
    """清理示例数据"""
    try:
        logger.info("清理示例数据...")
        vector_store.delete_data(filters={"source": "sample"})
        logger.info("示例数据已清理")
    except Exception as e:
        logger.error(f"清理数据失败: {e}")

def main():
    """主函数"""
    logger.info("开始PostgreSQL向量库多模式检索示例")
    
    # 准备数据库
    if not prepare_database():
        logger.error("数据库准备失败，退出...")
        return
    
    # 添加示例数据
    vector_store = add_sample_data_to_vector_store()
    
    try:
        # 执行检索示例
        run_search_examples()
    finally:
        # 完成所有查询后再清理示例数据
        # clear_sample_data(vector_store)
        print()
    
    logger.info("示例完成")

if __name__ == "__main__":
    main() 