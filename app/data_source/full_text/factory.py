from app.data_source.full_text.es import ESFullTextStore
from app.config.config import FULLTEXT_STORE_TYPE

class FullTextStoreFactory:
    """
    全文搜索工厂类，用于创建不同类型的全文搜索实例
    """
    
    @staticmethod
    def create(fulltext_store_type=None, **kwargs):
        """
        创建全文搜索实例
        
        Args:
            fulltext_store_type: 全文搜索类型，默认使用配置文件中的类型
                - es: Elasticsearch
                - milvus: Milvus向量数据库
                - pg_vector: PostgreSQL + pgvector
            **kwargs: 全文搜索初始化参数
            
        Returns:
            全文搜索实例
        """
        # 如果未指定类型，使用配置中的类型
        if fulltext_store_type is None:
            fulltext_store_type = FULLTEXT_STORE_TYPE
            
        try:
            if fulltext_store_type == "es":
                return ESFullTextStore(**kwargs)
            elif fulltext_store_type == "pg_vector":
                # 按需导入PG实现
                from app.data_source.full_text.pg_vector import PGFullTextStore
                return PGFullTextStore(**kwargs)
            else:
                raise ValueError(f"不支持的全文搜索类型: {fulltext_store_type}")
        except Exception as e:
            print(f"初始化全文搜索存储失败: {str(e)}")
            print(f"请确保{fulltext_store_type}服务已启动并且连接配置正确")
            # 重新抛出异常，以便上层处理
            raise 