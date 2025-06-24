from typing import List, Optional, Any

from llama_index.core import Settings
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from pydantic import Field

from app.config.config import (
    EMBED_MODEL_TYPE,
    LOCAL_EMBED_MODEL_CONFIG,
    ALIYUN_EMBED_MODEL_CONFIG
)


class LocalEmbeddingModel(BaseEmbedding):
    """
    本地嵌入模型封装类，使用HuggingFace模型
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化嵌入模型
        
        Args:
            model_name: 模型名称，默认使用配置文件中指定的模型
        """
        model_name = model_name or LOCAL_EMBED_MODEL_CONFIG["model_name"]
        super().__init__(model_name=model_name)
        self._local_model = OllamaEmbedding(base_url="http://127.0.0.1:11434", model_name=model_name)

    def _get_text_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            文本的向量表示
        """
        return self._local_model.get_text_embedding(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        获取查询文本的向量表示
        
        Args:
            query: 查询文本
            
        Returns:
            查询文本的向量表示
        """
        return self._local_model.get_query_embedding(query)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """
        异步获取查询文本的向量表示
        
        Args:
            query: 查询文本
            
        Returns:
            查询文本的向量表示
        """
        # 默认实现，调用同步方法
        return self._get_query_embedding(query)

    def set_as_default(self) -> 'LocalEmbeddingModel':
        """
        将当前嵌入模型设置为全局默认模型
        """
        Settings.embed_model = self
        return self


class AliyunEmbeddingModel(BaseEmbedding):
    """
    阿里云百炼嵌入模型封装类，使用llama-index提供的集成
    """

    dashscope_model: Any = Field(default=None, exclude=True, description="DashScope嵌入模型实例")

    def __init__(self):
        """
        初始化阿里云嵌入模型
        """
        api_key = ALIYUN_EMBED_MODEL_CONFIG["api_key"]
        model_name = ALIYUN_EMBED_MODEL_CONFIG["model_name"]

        if not api_key:
            raise ValueError("阿里云API密钥未设置，请检查配置")

        print(f"初始化阿里云嵌入模型，模型: {model_name}, API密钥前缀: {api_key[:8]}...")

        # 先调用父类初始化
        super().__init__(model_name=model_name)

        # 初始化llama-index的DashScopeEmbedding
        self._dashscope_model = DashScopeEmbedding(
            model_name=model_name,
            api_key=api_key
        )

    def _get_text_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            文本的向量表示
        """
        return self._dashscope_model.get_text_embedding(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        获取查询文本的向量表示
        
        Args:
            query: 查询文本
            
        Returns:
            查询文本的向量表示
        """
        return self._dashscope_model.get_query_embedding(query)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """
        异步获取查询文本的向量表示
        
        Args:
            query: 查询文本
            
        Returns:
            查询文本的向量表示
        """
        # 默认实现，调用同步方法
        return self._get_query_embedding(query)

    @property
    def model(self):
        return self._dashscope_model

    def set_as_default(self) -> 'AliyunEmbeddingModel':
        """
        将当前嵌入模型设置为全局默认模型
        """
        Settings.embed_model = self
        return self


class EmbeddingModelFactory:
    """
    嵌入模型工厂类，用于创建不同类型的嵌入模型
    """

    @staticmethod
    def create() -> BaseEmbedding:
        """
        创建嵌入模型实例
        
        Returns:
            嵌入模型实例
        """
        model_type = EMBED_MODEL_TYPE

        if model_type == "aliyun":
            print("使用阿里云嵌入模型...")
            return AliyunEmbeddingModel()
        elif model_type == "local":
            print("使用本地嵌入模型...")
            return LocalEmbeddingModel()
        else:
            raise ValueError(f"不支持的嵌入模型类型: {model_type}")


def get_embedding_model() -> BaseEmbedding:
    """
    获取嵌入模型实例
    
    Returns:
        嵌入模型实例
    """
    return EmbeddingModelFactory.create()