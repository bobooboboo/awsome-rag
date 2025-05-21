#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试PGVector向量存储的示例代码
"""

import os
import sys

from dotenv import load_dotenv

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 确保在导入其他模块前先加载环境变量
load_dotenv()

from app.data_source.vector.pg_vector import PGVectorStore
from examples.vector_store.common import create_test_nodes, print_search_results, logger, get_pg_vector_config


def test_pg_vector_store():
    """测试PGVector向量存储的基本功能"""
    logger.info("开始测试PGVector向量存储...")

    # 从配置中获取PGVector参数
    pg_config = get_pg_vector_config()

    # 初始化PGVector向量存储
    vector_store = PGVectorStore(**pg_config)

    # 创建测试节点
    test_nodes = create_test_nodes(10)
    logger.info(f"已创建 {len(test_nodes)} 个测试节点")

    # 添加数据
    node_ids = vector_store.add_data(test_nodes)
    logger.info(f"成功添加数据，节点ID: {node_ids}")

    # 通过ID获取数据
    retrieved_nodes = vector_store.get_data(node_ids=node_ids)
    logger.info(f"通过ID检索到 {len(retrieved_nodes)} 个节点")
    for node in retrieved_nodes:
        logger.info(f"节点ID: {node.node_id}, 内容: {node.get_content()}...")

    # 通过过滤条件获取数据
    filter_nodes = vector_store.get_data(filters={"category": "example"})
    logger.info(f"通过过滤条件检索到 {len(filter_nodes)} 个节点")

    # 测试文本搜索
    search_results = vector_store.search_by_text(
        text="测试文档",
        top_k=3,
        filters={"source": "test"}
    )
    print_search_results(search_results, "文本搜索结果")

    # 测试删除数据
    vector_store.delete_data(node_ids=node_ids[5:7])
    logger.info("已删除部分节点")

    # 验证删除结果
    remaining = vector_store.get_data(filters={"source": "test"})
    logger.info(f"删除后剩余节点数量: {len(remaining)}")

    # 通过过滤条件删除数据
    vector_store.delete_data(filters={"category": "sample"})
    logger.info("已通过过滤条件删除节点")

    # 验证删除结果
    final_nodes = vector_store.get_data(filters={"source": "test"})
    logger.info(f"最终节点数量: {len(final_nodes)}")

    logger.info("PGVector向量存储测试完成")


if __name__ == "__main__":
    test_pg_vector_store()
