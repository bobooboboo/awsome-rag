from pathlib import Path
from typing import List, Optional, Union
from llama_index.readers.file import PyMuPDFReader
from llama_index.core import Document

class LocalFileLoader:
    """
    本地文件加载器，使用PyMuPDF加载本地PDF文件
    """
    
    def __init__(self):
        """初始化本地文件加载器"""
        self.pdf_reader = PyMuPDFReader()
    
    def load_pdf(self, file_path: Union[str, Path]) -> List[Document]:
        """
        加载PDF文件
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            Document对象列表
        """
        return self.pdf_reader.load_data(file_path)
    
    def load_documents(self, file_paths: List[Union[str, Path]]) -> List[Document]:
        """
        加载多个文档文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            Document对象列表
        """
        documents = []
        
        for file_path in file_paths:
            file_path = Path(file_path)
            
            if not file_path.exists():
                print(f"警告: 文件不存在 - {file_path}")
                continue
            
            if file_path.suffix.lower() == '.pdf':
                # 处理PDF文件
                docs = self.load_pdf(file_path)
                documents.extend(docs)
            else:
                # 提示不支持的文件类型
                print(f"警告: 不支持的文件类型 - {file_path}")
        
        return documents 