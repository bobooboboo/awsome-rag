"""
查询构建模块，负责根据配置和用户参数决定使用哪种检索策略
"""

from app.query_construction.service import QueryService
from app.query_construction.routing import QueryRouter

__all__ = ['QueryService', 'QueryRouter'] 