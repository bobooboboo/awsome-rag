from app.config.config import VECTOR_STORE_TYPE
from app.data_source.vector.base import BaseVectorStore
from app.data_source.vector.pg_vector import PGVectorStore


class VectorStoreFactory:
    """
    向量数据库工厂类，用于创建不同类型的向量数据库实例
    """

    @staticmethod
    def create(vector_store_type=None, **kwargs) -> BaseVectorStore:
        """
        创建向量数据库实例
        
        Args:
            vector_store_type: 向量数据库类型，默认使用配置文件中的类型
                - pg_vector: PostgreSQL + pgvector
                - milvus: Milvus向量数据库
            **kwargs: 向量数据库初始化参数
            
        Returns:
            向量数据库实例
        """
        # 如果未指定类型，使用配置中的类型
        if vector_store_type is None:
            vector_store_type = VECTOR_STORE_TYPE

        try:
            if vector_store_type == "pg_vector":
                return PGVectorStore(**kwargs)
            elif vector_store_type == "milvus":
                # 按需导入Milvus实现
                from app.data_source.vector.milvus import MilvusVectorStore
                return MilvusVectorStore(**kwargs)
            else:
                raise ValueError(f"不支持的向量数据库类型: {vector_store_type}")
        except Exception as e:
            print(f"初始化向量存储失败: {str(e)}")
            print(f"请确保{vector_store_type}服务已启动并且连接配置正确")
            # 重新抛出异常，以便上层处理
            raise
