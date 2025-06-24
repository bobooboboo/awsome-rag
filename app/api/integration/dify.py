#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 外部知识库集成API
实现与Dify平台的外部知识库接口集成

直接复用 app.api.query 中的查询逻辑，确保查询行为一致性。
包含查询前处理（敏感词过滤、问题优化）和查询后处理（重排序）。

API文档: https://docs.dify.ai/zh-hans/guides/knowledge-base/api-documentation/external-knowledge-api-documentation
版本: v1.2.0
"""

import logging
import os
from datetime import datetime
from functools import wraps
from typing import Dict, Any, List, Tuple

from flask import Flask, request, jsonify, Response

from app.api.query import QueryAPI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DifyIntegrationAPI:
    """
    Dify外部知识库集成API类
    
    提供符合Dify外部知识库API规范的接口，
    将Dify的查询请求转换为内部查询服务调用，
    并将结果转换为Dify期望的格式。
    """
    
    def __init__(self, app: Flask = None, api_key: str = None, query_api: QueryAPI = None):
        """
        初始化Dify集成API
        
        Args:
            app: Flask应用实例
            api_key: API密钥，用于验证请求
            query_api: 已初始化的QueryAPI实例，必须提供
        """
        self.app = app
        self.api_key = api_key or os.getenv('DIFY_API_KEY')
        self.query_api = query_api
        
        if not self.query_api:
            raise ValueError("query_api参数是必需的，请传入已初始化的QueryAPI实例")
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        初始化Flask应用
        
        Args:
            app: Flask应用实例
        """
        self.app = app
        
        # 注册Dify路由
        self._register_routes()
        
        logger.info("Dify集成API初始化完成")
    
    def _verify_auth(self, f):
        """
        API密钥验证装饰器
        
        Args:
            f: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取Authorization头
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify(self._error_response(1001, "缺少Authorization请求头")), 401
            
            # 验证格式：Bearer <api-key>
            try:
                scheme, token = auth_header.split(' ', 1)
                if scheme.lower() != 'bearer':
                    return jsonify(self._error_response(1001, "无效的Authorization头格式。预期格式为 Bearer <api-key>")), 400
                
                # 验证API密钥
                if self.api_key and token != self.api_key:
                    return jsonify(self._error_response(1002, "授权失败")), 403
                    
            except ValueError:
                return jsonify(self._error_response(1001, "无效的Authorization头格式。预期格式为 Bearer <api-key>")), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def _register_routes(self):
        """注册Dify集成路由"""
        
        @self.app.route('/retrieval', methods=['POST'])
        @self._verify_auth
        def dify_retrieval():
            """
            Dify外部知识库检索接口
            
            按照Dify API规范实现的检索端点：
            https://docs.dify.ai/zh-hans/guides/knowledge-base/api-documentation/external-knowledge-api-documentation
            
            请求格式:
            {
                "knowledge_id": "AAA-BBB-CCC",
                "query": "用户查询",
                "retrieval_setting": {
                    "top_k": 5,
                    "score_threshold": 0.5
                },
                "metadata_condition": {
                    "logical_operator": "and",
                    "conditions": [...]
                }
            }
            
            响应格式:
            {
                "records": [
                    {
                        "content": "文档内容",
                        "score": 0.95,
                        "title": "文档标题",
                        "metadata": {...}
                    }
                ]
            }
            """
            return self._handle_dify_retrieval()
        
        @self.app.route('/dify/health', methods=['GET'])
        def dify_health():
            """Dify集成健康检查"""
            return jsonify({
                "status": "healthy",
                "service": "Dify外部知识库集成",
                "timestamp": datetime.now().isoformat(),
                "version": "1.2.0",
                "features": [
                    "查询前处理（敏感词过滤、问题优化）",
                    "查询后处理（结果重排序）", 
                    "元数据条件过滤",
                    "多种查询模式支持"
                ]
            })
    
    def _handle_dify_retrieval(self) -> Tuple[Response, int]:
        """
        处理Dify检索请求
        
        Returns:
            Flask响应对象
        """
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return jsonify(self._error_response(1001, "请求体不能为空")), 400
            
            # 验证必需参数
            knowledge_id = data.get('knowledge_id')
            if not knowledge_id:
                return jsonify(self._error_response(1001, "缺少必需参数: knowledge_id")), 400
            
            query = data.get('query')
            if not query or not query.strip():
                return jsonify(self._error_response(1001, "缺少必需参数: query")), 400
            
            retrieval_setting = data.get('retrieval_setting', {})
            if not isinstance(retrieval_setting, dict):
                return jsonify(self._error_response(1001, "retrieval_setting必须是对象")), 400
            
            # 解析检索设置
            top_k = retrieval_setting.get('top_k', 5)
            score_threshold = retrieval_setting.get('score_threshold', 0.0)
            
            # 验证参数范围
            if not isinstance(top_k, int) or top_k <= 0 or top_k > 100:
                return jsonify(self._error_response(1001, "top_k必须是1-100之间的整数")), 400
            
            if not isinstance(score_threshold, (int, float)) or score_threshold < 0 or score_threshold > 1:
                return jsonify(self._error_response(1001, "score_threshold必须是0-1之间的数值")), 400
            
            # 解析元数据条件
            metadata_condition = data.get('metadata_condition')
            filters = self._parse_metadata_condition(metadata_condition) if metadata_condition else {}
            
            logger.info(f"Dify检索请求: knowledge_id={knowledge_id}, query={query[:50]}...")
            
            # 直接调用QueryAPI的核心查询逻辑
            results = self.query_api.execute_query(
                query_text=query,
                top_k=top_k,
                filters=filters,
                enable_pre_processing=True,
                enable_post_processing=True,
                params={"mode": "vector"}  # 默认使用向量检索
            )
            
            # 转换为Dify格式并过滤低分结果
            dify_records = self._convert_to_dify_format(results, score_threshold)
            
            logger.info(f"Dify检索完成，返回{len(dify_records)}个结果")
            
            return jsonify({
                "records": dify_records
            }), 200
            
        except Exception as e:
            logger.error(f"Dify检索请求处理失败: {str(e)}", exc_info=True)
            return jsonify(self._error_response(500, f"内部服务器错误: {str(e)}")), 500
    
    @staticmethod
    def _parse_metadata_condition(metadata_condition: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析Dify元数据筛选条件为内部过滤格式
        
        Args:
            metadata_condition: Dify元数据条件
            
        Returns:
            QueryAPI兼容的过滤器格式
        """
        if not metadata_condition or not isinstance(metadata_condition, dict):
            return {}
        
        logical_operator = metadata_condition.get('logical_operator', 'and')
        conditions = metadata_condition.get('conditions', [])
        
        if not conditions:
            return {}
        
        # 简化处理：只支持基础的过滤条件
        filters = {}
        
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
                
            names = condition.get('name', [])
            comparison_operator = condition.get('comparison_operator')
            value = condition.get('value')
            
            if not names or not comparison_operator:
                continue
            
            # 处理每个字段名，只支持基础操作
            for name in names:
                if not isinstance(name, str):
                    continue
                
                # 只支持基础的相等和包含操作
                if comparison_operator in ['is', '='] and value is not None:
                    filters[name] = value
                elif comparison_operator == 'contains' and value:
                    # 对于包含操作，可以使用通配符格式（如果QueryService支持）
                    filters[name] = f"*{value}*"
                elif comparison_operator == 'start with' and value:
                    filters[name] = f"{value}*"
                elif comparison_operator == 'end with' and value:
                    filters[name] = f"*{value}"
                else:
                    # 对于不支持的操作符，记录警告但不影响其他条件
                    logger.warning(f"Dify条件转换: 不支持的操作符 '{comparison_operator}'，已跳过")
        
        # 对于OR逻辑，由于QueryAPI可能不支持，记录警告并使用第一个条件
        if logical_operator.lower() == 'or' and len(conditions) > 1:
            logger.warning("检测到OR逻辑条件，当前实现将使用AND逻辑处理所有条件")
        
        return filters
    
    def _convert_to_dify_format(self, results: List, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        将内部查询结果转换为Dify API格式
        
        Args:
            results: 内部查询结果（NodeWithScore列表）
            score_threshold: 分数阈值，低于此分数的结果将被过滤
            
        Returns:
            Dify格式的记录列表
        """
        dify_records = []
        
        for result in results:
            # 获取分数并应用阈值过滤
            score = float(result.score) if hasattr(result, 'score') else 0.0
            if score < score_threshold:
                continue
            
            # 获取节点信息
            node = result.node
            content = getattr(node, 'text', str(node))
            node_id = getattr(node, 'id_', '')
            
            # 构建标题
            title = self._extract_title(node, content)
            
            # 构建元数据
            metadata = {}
            if hasattr(node, 'metadata') and node.metadata:
                metadata = dict(node.metadata)
            
            # 添加额外的元数据信息
            metadata.update({
                'node_id': node_id,
                'source': 'external_knowledge_base',
                'retrieved_at': datetime.now().isoformat()
            })
            
            # 构建Dify记录
            dify_record = {
                'content': content,
                'score': round(score, 4),  # 保留4位小数
                'title': title,
                'metadata': metadata
            }
            
            dify_records.append(dify_record)
        
        return dify_records
    
    @staticmethod
    def _extract_title(node: Any, content: str) -> str:
        """
        从节点或内容中提取标题
        
        Args:
            node: 节点对象
            content: 内容文本
            
        Returns:
            提取的标题
        """
        # 首先尝试从元数据中获取标题
        if hasattr(node, 'metadata') and node.metadata:
            title = node.metadata.get('title') or node.metadata.get('name') or node.metadata.get('filename')
            if title:
                return str(title)
        
        # 如果没有元数据标题，从内容中提取前50个字符作为标题
        if content:
            title = content.strip()[:50]
            if len(content) > 50:
                title += "..."
            return title
        
        # 最后使用节点ID作为标题
        node_id = getattr(node, 'id_', '')
        return f"文档 {node_id}" if node_id else "未知文档"

    @staticmethod
    def _error_response(error_code: int, error_msg: str) -> Dict[str, Any]:
        """
        生成Dify格式的错误响应

        Args:
            error_code: 错误代码
            error_msg: 错误消息

        Returns:
            错误响应字典
        """
        return {
            "error_code": error_code,
            "error_msg": error_msg
        }


def create_dify_integration_api(app: Flask = None, api_key: str = None, query_api: QueryAPI = None) -> DifyIntegrationAPI:
    """
    创建Dify集成API实例
    
    Args:
        app: Flask应用实例
        api_key: API密钥
        query_api: 已初始化的QueryAPI实例
        
    Returns:
        DifyIntegrationAPI实例
    """
    return DifyIntegrationAPI(app, api_key, query_api)


def init_dify_integration(app: Flask, api_key: str = None, query_api: QueryAPI = None) -> DifyIntegrationAPI:
    """
    初始化Dify集成（函数式接口）
    
    Args:
        app: Flask应用实例
        api_key: API密钥
        query_api: 已初始化的QueryAPI实例，必须提供
        
    Returns:
        DifyIntegrationAPI实例
    """
    if not query_api:
        raise ValueError("query_api参数是必需的，请传入已初始化的QueryAPI实例")
        
    dify_api = DifyIntegrationAPI(app=app, api_key=api_key, query_api=query_api)
    logger.info("Dify外部知识库集成已初始化")
    return dify_api 