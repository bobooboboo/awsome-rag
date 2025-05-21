from typing import List, Optional
from llama_index.core.node_parser import SentenceSplitter, NodeParser
from llama_index.core import Document
from llama_index.core.schema import TextNode

from app.config.config import DOC_PROCESSING_CONFIG

class ChunkSplitter:
    """
    固定大小的文档分块器，将文档拆分为固定大小的块
    """
    
    def __init__(
        self, 
        chunk_size: Optional[int] = None, 
        chunk_overlap: Optional[int] = None,
        parser_cls=SentenceSplitter
    ):
        """
        初始化分块器
        
        Args:
            chunk_size: 块大小（单位：字符）
            chunk_overlap: 块之间的重叠大小（单位：字符）
            parser_cls: 使用的解析器类，默认为SentenceSplitter
        """
        self.chunk_size = chunk_size or DOC_PROCESSING_CONFIG["chunk_size"]
        self.chunk_overlap = chunk_overlap or DOC_PROCESSING_CONFIG["chunk_overlap"]
        
        # 使用llama_index的SentenceSplitter作为实际的分块器
        self.parser = parser_cls(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
    
    def split_documents(self, documents: List[Document]) -> List[TextNode]:
        """
        将文档列表拆分为节点
        
        Args:
            documents: 文档列表
            
        Returns:
            节点列表
        """
        return self.parser.get_nodes_from_documents(documents)
    
    def split_text(self, text: str, metadata: Optional[dict] = None) -> List[TextNode]:
        """
        将文本拆分为节点
        
        Args:
            text: 要拆分的文本
            metadata: 节点元数据
            
        Returns:
            节点列表
        """
        doc = Document(text=text, metadata=metadata or {})
        return self.parser.get_nodes_from_documents([doc]) 