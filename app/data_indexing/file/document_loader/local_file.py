from pathlib import Path
from typing import List

from llama_index.core import Document
from llama_index.readers.file import DocxReader, PDFReader, HTMLTagReader, MarkdownReader, UnstructuredReader, \
    PandasExcelReader, CSVReader


class LocalFileLoader:
    """
    本地文件加载器，使用PyMuPDF加载本地PDF文件
    """

    def __init__(self):
        """初始化本地文件加载器"""
        self.doc_reader = DocxReader()
        self.pdf_reader = PDFReader(return_full_document=True)
        self.html_reader = HTMLTagReader()
        self.markdown_reader = MarkdownReader()
        self.default_reader = UnstructuredReader()
        self.excel_reader = PandasExcelReader()
        self.csv_reader = CSVReader()

    def load_documents(self, file_path: str) -> List[Document]:
        """
        加载多个文档文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Document对象列表
        """
        file_type = file_path.split('.')[-1]
        if file_type in ['docx', 'doc']:
            return self.doc_reader.load_data(file=Path(file_path))
        elif file_type == 'pdf':
            return self.pdf_reader.load_data(file=Path(file_path))
        elif file_type in ['html', 'htm']:
            return self.html_reader.load_data(file=Path(file_path))
        elif file_type in ['markdown', 'md']:
            return self.markdown_reader.load_data(file=file_path)
        elif file_type in ["txt", "text"]:
            with open(file_path, 'r', encoding="utf-8") as f:
                return [Document(text=f.read())]
        elif file_type in ['csv']:
            return self.csv_reader.load_data(file=Path(file_path))
        elif file_type in ['xls', 'xlsx']:
            return self.excel_reader.load_data(file=Path(file_path))
        else:
            return self.default_reader.load_data(file=Path(file_path))

# if __name__ == '__main__':
#     filenames = os.listdir("/Users/boboo/Documents/法规文件")
#     loader = LocalFileLoader()
#     for filename in filenames:
#         if filename.endswith("DS_Store"):
#             continue
#         documents = loader.load_documents(f"/Users/boboo/Documents/法规文件/{filename}")
#         print(documents)
