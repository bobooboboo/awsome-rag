#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
不同检索方式的比较示例

此脚本演示并比较三种不同的检索方式:
1. 向量检索 - 基于语义相似度匹配
2. 全文检索 - 基于关键词匹配
3. 混合检索 - 结合向量检索和全文检索的优点

使用方法:
1. 首先应用PGVectorStore补丁: `python patches/fix_pgvector_text_search.py`
2. 运行本脚本: `python examples/search_comparison.py`
"""

import logging
import sys
from pathlib import Path
from time import time

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

# 导入项目组件
from app.config.config import PG_CONFIG
from app.data_source.vector.factory import VectorStoreFactory
from app.query_construction.service import QueryService
from examples.pg_fulltext_setup import create_table_if_not_exists

# 应用补丁以支持全文检索功能
import patches.fix_pgvector_text_search

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

def compare_search_methods():
    """比较不同的搜索方法"""
    logger.info("初始化向量库和查询服务...")
    vector_store = VectorStoreFactory.create(vector_store_type="pg_vector")
    query_service = QueryService()
    
    # 测试查询
    queries = [
        # 1. 向量检索通常更适合的查询
        "人工智能如何应用于医疗行业？",
        # 2. 全文检索可能更适合的关键词查询
        "PostgreSQL pgvector",
        # 3. 混合检索有优势的查询
        "NLP机器学习技术"
    ]
    
    # 运行比较
    for i, query in enumerate(queries):
        logger.info(f"\n{'='*100}")
        logger.info(f"查询 {i+1}: {query}")
        logger.info(f"{'='*100}")
        
        # 1. 向量检索
        logger.info("\n1. 向量检索 (Vector Search)")
        logger.info("-" * 50)
        start_time = time()
        vector_results = query_service.query(
            query_text=query,
            top_k=3,
            params={"mode": "vector"}
        )
        vector_time = time() - start_time
        display_results(vector_results, query_time=vector_time)
        
        # 2. 全文检索
        logger.info("\n2. 全文检索 (Text Search)")
        logger.info("-" * 50)
        try:
            start_time = time()
            text_results = query_service.query(
                query_text=query,
                top_k=3,
                params={"mode": "text"}
            )
            text_time = time() - start_time
            display_results(text_results, query_time=text_time)
        except Exception as e:
            logger.error(f"全文检索失败: {e}")
            logger.error("确保已运行 pg_fulltext_setup.py 创建全文索引")
        
        # 3. 混合检索
        logger.info("\n3. 混合检索 (Hybrid Search)")
        logger.info("-" * 50)
        try:
            start_time = time()
            hybrid_results = query_service.query(
                query_text=query,
                top_k=3,
                params={"mode": "hybrid", "alpha": 0.5}  # alpha=0.5表示向量和关键词权重相等
            )
            hybrid_time = time() - start_time
            display_results(hybrid_results, query_time=hybrid_time)
        except Exception as e:
            logger.error(f"混合检索失败: {e}")

def display_results(results, query_time=None):
    """显示检索结果"""
    if query_time:
        logger.info(f"查询耗时: {query_time:.4f} 秒")
        
    for i, node_with_score in enumerate(results):
        node = node_with_score.node
        score = node_with_score.score
        
        logger.info(f"结果 {i+1} (相似度: {score:.4f}):")
        logger.info(f"ID: {node.node_id}")
        logger.info(f"内容: {node.get_content()}")
        logger.info(f"元数据: {node.metadata}")
        logger.info("-" * 40)

def prepare_database():
    """检查PG数据库是否就绪"""
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
        
        # 检查pgvector扩展
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
        if not cursor.fetchone():
            logger.error("未安装pgvector扩展，请安装后再试")
            return False
        
        # 检查是否有数据
        cursor.execute(f"SELECT COUNT(*) FROM data_{PG_CONFIG['table_name']};")
        count = cursor.fetchone()[0]
        if count == 0:
            logger.warning(f"表 data_{PG_CONFIG['table_name']} 中没有数据，结果可能不准确")
        else:
            logger.info(f"数据库中有 {count} 条记录")
        
        # 检查text_search_tsv列
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = 'data_{PG_CONFIG['table_name']}' AND column_name = 'text_search_tsv';")
        if not cursor.fetchone():
            logger.warning(f"表 data_{PG_CONFIG['table_name']} 中不存在 text_search_tsv 列，全文检索可能无法正常工作")
            logger.warning("请运行 pg_fulltext_setup.py 创建全文索引")
            
            # 尝试创建text_search_tsv列
            logger.info("正在尝试创建text_search_tsv列...")
            return create_table_if_not_exists()
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"数据库检查失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始检索方法比较示例")
    
    # 应用补丁
    patches.fix_pgvector_text_search.apply_patch()
    
    # 确保表结构正确
    logger.info("确保数据库表结构正确...")
    create_table_if_not_exists()
    
    # 检查数据库
    if not prepare_database():
        logger.error("数据库准备失败，退出...")
        return
    
    # 运行比较
    compare_search_methods()
    
    logger.info("\n比较完成，总结:")
    logger.info("1. 向量检索 - 擅长理解语义和相似概念，但可能错过关键词匹配")
    logger.info("2. 全文检索 - 擅长精确的关键词匹配，但理解语义的能力有限")
    logger.info("3. 混合检索 - 结合两者优点，通常能获得更全面的结果")

if __name__ == "__main__":
    main() 