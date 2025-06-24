#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
向量存储测试的公共模块，包含共用的函数和常量
"""

import logging
import os
import sys
from typing import List, Dict, Any

from dotenv import load_dotenv

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 确保在导入其他模块前先加载环境变量
load_dotenv()

# 强制设置环境变量
os.environ["EMBED_MODEL_TYPE"] = "aliyun"

from llama_index.core.schema import TextNode, NodeWithScore
from app.config.config import MILVUS_CONFIG, PG_CONFIG, VECTOR_STORE_CONFIG
from app.model.embedding_model import get_embedding_model

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_nodes(num_nodes: int = 5) -> List[TextNode]:
    """
    创建测试用的TextNode列表
    
    Args:
        num_nodes: 创建的节点数量
        
    Returns:
        TextNode列表
    """
    # 获取嵌入模型
    embed_model = get_embedding_model()
    logger.info("为测试节点生成嵌入向量...")
    
    nodes = []
    for i in range(num_nodes):
        text = f"这是测试文档 {i}，包含一些示例内容。这个文档用于测试向量存储功能。"
        
        # 生成文本的嵌入向量
        embedding = embed_model.get_text_embedding(text)
        node = TextNode(
            text=text,
            metadata={
                "doc_id": f"doc_{i}",
                "source": "test",
                "category": "example" if i % 2 == 0 else "sample",
                "priority": i
            },
            embedding=embedding  # 设置节点的嵌入向量
        )
        nodes.append(node)
    return nodes


def print_search_results(results: List[NodeWithScore], title: str = "搜索结果"):
    """
    打印搜索结果
    
    Args:
        results: 搜索结果列表
        title: 结果标题
    """
    logger.info(f"{title}数量: {len(results)}")
    for i, result in enumerate(results):
        logger.info(f"结果 {i+1}: ID={result.id_}, 相似度={result.score:.4f}")
        logger.info(f"内容: {result.text[:50]}...")


def get_milvus_config() -> Dict[str, Any]:
    """
    获取Milvus测试配置
    
    Returns:
        Milvus配置字典
    """
    # 从配置中获取Milvus参数
    config = {
        "host": MILVUS_CONFIG["host"],
        "port": MILVUS_CONFIG["port"],
        "collection_name": MILVUS_CONFIG["collection"],
        "dimension": VECTOR_STORE_CONFIG.get("embed_dim", 1536),
        "overwrite": True,  # 测试时总是覆盖现有集合
        "embed_model": get_embedding_model()  # 显式传入嵌入模型
    }
    
    # 如果有用户名和密码，添加到配置中
    if MILVUS_CONFIG["username"] and MILVUS_CONFIG["password"]:
        config["username"] = MILVUS_CONFIG["username"]
        config["password"] = MILVUS_CONFIG["password"]
    
    logger.info(f"使用Milvus配置: host={config['host']}, port={config['port']}, collection={config['collection_name']}")
    return config


def get_pg_vector_config() -> Dict[str, Any]:
    """
    获取PGVector测试配置
    
    Returns:
        PGVector配置字典
    """
    # 从配置中获取PGVector参数
    config = {
        "host": PG_CONFIG["host"],
        "port": PG_CONFIG["port"],
        "database": PG_CONFIG["database"],
        "user": PG_CONFIG["user"],
        "password": PG_CONFIG["password"],
        "table_name": PG_CONFIG["table_name"],
        "embed_dim": VECTOR_STORE_CONFIG.get("embed_dim", 1536),
        "overwrite": True,  # 测试时总是覆盖现有表
        "drop_table": True,  # 测试时总是删除并重建表
        "embed_model": get_embedding_model()  # 显式传入嵌入模型
    }
    
    logger.info(f"使用PGVector配置: host={config['host']}, port={config['port']}, database={config['database']}, table={config['table_name']}")
    return config 