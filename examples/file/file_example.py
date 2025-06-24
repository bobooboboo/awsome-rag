import json

from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SemanticSplitterNodeParser

from app.data_indexing.file.document_loader.local_file import LocalFileLoader
from app.data_indexing.file.document_splitter.document_splitter_factory import DocumentSplitterFactory
from app.model import get_embedding_model




if __name__ == '__main__':
    documents = LocalFileLoader().load_documents(
        "/Users/boboo/test.txt")

    # split_strategy_list = ["sentence",
    #                        "token",
    #                        "semantic",
    #                        "legal"]
    # for split_strategy in split_strategy_list:
    #     splitter = DocumentSplitterFactory.create(split_strategy)
    #     nodes = splitter.get_nodes_from_documents(documents)
    #     print(f"{split_strategy}: {[node.text for node in nodes]}")

    embedding_model = get_embedding_model()


    splitter = DocumentSplitterFactory.create("semantic")

    nodes = splitter.get_nodes_from_documents(documents)
    for node in nodes:
        print(node)




