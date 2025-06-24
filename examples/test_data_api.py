#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据API测试脚本
测试文档上传、查询、删除等功能
"""

import requests
import json
import time
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:5001"

def test_upload_document():
    """测试单个文档上传"""
    print("=== 测试单个文档上传 ===")
    
    # 创建测试文件
    test_file_path = Path("test_document.txt")
    test_content = """
这是一个测试文档。
本文档用于测试RAG系统的文档上传功能。
包含多个段落和句子，用于测试文档分割功能。

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支。
它旨在创建能够模拟人类智能行为的系统。
机器学习是人工智能的一个重要子领域。

自然语言处理（Natural Language Processing，NLP）是AI的另一个重要分支。
它专注于让计算机理解和生成人类语言。
    """.strip()
    
    # 写入测试文件
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        # 准备上传
        with open(test_file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'split_strategy': 'sentence',
                'chunk_size': '300',
                'chunk_overlap': '50',
                'metadata': json.dumps({"category": "测试文档", "source": "test_script"})
            }
            
            response = requests.post(f"{BASE_URL}/api/data/upload", files=files, data=data)
            
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            return response.json()['data']['file_id']
        return None
        
    except Exception as e:
        print(f"上传失败: {str(e)}")
        return None
    finally:
        # 清理测试文件
        if test_file_path.exists():
            test_file_path.unlink()

def test_list_documents():
    """测试文档列表查询"""
    print("\n=== 测试文档列表查询 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/data/list?page=1&page_size=10")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"查询失败: {str(e)}")

def test_stats():
    """测试统计信息"""
    print("\n=== 测试统计信息 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/data/stats")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")

def test_query_uploaded_document():
    """测试查询上传的文档"""
    print("\n=== 测试查询上传的文档 ===")
    
    try:
        # 查询关于人工智能的内容
        query_data = {
            "query": "什么是人工智能？",
            "top_k": 3,
            "mode": "vector"
        }
        
        response = requests.post(f"{BASE_URL}/api/query", json=query_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"查询到 {len(result['data']['results'])} 个结果:")
            for i, result_item in enumerate(result['data']['results']):
                print(f"  结果 {i+1}:")
                print(f"    分数: {result_item['score']:.4f}")
                print(f"    内容: {result_item['text'][:100]}...")
                if 'metadata' in result_item:
                    print(f"    文件: {result_item['metadata'].get('file_name', 'unknown')}")
                    # 返回第一个文件的ID用于后续测试
                    if i == 0:
                        return result_item['metadata'].get('file_id')
        else:
            print(f"查询失败: {response.text}")
            
    except Exception as e:
        print(f"查询失败: {str(e)}")
    
    return None

def test_document_info(file_id):
    """测试获取文档信息"""
    if not file_id:
        print("\n=== 跳过文档信息测试（没有可用的文件ID） ===")
        return
        
    print(f"\n=== 测试获取文档信息 (ID: {file_id}) ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/data/document/{file_id}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"获取文档信息失败: {str(e)}")

def test_document_download(file_id):
    """测试文档下载"""
    if not file_id:
        print("\n=== 跳过文档下载测试（没有可用的文件ID） ===")
        return
        
    print(f"\n=== 测试文档下载 (ID: {file_id}) ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/data/download/{file_id}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查响应头
            content_type = response.headers.get('Content-Type', '')
            content_disposition = response.headers.get('Content-Disposition', '')
            content_length = response.headers.get('Content-Length', '')
            
            print(f"Content-Type: {content_type}")
            print(f"Content-Disposition: {content_disposition}")
            print(f"Content-Length: {content_length}")
            print(f"文件大小: {len(response.content)} bytes")
            print("文档下载成功（未实际保存文件）")
        else:
            print(f"下载失败: {response.text}")
            
    except Exception as e:
        print(f"文档下载失败: {str(e)}")

def test_delete_document(file_id):
    """测试删除文档"""
    if not file_id:
        print("\n=== 跳过删除测试（没有可删除的文件ID） ===")
        return
        
    print(f"\n=== 测试删除文档 (ID: {file_id}) ===")
    
    try:
        delete_data = {
            "file_ids": [file_id],
            "delete_files": True
        }
        
        response = requests.delete(f"{BASE_URL}/api/data/delete", json=delete_data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"删除失败: {str(e)}")

def test_batch_upload():
    """测试批量上传"""
    print("\n=== 测试批量上传 ===")
    
    # 创建多个测试文件
    test_files = []
    for i in range(2):
        file_path = Path(f"test_batch_{i}.txt")
        content = f"""
这是批量上传测试文件 {i+1}。
包含关于机器学习的内容。

机器学习是人工智能的一个重要分支，它通过数据训练模型。
常见的机器学习算法包括线性回归、决策树、神经网络等。
深度学习是机器学习的一个子集，使用多层神经网络。
        """.strip()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        test_files.append(file_path)
    
    try:
        # 准备批量上传
        files = []
        for file_path in test_files:
            files.append(('files', open(file_path, 'rb')))
        
        data = {
            'split_strategy': 'sentence',
            'chunk_size': '200',
            'chunk_overlap': '30',
            'metadata': json.dumps({"category": "批量测试", "batch": "test_batch_1"})
        }
        
        response = requests.post(f"{BASE_URL}/api/data/batch_upload", files=files, data=data)
        
        # 关闭文件
        for _, file_obj in files:
            file_obj.close()
            
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            return [item['file_id'] for item in response.json()['data']['uploaded_files']]
        return []
        
    except Exception as e:
        print(f"批量上传失败: {str(e)}")
        return []
    finally:
        # 清理测试文件
        for file_path in test_files:
            if file_path.exists():
                file_path.unlink()

def test_directory_import():
    """测试目录导入"""
    print("\n=== 测试目录导入 ===")
    
    # 创建测试目录和文件
    test_dir = Path("test_import_dir")
    test_dir.mkdir(exist_ok=True)
    
    # 创建子目录
    sub_dir = test_dir / "subdoc"
    sub_dir.mkdir(exist_ok=True)
    
    test_files = [
        (test_dir / "doc1.txt", "这是第一个导入测试文档，包含向量数据库的相关内容。"),
        (test_dir / "doc2.txt", "这是第二个导入测试文档，包含全文搜索的相关内容。"),
        (sub_dir / "subdoc1.txt", "这是子目录中的文档，包含检索增强生成的相关内容。")
    ]
    
    # 写入测试文件
    for file_path, content in test_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    try:
        import_data = {
            "directory_path": str(test_dir.absolute()),
            "recursive": True,
            "file_pattern": "*.txt",
            "split_strategy": "sentence",
            "chunk_size": 100,
            "chunk_overlap": 20,
            "metadata": {"category": "目录导入测试", "source": "test_directory"}
        }
        
        response = requests.post(f"{BASE_URL}/api/data/import", json=import_data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            return [item['file_id'] for item in response.json()['data']['imported_files']]
        return []
        
    except Exception as e:
        print(f"目录导入失败: {str(e)}")
        return []
    finally:
        # 清理测试目录
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)

def main():
    """主测试函数"""
    print("开始测试数据API...")
    print(f"API服务器: {BASE_URL}")
    
    # 首先检查API服务是否可用
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("API服务器不可用，请先启动服务器")
            return
    except Exception as e:
        print(f"无法连接到API服务器: {str(e)}")
        print("请确保已启动服务器: python main.py")
        return
    
    # 记录所有上传的文件ID，用于最后清理
    uploaded_file_ids = []
    
    # 测试单个文档上传
    file_id = test_upload_document()
    if file_id:
        uploaded_file_ids.append(file_id)
    
    # 测试批量上传
    batch_ids = test_batch_upload()
    uploaded_file_ids.extend(batch_ids)
    
    # 测试目录导入
    import_ids = test_directory_import()
    uploaded_file_ids.extend(import_ids)
    
    # 等待一会儿，让索引完成
    time.sleep(2)
    
    # 测试查询功能，并获取一个文件ID用于后续测试
    query_file_id = test_query_uploaded_document()
    
    # 测试文档信息和下载功能
    test_document_info(query_file_id)
    test_document_download(query_file_id)
    
    # 测试列表查询
    test_list_documents()
    
    # 测试统计信息
    test_stats()
    
    # 清理：删除所有上传的文档
    if uploaded_file_ids:
        print(f"\n=== 清理测试数据 (删除 {len(uploaded_file_ids)} 个文档) ===")
        try:
            delete_data = {
                "file_ids": uploaded_file_ids,
                "delete_files": True
            }
            response = requests.delete(f"{BASE_URL}/api/data/delete", json=delete_data)
            print(f"清理状态码: {response.status_code}")
            if response.status_code == 200:
                print("测试数据清理完成")
            else:
                print(f"清理失败: {response.text}")
        except Exception as e:
            print(f"清理失败: {str(e)}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main() 