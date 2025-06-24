from typing import Dict, Any, Optional

class QueryRouter:
    """
    查询路由器，根据配置和用户参数确定使用哪种检索模式
    """
    
    def __init__(self, search_mode: str):
        """
        初始化路由器
        
        Args:
            search_mode: 检索方式
        """
        # 从配置中获取默认检索模式，默认为vector
        self.default_mode = search_mode
        
    def determine_mode(self, params: Optional[Dict[str, Any]] = None) -> str:
        """
        确定适合的查询模式
        
        Args:
            params: 用户提供的参数，可能包含所需的检索模式
            
        Returns:
            检索模式：vector, text, hybrid, sparse, semantic_hybrid
        """
        params = params or {}
        
        # 有效的检索模式列表
        valid_modes = ["vector", "text", "hybrid", "sparse", "semantic_hybrid"]
        
        # 优先使用用户指定的模式
        # 查找可能的模式参数名称
        for param_name in ["mode", "search_mode", "query_mode"]:
            if param_name in params:
                user_mode = params[param_name].lower()
                if user_mode in valid_modes:
                    return user_mode
        
        # 如果未找到有效模式，返回默认模式
        return self.default_mode 