#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify集成API测试脚本
用于验证与Dify平台的外部知识库集成功能
"""

import requests
import json
import time
from typing import Dict, Any


class DifyIntegrationTester:
    """Dify集成API测试类"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5001", api_key: str = "your-dify-api-key"):
        """
        初始化测试器
        
        Args:
            base_url: API服务的基础URL
            api_key: Dify API密钥
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def test_dify_health(self) -> bool:
        """测试Dify集成健康检查"""
        try:
            print("🔍 测试Dify集成健康检查...")
            response = requests.get(f"{self.base_url}/dify/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Dify集成健康检查成功: {data.get('service')}")
                print(f"   版本: {data.get('version')}")
                print(f"   时间戳: {data.get('timestamp')}")
                return True
            else:
                print(f"❌ Dify集成健康检查失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Dify集成健康检查异常: {str(e)}")
            return False
    
    def test_dify_retrieval_basic(self) -> bool:
        """测试基础Dify检索功能"""
        try:
            print("\n🔍 测试基础Dify检索功能...")
            
            # 构建Dify格式的请求
            request_data = {
                "knowledge_id": "test-knowledge-001",
                "query": "什么是人工智能？",
                "retrieval_setting": {
                    "top_k": 5,
                    "score_threshold": 0.3
                }
            }
            
            response = requests.post(
                f"{self.base_url}/retrieval",
                json=request_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                print(f"✅ Dify检索成功:")
                print(f"   返回记录数: {len(records)}")
                
                # 显示前几条记录的详细信息
                for i, record in enumerate(records[:2]):
                    print(f"   记录{i+1}:")
                    print(f"     标题: {record.get('title', '无标题')}")
                    print(f"     分数: {record.get('score', 0):.4f}")
                    content = record.get('content', '')
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    print(f"     内容: {content_preview}")
                    if record.get('metadata'):
                        print(f"     元数据: {record['metadata']}")
                    print()
                
                return True
            else:
                print(f"❌ Dify检索失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   错误代码: {error_data.get('error_code')}")
                    print(f"   错误信息: {error_data.get('error_msg')}")
                except:
                    print(f"   错误响应: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Dify检索请求异常: {str(e)}")
            return False
    
    def test_dify_retrieval_with_metadata(self) -> bool:
        """测试带元数据筛选的Dify检索"""
        try:
            print("\n🔍 测试带元数据筛选的Dify检索...")
            
            request_data = {
                "knowledge_id": "test-knowledge-002",
                "query": "深度学习算法",
                "retrieval_setting": {
                    "top_k": 3,
                    "score_threshold": 0.5
                },
                "metadata_condition": {
                    "logical_operator": "and",
                    "conditions": [
                        {
                            "name": ["category"],
                            "comparison_operator": "is",
                            "value": "AI技术"
                        },
                        {
                            "name": ["language"],
                            "comparison_operator": "contains",
                            "value": "zh"
                        }
                    ]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/retrieval",
                json=request_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                print(f"✅ 带元数据筛选的Dify检索成功:")
                print(f"   返回记录数: {len(records)}")
                
                for i, record in enumerate(records):
                    print(f"   记录{i+1}: score={record.get('score', 0):.4f}")
                
                return True
            else:
                print(f"❌ 带元数据筛选的Dify检索失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 带元数据筛选的Dify检索异常: {str(e)}")
            return False
    
    def test_dify_logical_operator_and(self) -> bool:
        """测试AND逻辑操作符"""
        try:
            print("\n🔍 测试AND逻辑操作符...")
            
            request_data = {
                "knowledge_id": "test-logical-and",
                "query": "机器学习",
                "retrieval_setting": {
                    "top_k": 3,
                    "score_threshold": 0.3
                },
                "metadata_condition": {
                    "logical_operator": "and",
                    "conditions": [
                        {
                            "name": ["type"],
                            "comparison_operator": "is",
                            "value": "tutorial"
                        },
                        {
                            "name": ["level"],
                            "comparison_operator": "is",
                            "value": "beginner"
                        }
                    ]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/retrieval",
                json=request_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                print(f"✅ AND逻辑操作符测试成功:")
                print(f"   返回记录数: {len(records)}")
                print(f"   逻辑: type='tutorial' AND level='beginner'")
                
                return True
            else:
                print(f"❌ AND逻辑操作符测试失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ AND逻辑操作符测试异常: {str(e)}")
            return False
    
    def test_dify_logical_operator_or(self) -> bool:
        """测试OR逻辑操作符"""
        try:
            print("\n🔍 测试OR逻辑操作符...")
            
            request_data = {
                "knowledge_id": "test-logical-or",
                "query": "人工智能",
                "retrieval_setting": {
                    "top_k": 5,
                    "score_threshold": 0.2
                },
                "metadata_condition": {
                    "logical_operator": "or",
                    "conditions": [
                        {
                            "name": ["category"],
                            "comparison_operator": "is",
                            "value": "机器学习"
                        },
                        {
                            "name": ["category"],
                            "comparison_operator": "is",
                            "value": "深度学习"
                        },
                        {
                            "name": ["tag"],
                            "comparison_operator": "contains",
                            "value": "neural"
                        }
                    ]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/retrieval",
                json=request_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                print(f"✅ OR逻辑操作符测试成功:")
                print(f"   返回记录数: {len(records)}")
                print(f"   逻辑: category='机器学习' OR category='深度学习' OR tag contains 'neural'")
                
                return True
            else:
                print(f"❌ OR逻辑操作符测试失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ OR逻辑操作符测试异常: {str(e)}")
            return False
    
    def test_dify_comparison_operators(self) -> bool:
        """测试各种比较操作符"""
        try:
            print("\n🔍 测试各种比较操作符...")
            
            # 测试多种比较操作符
            test_cases = [
                ("contains", "包含测试"),
                ("start with", "开头测试"),
                ("end with", "结尾测试"),
                ("is not", "不等于测试"),
                ("not contains", "不包含测试")
            ]
            
            success_count = 0
            for operator, description in test_cases:
                request_data = {
                    "knowledge_id": f"test-{operator.replace(' ', '-')}",
                    "query": "测试查询",
                    "retrieval_setting": {
                        "top_k": 2,
                        "score_threshold": 0.1
                    },
                    "metadata_condition": {
                        "logical_operator": "and",
                        "conditions": [
                            {
                                "name": ["description"],
                                "comparison_operator": operator,
                                "value": "test" if operator != "empty" else None
                            }
                        ]
                    }
                }
                
                response = requests.post(
                    f"{self.base_url}/retrieval",
                    json=request_data,
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    print(f"   ✅ {description} ({operator}): 成功")
                    success_count += 1
                else:
                    print(f"   ❌ {description} ({operator}): 失败 ({response.status_code})")
            
            print(f"✅ 比较操作符测试完成: {success_count}/{len(test_cases)} 成功")
            return success_count == len(test_cases)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 比较操作符测试异常: {str(e)}")
            return False
    
    def test_dify_auth_validation(self) -> bool:
        """测试Dify API认证验证"""
        print("\n🔍 测试Dify API认证验证...")
        
        # 测试无Authorization头
        try:
            response = requests.post(
                f"{self.base_url}/retrieval",
                json={"knowledge_id": "test", "query": "test"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 403 or response.status_code == 401:
                print("✅ 无Authorization头正确返回认证错误")
            else:
                print(f"❌ 无Authorization头应返回认证错误，实际返回{response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 无Authorization头测试异常: {str(e)}")
            return False
        
        # 测试错误的API Key
        try:
            wrong_headers = {
                "Authorization": "Bearer wrong-api-key",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/retrieval",
                json={"knowledge_id": "test", "query": "test"},
                headers=wrong_headers,
                timeout=10
            )
            
            if response.status_code == 403 or response.status_code == 401:
                print("✅ 错误API Key正确返回认证错误")
            else:
                print(f"❌ 错误API Key应返回认证错误，实际返回{response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 错误API Key测试异常: {str(e)}")
            return False
        
        return True
    
    def test_dify_parameter_validation(self) -> bool:
        """测试Dify API参数验证"""
        print("\n🔍 测试Dify API参数验证...")
        
        # 测试缺少必需参数
        test_cases = [
            ({"query": "test"}, "缺少knowledge_id"),
            ({"knowledge_id": "test"}, "缺少query"),
            ({"knowledge_id": "test", "query": ""}, "空query"),
            ({"knowledge_id": "test", "query": "test", "retrieval_setting": {"top_k": 0}}, "无效top_k"),
            ({"knowledge_id": "test", "query": "test", "retrieval_setting": {"score_threshold": 1.5}}, "无效score_threshold"),
        ]
        
        for request_data, description in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/retrieval",
                    json=request_data,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 400:
                    print(f"✅ {description}正确返回400错误")
                else:
                    print(f"❌ {description}应返回400，实际返回{response.status_code}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ {description}测试异常: {str(e)}")
                return False
        
        return True
    
    def test_dify_response_format(self) -> bool:
        """测试Dify响应格式的正确性"""
        try:
            print("\n🔍 测试Dify响应格式...")
            
            request_data = {
                "knowledge_id": "format-test",
                "query": "测试响应格式",
                "retrieval_setting": {
                    "top_k": 2,
                    "score_threshold": 0.0
                }
            }
            
            response = requests.post(
                f"{self.base_url}/retrieval",
                json=request_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 验证响应格式
                if 'records' not in data:
                    print("❌ 响应缺少records字段")
                    return False
                
                records = data['records']
                if not isinstance(records, list):
                    print("❌ records字段不是列表")
                    return False
                
                # 验证记录格式
                for i, record in enumerate(records):
                    required_fields = ['content', 'score', 'title']
                    for field in required_fields:
                        if field not in record:
                            print(f"❌ 记录{i+1}缺少{field}字段")
                            return False
                    
                    # 验证字段类型
                    if not isinstance(record['score'], (int, float)):
                        print(f"❌ 记录{i+1}的score字段不是数值类型")
                        return False
                    
                    if not isinstance(record['content'], str):
                        print(f"❌ 记录{i+1}的content字段不是字符串类型")
                        return False
                    
                    if not isinstance(record['title'], str):
                        print(f"❌ 记录{i+1}的title字段不是字符串类型")
                        return False
                
                print("✅ Dify响应格式验证通过")
                return True
            else:
                print(f"❌ 响应格式测试失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 响应格式测试异常: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ 响应格式验证异常: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有Dify集成测试"""
        print("🚀 开始运行Dify集成测试套件...")
        print("=" * 70)
        
        start_time = time.time()
        test_results = []
        
        # 健康检查测试
        test_results.append(self.test_dify_health())
        
        # 基础功能测试
        test_results.append(self.test_dify_retrieval_basic())
        test_results.append(self.test_dify_retrieval_with_metadata())
        
        # 安全性测试
        test_results.append(self.test_dify_auth_validation())
        test_results.append(self.test_dify_parameter_validation())
        
        # 格式验证测试
        test_results.append(self.test_dify_response_format())
        
        # 逻辑操作符测试
        test_results.append(self.test_dify_logical_operator_and())
        test_results.append(self.test_dify_logical_operator_or())
        test_results.append(self.test_dify_comparison_operators())
        
        # 统计结果
        total_time = time.time() - start_time
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print("\n" + "=" * 70)
        print(f"📊 Dify集成测试结果总结:")
        print(f"   - 总测试数: {total_tests}")
        print(f"   - 通过测试: {passed_tests}")
        print(f"   - 失败测试: {total_tests - passed_tests}")
        print(f"   - 总耗时: {total_time:.2f}s")
        print(f"   - 成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 所有Dify集成测试通过！集成工作正常。")
            return True
        else:
            print("⚠️  部分Dify集成测试失败，请检查集成配置。")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dify集成API测试工具")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:5001",
        help="API服务地址 (默认: http://127.0.0.1:5001)"
    )
    parser.add_argument(
        "--api-key",
        default="your-dify-api-key",
        help="Dify API密钥 (默认: your-dify-api-key)"
    )
    parser.add_argument(
        "--query",
        help="单独测试指定查询文本"
    )
    
    args = parser.parse_args()
    
    tester = DifyIntegrationTester(args.url, args.api_key)
    
    if args.query:
        # 单独测试指定查询
        print(f"🎯 测试Dify单个查询: '{args.query}'")
        
        request_data = {
            "knowledge_id": "single-test",
            "query": args.query,
            "retrieval_setting": {
                "top_k": 5,
                "score_threshold": 0.3
            }
        }
        
        try:
            response = requests.post(
                f"{args.url}/retrieval",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {args.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 查询成功，返回{len(data.get('records', []))}个结果")
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(f"❌ 查询失败: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ 查询异常: {str(e)}")
    else:
        # 运行完整测试套件
        success = tester.run_all_tests()
        exit(0 if success else 1)


if __name__ == "__main__":
    main() 