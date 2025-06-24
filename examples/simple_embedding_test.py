#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版本地 Embedding 模型测试

快速验证本地 embedding 模型的基本功能：
1. 模型初始化
2. 文本嵌入
3. 查询嵌入
4. 相似度计算

运行命令：
python examples/simple_embedding_test.py
"""

import os
import sys
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.model.embedding_model import LocalEmbeddingModel
from app.config.config import LOCAL_EMBED_MODEL_CONFIG


def main():
    """主测试函数"""
    print("🚀 简化版本地 Embedding 模型测试")
    print(f"📋 模型: {LOCAL_EMBED_MODEL_CONFIG['model_name']}")
    print("-" * 50)
    
    try:
        # 1. 初始化模型
        print("1️⃣ 初始化本地嵌入模型...")
        start_time = time.time()
        embedding_model = LocalEmbeddingModel()
        init_time = time.time() - start_time
        print(f"   ✅ 初始化成功 (耗时: {init_time:.2f}秒)")
        
        # 2. 测试文本嵌入
        print("\n2️⃣ 测试文本嵌入...")
        test_text = "人工智能技术发展迅速"
        start_time = time.time()
        text_embedding = embedding_model._get_text_embedding(test_text)
        embed_time = time.time() - start_time
        
        print(f"   文本: {test_text}")
        print(f"   维度: {len(text_embedding)}")
        print(f"   类型: {type(text_embedding)}")
        print(f"   样例: {text_embedding[:3]}")
        print(f"   ✅ 文本嵌入成功 (耗时: {embed_time:.2f}秒)")
        
        # 3. 测试查询嵌入
        print("\n3️⃣ 测试查询嵌入...")
        test_query = "什么是AI技术？"
        start_time = time.time()
        query_embedding = embedding_model._get_query_embedding(test_query)
        query_time = time.time() - start_time
        
        print(f"   查询: {test_query}")
        print(f"   维度: {len(query_embedding)}")
        print(f"   样例: {query_embedding[:3]}")
        print(f"   ✅ 查询嵌入成功 (耗时: {query_time:.2f}秒)")
        
        # 4. 测试相似度计算
        print("\n4️⃣ 测试相似度计算...")
        
        # 测试相似文本
        similar_text = "AI技术快速发展"
        similar_embedding = embedding_model._get_text_embedding(similar_text)
        
        # 测试不相关文本
        different_text = "今天天气很好"
        different_embedding = embedding_model._get_text_embedding(different_text)
        
        # 计算相似度
        sim_similar = cosine_similarity([text_embedding], [similar_embedding])[0][0]
        sim_different = cosine_similarity([text_embedding], [different_embedding])[0][0]
        sim_query = cosine_similarity([text_embedding], [query_embedding])[0][0]
        
        print(f"   原文本: {test_text}")
        print(f"   相似文本: {similar_text}")
        print(f"   相似度: {sim_similar:.4f}")
        print(f"   ")
        print(f"   不相关文本: {different_text}")
        print(f"   相似度: {sim_different:.4f}")
        print(f"   ")
        print(f"   查询文本: {test_query}")
        print(f"   相似度: {sim_query:.4f}")
        
        # 5. 结果评估
        print("\n5️⃣ 结果评估...")
        if sim_similar > sim_different:
            print("   ✅ 相似文本比不相关文本有更高相似度")
        else:
            print("   ⚠️  相似度计算可能存在问题")
        
        if sim_query > 0.5:
            print("   ✅ 查询与原文本有合理的相似度")
        else:
            print("   ⚠️  查询相似度较低")
        
        print(f"\n🎉 测试完成！")
        print(f"📊 性能总结:")
        print(f"   初始化耗时: {init_time:.2f}秒")
        print(f"   平均嵌入耗时: {(embed_time + query_time) / 2:.2f}秒")
        print(f"   向量维度: {len(text_embedding)}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("\n💡 可能的解决方案:")
        print("   1. 检查 ollama 服务是否运行: ollama serve")
        print("   2. 检查模型是否已下载: ollama pull dengcao/Qwen3-Embedding-8B:Q5_K_M")
        print("   3. 检查网络连接")
        print("   4. 检查环境变量配置")


if __name__ == "__main__":
    main() 