#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询API测试脚本
用于验证Flask查询API的基本功能
"""

import time

import requests


class QueryAPITester:
    """查询API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        初始化测试器
        
        Args:
            base_url: API服务的基础URL
        """
        self.base_url = base_url
        
    def test_health_check(self) -> bool:
        """测试健康检查接口"""
        try:
            print("🔍 测试健康检查接口...")
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查成功: {data.get('message')}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 健康检查异常: {str(e)}")
            return False
    
    def test_query_modes(self) -> bool:
        """测试查询模式接口"""
        try:
            print("\n🔍 测试查询模式接口...")
            response = requests.get(f"{self.base_url}/api/query/modes", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    modes = data.get('data', {}).get('modes', [])
                    print(f"✅ 获取到 {len(modes)} 种查询模式:")
                    for mode in modes:
                        print(f"   - {mode['name']}: {mode['description']}")
                    return True
                else:
                    print(f"❌ 查询模式请求失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ 查询模式请求失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 查询模式请求异常: {str(e)}")
            return False
    
    def test_post_query(self, query_text: str = "测试查询", **kwargs) -> bool:
        """
        测试POST查询接口
        
        Args:
            query_text: 查询文本
            **kwargs: 其他查询参数
        """
        try:
            print(f"\n🔍 测试POST查询接口: '{query_text}'...")
            
            # 构建请求数据
            data = {
                "query": query_text,
                "top_k": kwargs.get('top_k', 3),
                "mode": kwargs.get('mode', 'vector'),
                "enable_pre_processing": kwargs.get('enable_pre_processing', True),
                "enable_post_processing": kwargs.get('enable_post_processing', True),
                "include_metadata": kwargs.get('include_metadata', True)
            }
            
            # 添加可选参数
            if 'filters' in kwargs:
                data['filters'] = kwargs['filters']
            if 'alpha' in kwargs:
                data['alpha'] = kwargs['alpha']
            
            response = requests.post(
                f"{self.base_url}/api/query",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    query_data = result.get('data', {})
                    results = query_data.get('results', [])
                    execution_time = query_data.get('execution_time', 0)
                    search_mode = query_data.get('search_mode', 'unknown')
                    
                    print(f"✅ POST查询成功:")
                    print(f"   - 搜索模式: {search_mode}")
                    print(f"   - 结果数量: {len(results)}")
                    print(f"   - 执行时间: {execution_time}s")
                    print(f"   - 处理后查询: {query_data.get('processed_query', '无')}")
                    
                    # 显示前几个结果的简要信息
                    for i, result_item in enumerate(results[:2]):
                        text_preview = result_item.get('text', '')[:100] + "..." if len(result_item.get('text', '')) > 100 else result_item.get('text', '')
                        print(f"   - 结果{i+1}: score={result_item.get('score', 0):.4f}, text='{text_preview}'")
                    
                    return True
                else:
                    print(f"❌ POST查询失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ POST查询请求失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   错误信息: {error_data.get('message', '未知错误')}")
                except:
                    print(f"   错误响应: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ POST查询请求异常: {str(e)}")
            return False
    
    def test_get_query(self, query_text: str = "测试查询", **kwargs) -> bool:
        """
        测试GET查询接口
        
        Args:
            query_text: 查询文本
            **kwargs: 其他查询参数
        """
        try:
            print(f"\n🔍 测试GET查询接口: '{query_text}'...")
            
            # 构建查询参数
            params = {
                "q": query_text,
                "top_k": kwargs.get('top_k', 3),
                "mode": kwargs.get('mode', 'vector')
            }
            
            response = requests.get(
                f"{self.base_url}/api/query",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    query_data = result.get('data', {})
                    results = query_data.get('results', [])
                    execution_time = query_data.get('execution_time', 0)
                    search_mode = query_data.get('search_mode', 'unknown')
                    
                    print(f"✅ GET查询成功:")
                    print(f"   - 搜索模式: {search_mode}")
                    print(f"   - 结果数量: {len(results)}")
                    print(f"   - 执行时间: {execution_time}s")
                    
                    return True
                else:
                    print(f"❌ GET查询失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ GET查询请求失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   错误信息: {error_data.get('message', '未知错误')}")
                except:
                    print(f"   错误响应: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ GET查询请求异常: {str(e)}")
            return False
    
    def test_invalid_requests(self) -> bool:
        """测试无效请求的处理"""
        print("\n🔍 测试无效请求处理...")
        
        # 测试空查询
        try:
            response = requests.post(
                f"{self.base_url}/api/query",
                json={"query": ""},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 400:
                print("✅ 空查询正确返回400错误")
            else:
                print(f"❌ 空查询应返回400，实际返回{response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 空查询测试异常: {str(e)}")
            return False
        
        # 测试无效top_k
        try:
            response = requests.post(
                f"{self.base_url}/api/query",
                json={"query": "测试", "top_k": 1000},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 400:
                print("✅ 无效top_k正确返回400错误")
            else:
                print(f"❌ 无效top_k应返回400，实际返回{response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 无效top_k测试异常: {str(e)}")
            return False
        
        return True
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始运行查询API测试套件...")
        print("=" * 60)
        
        start_time = time.time()
        test_results = []
        
        # 基础功能测试
        test_results.append(self.test_health_check())
        test_results.append(self.test_query_modes())
        
        # 查询功能测试
        test_results.append(self.test_post_query("什么是人工智能？", mode="vector", top_k=5))
        test_results.append(self.test_get_query("机器学习", mode="vector", top_k=3))
        
        # 高级功能测试
        test_results.append(self.test_post_query(
            "深度学习算法",
            mode="hybrid",
            top_k=3,
            alpha=0.7,
            filters={"category": "技术"}
        ))
        
        # 错误处理测试
        test_results.append(self.test_invalid_requests())
        
        # 统计结果
        total_time = time.time() - start_time
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print("\n" + "=" * 60)
        print(f"📊 测试结果总结:")
        print(f"   - 总测试数: {total_tests}")
        print(f"   - 通过测试: {passed_tests}")
        print(f"   - 失败测试: {total_tests - passed_tests}")
        print(f"   - 总耗时: {total_time:.2f}s")
        print(f"   - 成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！API工作正常。")
            return True
        else:
            print("⚠️  部分测试失败，请检查API服务。")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="查询API测试工具")
    parser.add_argument(
        "--url",
        default="http://localhost:5000",
        help="API服务地址 (默认: http://localhost:5000)"
    )
    parser.add_argument(
        "--query",
        help="单独测试指定查询文本"
    )
    
    args = parser.parse_args()
    
    tester = QueryAPITester(args.url)
    
    if args.query:
        # 单独测试指定查询
        print(f"🎯 测试单个查询: '{args.query}'")
        tester.test_post_query(args.query)
    else:
        # 运行完整测试套件
        success = tester.run_all_tests()
        exit(0 if success else 1)


if __name__ == "__main__":
    main() 