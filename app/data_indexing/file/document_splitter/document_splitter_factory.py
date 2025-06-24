import re
from typing import Optional, List, cast

from llama_index.core.node_parser import NodeParser, SentenceSplitter, TokenTextSplitter, SemanticSplitterNodeParser
from llama_index.core.node_parser.text.semantic_splitter import SentenceSplitterCallable

from app.data_indexing.file.document_splitter.legal_splitter import LegalSplitter
from app.model.embedding_model import get_embedding_model


class DocumentSplitterFactory:
    @staticmethod
    def create(split_strategy: str, chunk_size: Optional[int] = 500,
               chunk_overlap: Optional[int] = 50) -> NodeParser:
        if split_strategy == "sentence":
            return SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, paragraph_separator="\n\n",
                                    secondary_chunking_regex=r'[^,.;。？！；…]+[,.;。？！；…]?|[,.;。？！；…]', separator=' ')
        elif split_strategy == "token":
            return TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        elif split_strategy == "semantic":
            def _chinese_sentence_splitter(text: str) -> List[str]:
                # 根据中文标点进行分句
                text = re.sub(r'([。！？?])([^”’])', r"\1\n\2", text)  # 标点后换行
                text = re.sub(r'(\.{6})([^”’])', r"\1\n\2", text)  # 省略号后换行
                text = re.sub(r'(…{2})([^”’])', r"\1\n\2", text)
                text = re.sub(r'([。！？?][”’])([^，。！？?])', r'\1\n\2', text)
                sentences = text.strip().split('\n')
                return [s.strip() for s in sentences if s.strip()]

            chinese_sentence_splitter_callable: SentenceSplitterCallable = cast(SentenceSplitterCallable,
                                                                                _chinese_sentence_splitter)

            # 要注意超出llm的上下文长度，比如阿里云百炼的text-embedding-v2是2048
            # return SemanticSplitterNodeParser(buffer_size=chunk_overlap, breakpoint_percentile_threshold=95,
            #                                   embed_model=get_embedding_model())
            return SemanticSplitterNodeParser(breakpoint_percentile_threshold=10, buffer_size=3,
                                              sentence_splitter=chinese_sentence_splitter_callable,
                                              embed_model=get_embedding_model())
        elif split_strategy == "legal":
            return LegalSplitter()
        else:
            raise NotImplementedError(f"不支持的文档分割策略{split_strategy}")
