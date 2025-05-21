from abc import ABC, abstractmethod


class BasePreQueryProcessor(ABC):
    @abstractmethod
    def run(self, query: str) -> str:
        """对查询字符串进行转换"""
        pass