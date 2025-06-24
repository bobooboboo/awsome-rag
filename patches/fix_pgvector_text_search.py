#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复PGVectorStore全文检索功能

问题：LlamaIndex的PGVectorStore在初始化数据库表时未包含text_search_tsv列，
导致在查询时出现 'Datadocument_embeddings' has no attribute 'text_search_tsv' 错误。

此脚本通过Monkey Patching方式，为SQLAlchemy的数据库模型添加text_search_tsv列定义。
在导入向量库类和服务前运行此脚本即可修复问题。
"""

import sys
import logging
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

# 导入配置
from app.config.config import PG_CONFIG

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)


def apply_patch():
    """
    应用Monkey Patch，修改LlamaIndex的PGVectorStore表定义
    """
    logger.info("正在应用PGVectorStore全文检索修复补丁...")
    
    try:
        # 从llama_index导入PGVectorStore和相关类
        from llama_index.vector_stores.postgres.base import PGVectorStore
        from sqlalchemy.ext.declarative import declarative_base

        # 创建基础模型
        BaseModel = declarative_base()
        
        # 保存原始的create_tables_if_not_exists方法
        original_create_tables = PGVectorStore._create_tables_if_not_exists
        
        # 创建一个补丁函数，扩展表定义
        def patched_create_tables_if_not_exists(self):
            """
            扩展表定义，添加text_search_tsv列
            """
            logger.info("拦截并扩展表定义，添加text_search_tsv列...")
            
            table_name = PGVectorStore._get_table_name(self.table_name)
            
            # 定义具有text_search_tsv列的新模型类
            class PatchedTableClass(BaseModel):
                __tablename__ = table_name

                id = Column(Integer, primary_key=True)
                text = Column(String)
                metadata_ = Column(String)
                node_id = Column(String)
                embedding = Column(self.vector_type(self.embed_dim))
                # 添加tsvector列
                text_search_tsv = Column(TSVECTOR)
            
            # 设置表类
            self._table_class = PatchedTableClass
            
            # 调用原始方法
            return original_create_tables(self)
        
        # 应用补丁
        PGVectorStore._create_tables_if_not_exists = patched_create_tables_if_not_exists
        logger.info("PGVectorStore全文检索修复补丁已应用成功")
        
        return True
    except Exception as e:
        logger.error(f"应用补丁失败: {e}")
        return False


def test_patch():
    """
    测试补丁是否有效
    """
    try:
        from llama_index.vector_stores.postgres import PGVectorStore
        from llama_index.core.schema import TextNode
        from app.model import get_embedding_model
        
        # 初始化向量库
        store = PGVectorStore.from_params(
            database=PG_CONFIG["database"],
            host=PG_CONFIG["host"],
            password=PG_CONFIG["password"],
            port=PG_CONFIG["port"],
            user=PG_CONFIG["user"],
            table_name="test_patched",
            embed_dim=1536,
        )
        
        # 添加测试节点
        embed_model = get_embedding_model()
        embedding = embed_model.get_text_embedding("测试文本")
        node = TextNode(
            text="测试文本",
            embedding=embedding,
            metadata={"source": "test_patch"}
        )
        
        try:
            store.add([node])
            logger.info("添加测试节点成功")
            
            # 测试文本搜索
            from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode
            query = VectorStoreQuery(
                query_str="测试",
                mode=VectorStoreQueryMode.TEXT_SEARCH,
                similarity_top_k=1
            )
            result = store.query(query)
            logger.info(f"全文检索测试成功，找到 {len(result.nodes)} 个结果")
            
            # 删除测试节点
            store.delete([node.node_id])
            logger.info("删除测试节点成功")
            
            return True
        except Exception as e:
            logger.error(f"测试失败: {e}")
            return False
            
    except Exception as e:
        logger.error(f"测试初始化失败: {e}")
        return False


if __name__ == "__main__":
    if apply_patch():
        logger.info("PGVectorStore补丁应用成功")
        
        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            if test_patch():
                logger.info("补丁测试通过，全文检索功能正常工作")
            else:
                logger.error("补丁测试失败，全文检索功能可能仍有问题")
    else:
        logger.error("补丁应用失败") 