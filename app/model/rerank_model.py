from typing import List, Optional

from llama_index.core import Settings
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank

from app.config.config import (
    RERANK_MODEL_TYPE,
    LOCAL_RERANK_MODEL_CONFIG,
    ALIYUN_RERANK_MODEL_CONFIG
)


class BaseRerankModel(BaseNodePostprocessor):
    """
    重排模型基类，继承自llama_index的BaseNodePostprocessor
    """

    def _postprocess_nodes(self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None) -> List[
        NodeWithScore]:
        pass

    def __init__(self, model_name: str):
        """
        初始化重排模型
        
        Args:
            model_name: 模型名称
        """
        super().__init__()
        # 不再设置为实例属性，而是存储为类变量
        self._model_name = model_name
    
    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self._model_name
    
    def rerank(self, nodes: List[NodeWithScore], query_str: str) -> List[NodeWithScore]:
        """
        重排节点的便捷方法
        
        Args:
            nodes: 待重排的节点列表
            query_str: 查询文本
            
        Returns:
            重排后的节点列表
        """
        query_bundle = QueryBundle(query_str=query_str)
        return self.postprocess_nodes(nodes, query_bundle)


class LocalRerankModel(BaseRerankModel):
    """
    本地重排模型封装类，使用BGE重排模型
    """
    
    def __init__(
        self, 
        model_name: Optional[str] = None,
        top_n: Optional[int] = None
    ):
        """
        初始化本地BGE重排模型
        
        Args:
            model_name: 模型名称，默认使用配置文件中指定的模型
            top_n: 返回的节点数量，默认使用配置文件中指定的值
        """
        # 使用配置文件中的默认值
        model_name = model_name or LOCAL_RERANK_MODEL_CONFIG["model_name"]
        top_n = top_n or LOCAL_RERANK_MODEL_CONFIG["top_n"]
        
        # 调用父类初始化
        super().__init__(model_name=model_name)
        
        print(f"初始化本地BGE重排模型，模型: {model_name}, top_n: {top_n}")
        
        # 初始化BGE重排模型
        self._reranker = SentenceTransformerRerank(
            model=model_name,
            top_n=top_n
        )
    
    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None
    ) -> List[NodeWithScore]:
        """
        使用BGE重排模型重排节点
        
        Args:
            nodes: 待重排的节点列表
            query_bundle: 查询包，包含查询文本等信息
            
        Returns:
            重排后的节点列表
        """
        return self._reranker.postprocess_nodes(nodes, query_bundle)
    
    def set_as_default(self) -> 'LocalRerankModel':
        """
        将当前重排模型设置为全局默认模型
        """
        Settings.node_postprocessors = [self]
        return self


class AliyunRerankModel(BaseRerankModel):
    """
    阿里云百炼平台重排模型封装类
    
    注意：阿里云百炼平台目前通过GTE-Rerank模型提供重排功能，这里通过FlagEmbeddingReranker集成
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        top_n: Optional[int] = None,
        api_key: Optional[str] = None
    ):
        """
        初始化阿里云百炼平台重排模型
        
        Args:
            model_name: 模型名称，默认使用配置文件中指定的模型
            top_n: 返回的节点数量，默认使用配置文件中指定的值
            api_key: 阿里云API密钥，默认使用配置文件中指定的值
        """
        # 使用配置文件中的默认值
        model_name = model_name or ALIYUN_RERANK_MODEL_CONFIG["model_name"]
        top_n = top_n or ALIYUN_RERANK_MODEL_CONFIG["top_n"]
        api_key = api_key or ALIYUN_RERANK_MODEL_CONFIG["api_key"]
        
        # 调用父类初始化
        super().__init__(model_name=model_name)
        
        if not api_key:
            raise ValueError("阿里云API密钥未设置，请检查配置")
        
        print(f"初始化阿里云重排模型，模型: {model_name}, API密钥前缀: {api_key[:8]}...")

        # 目前阿里云百炼平台通过DashScopeRerank集成GTE-Rerank模型
        self._reranker = DashScopeRerank(
            model=model_name,
            top_n=top_n,
            api_key=api_key
        )
    
    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None
    ) -> List[NodeWithScore]:
        """
        使用阿里云重排模型重排节点
        
        Args:
            nodes: 待重排的节点列表
            query_bundle: 查询包，包含查询文本等信息
            
        Returns:
            重排后的节点列表
        """
        return self._reranker.postprocess_nodes(nodes, query_bundle)
    
    def set_as_default(self) -> 'AliyunRerankModel':
        """
        将当前重排模型设置为全局默认模型
        """
        Settings.node_postprocessors = [self]
        return self


class RerankModelFactory:
    """
    重排模型工厂类，用于创建不同类型的重排模型
    """
    
    @staticmethod
    def create() -> BaseRerankModel:
        """
        创建重排模型实例
        
        Returns:
            重排模型实例
        """
        model_type = RERANK_MODEL_TYPE
        
        if model_type == "aliyun":
            print("使用阿里云重排模型...")
            return AliyunRerankModel()
        elif model_type == "local":
            print("使用本地重排模型...")
            return LocalRerankModel()
        else:
            raise ValueError(f"不支持的重排模型类型: {model_type}")


def get_rerank_model() -> BaseRerankModel:
    """
    获取重排模型实例
    
    Returns:
        重排模型实例
    """
    return RerankModelFactory.create()


# 使用示例
if __name__ == "__main__":
    from llama_index.core.schema import TextNode, NodeWithScore
    
    # 创建一些测试节点
    test_nodes = [
        NodeWithScore(
            node=TextNode(text="北京是中国的首都，有着悠久的历史文化。"),
            score=0.9
        ),
        NodeWithScore(
            node=TextNode(text="上海是中国的经济中心，是一个国际化大都市。"),
            score=0.8
        ),
        NodeWithScore(
            node=TextNode(text="广州是中国南方的重要城市，拥有独特的粤式文化。"),
            score=0.7
        ),
        NodeWithScore(
            node=TextNode(text="中国有很多著名的城市，如北京、上海、广州等。"),
            score=0.6
        ),
    ]
    
    query = "中国的首都在哪里？"
    
    # 示例：使用配置中指定的重排模型
    print("\n使用配置中指定的重排模型:")
    reranker = get_rerank_model()
    print(f"模型类型: {reranker.__class__.__name__}, 模型名称: {reranker.model_name}")
    
    # 打印重排结果
    try:
        reranked_nodes = reranker.rerank(test_nodes, query)
        for i, node in enumerate(reranked_nodes):
            print(f"排名 {i+1}: 分数={node.score:.4f}, 文本={node.node.get_content()}")
    except Exception as e:
        print(f"重排失败: {e}")