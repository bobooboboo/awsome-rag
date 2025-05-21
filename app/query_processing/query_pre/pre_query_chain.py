from typing import List

from app.query_processing.query_pre.base_processor import BasePreQueryProcessor


class PreQueryProcessorChain:
    def __init__(self, processors: List[BasePreQueryProcessor]):
        self.processors = processors

    def run(self, query: str) -> str:
        for processor in self.processors:
            query = processor.run(query)
        return query
