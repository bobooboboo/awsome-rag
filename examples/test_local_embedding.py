#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地 Embedding 模型测试示例

该示例演示如何：
1. 初始化本地 embedding 模型
2. 测试文本嵌入功能
3. 测试查询嵌入功能
4. 验证嵌入向量的维度和质量
5. 测试批量嵌入
6. 计算相似度
7. 性能基准测试

使用前请确保：
- 已安装 ollama
- 已下载指定的模型（dengcao/Qwen3-Embedding-8B:Q5_K_M）
- ollama 服务正在运行（默认端口 11434）

运行命令：
python examples/test_local_embedding.py
"""

import os
import sys
import time
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.model.embedding_model import LocalEmbeddingModel, get_embedding_model
from app.config.config import LOCAL_EMBED_MODEL_CONFIG, EMBED_MODEL_TYPE


def test_basic_embedding():
    """测试基本的嵌入功能"""
    print("=" * 60)
    print("🔬 测试基本嵌入功能")
    print("=" * 60)
    
    # 初始化本地嵌入模型
    try:
        embedding_model = LocalEmbeddingModel()
        print(f"✅ 成功初始化本地嵌入模型: {LOCAL_EMBED_MODEL_CONFIG['model_name']}")
    except Exception as e:
        print(f"❌ 初始化模型失败: {e}")
        return None
    
    # 测试文本
    test_texts = [
        "今天天气真好，阳光明媚。",
        "机器学习是人工智能的重要分支。",
        "自然语言处理技术发展迅速。",
        "深度学习在计算机视觉中应用广泛。"
    ]
    
    print("\n📝 测试文本列表:")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. {text}")
    
    # 测试单个文本嵌入
    print("\n🔍 测试单个文本嵌入:")
    try:
        text = test_texts[0]
        start_time = time.time()
        embedding = embedding_model._get_text_embedding(text)
        end_time = time.time()
        
        print(f"  输入文本: {text}")
        print(f"  嵌入维度: {len(embedding)}")
        print(f"  向量类型: {type(embedding)}")
        print(f"  前5个值: {embedding[:5]}")
        print(f"  耗时: {end_time - start_time:.3f}秒")
        
        # 验证向量是否有效
        if embedding and len(embedding) > 0:
            print("  ✅ 文本嵌入成功")
        else:
            print("  ❌ 文本嵌入失败")
            return None
            
    except Exception as e:
        print(f"  ❌ 文本嵌入异常: {e}")
        return None
    
    return embedding_model


def test_query_embedding(embedding_model: LocalEmbeddingModel):
    """测试查询嵌入功能"""
    print("\n" + "=" * 60)
    print("🔍 测试查询嵌入功能")
    print("=" * 60)
    
    # 测试查询
    test_queries = [
        "什么是机器学习？",
        "今天的天气如何？",
        "NLP技术有哪些应用？"
    ]
    
    print("\n📋 测试查询列表:")
    for i, query in enumerate(test_queries, 1):
        print(f"  {i}. {query}")
    
    try:
        query = test_queries[0]
        start_time = time.time()
        query_embedding = embedding_model._get_query_embedding(query)
        end_time = time.time()
        
        print(f"\n🔍 查询嵌入结果:")
        print(f"  查询文本: {query}")
        print(f"  嵌入维度: {len(query_embedding)}")
        print(f"  前5个值: {query_embedding[:5]}")
        print(f"  耗时: {end_time - start_time:.3f}秒")
        
        if query_embedding and len(query_embedding) > 0:
            print("  ✅ 查询嵌入成功")
        else:
            print("  ❌ 查询嵌入失败")
            
    except Exception as e:
        print(f"  ❌ 查询嵌入异常: {e}")


def test_batch_embedding(embedding_model: LocalEmbeddingModel):
    """测试批量嵌入"""
    print("\n" + "=" * 60)
    print("📦 测试批量嵌入")
    print("=" * 60)
    
    # 测试文本批次
    batch_texts = [
        "人工智能正在改变世界",
        "深度学习是AI的核心技术",
        "自然语言处理让机器理解人类语言",
        "计算机视觉让机器看懂世界",
        "推荐系统提升用户体验",
        "知识图谱构建智能系统",
        "强化学习实现智能决策",
        "神经网络模拟人脑工作"
    ]
    
    print(f"\n📋 批量处理 {len(batch_texts)} 个文本:")
    for i, text in enumerate(batch_texts, 1):
        print(f"  {i}. {text}")
    
    try:
        start_time = time.time()
        embeddings = []
        
        # 逐个处理（模拟批量）
        for text in batch_texts:
            embedding = embedding_model._get_text_embedding(text)
            embeddings.append(embedding)
        
        end_time = time.time()
        
        print(f"\n📊 批量嵌入结果:")
        print(f"  处理文本数: {len(embeddings)}")
        print(f"  总耗时: {end_time - start_time:.3f}秒")
        print(f"  平均每个: {(end_time - start_time) / len(batch_texts):.3f}秒")
        print(f"  向量维度: {len(embeddings[0]) if embeddings else 0}")
        print("  ✅ 批量嵌入成功")
        
        return embeddings
        
    except Exception as e:
        print(f"  ❌ 批量嵌入异常: {e}")
        return []


def test_similarity_calculation(embeddings: List[List[float]]):
    """测试相似度计算"""
    print("\n" + "=" * 60)
    print("🎯 测试相似度计算")
    print("=" * 60)
    
    if len(embeddings) < 2:
        print("❌ 需要至少2个嵌入向量来计算相似度")
        return
    
    try:
        # 转换为numpy数组
        embeddings_array = np.array(embeddings)
        
        # 计算余弦相似度矩阵
        similarity_matrix = cosine_similarity(embeddings_array)
        
        print(f"\n📊 相似度矩阵 ({len(embeddings)}x{len(embeddings)}):")
        
        # 显示相似度矩阵（保留3位小数）
        print("     ", end="")
        for i in range(len(embeddings)):
            print(f"  {i:2d}  ", end="")
        print()
        
        for i in range(len(embeddings)):
            print(f"  {i:2d} ", end="")
            for j in range(len(embeddings)):
                print(f"{similarity_matrix[i][j]:5.3f}", end=" ")
            print()
        
        # 找出最相似的文本对（排除自身）
        max_similarity = 0
        max_pair = (0, 1)
        
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                if similarity_matrix[i][j] > max_similarity:
                    max_similarity = similarity_matrix[i][j]
                    max_pair = (i, j)
        
        print(f"\n🏆 最相似的文本对:")
        print(f"  文本 {max_pair[0]} 和文本 {max_pair[1]}")
        print(f"  相似度: {max_similarity:.4f}")
        print("  ✅ 相似度计算成功")
        
    except Exception as e:
        print(f"❌ 相似度计算异常: {e}")


def test_vector_quality(embedding_model: LocalEmbeddingModel):
    """测试向量质量"""
    print("\n" + "=" * 60)
    print("⭐ 测试向量质量")
    print("=" * 60)
    
    # 测试不同类型的文本
    test_cases = [
        {
            "category": "相似文本",
            "texts": [
                "机器学习是人工智能的重要分支",
                "人工智能包含机器学习技术"
            ]
        },
        {
            "category": "不同主题",
            "texts": [
                "今天天气很好，阳光明媚",
                "深度学习神经网络训练"
            ]
        },
        {
            "category": "语言差异",
            "texts": [
                "自然语言处理技术",
                "Natural Language Processing"
            ]
        }
    ]
    
    for case in test_cases:
        print(f"\n🔬 测试案例: {case['category']}")
        try:
            embeddings = []
            for text in case['texts']:
                embedding = embedding_model._get_text_embedding(text)
                embeddings.append(embedding)
                print(f"  文本: {text}")
            
            # 计算相似度
            if len(embeddings) == 2:
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                print(f"  相似度: {similarity:.4f}")
                
                # 质量评估
                if case['category'] == "相似文本" and similarity > 0.7:
                    print("  ✅ 相似文本有高相似度，向量质量良好")
                elif case['category'] == "不同主题" and similarity < 0.5:
                    print("  ✅ 不同主题有低相似度，向量区分性良好")
                elif case['category'] == "语言差异":
                    print(f"  📝 跨语言相似度: {similarity:.4f}")
                else:
                    print("  ⚠️  向量质量需要进一步验证")
            
        except Exception as e:
            print(f"  ❌ 测试案例异常: {e}")


def test_performance_benchmark(embedding_model: LocalEmbeddingModel):
    """性能基准测试"""
    print("\n" + "=" * 60)
    print("⚡ 性能基准测试")
    print("=" * 60)
    
    # 不同长度的文本
    test_texts = {
        "短文本": "AI技术",
        "中等文本": "人工智能技术在各个领域都有广泛的应用前景",
        "长文本": "随着深度学习技术的快速发展，自然语言处理、计算机视觉、语音识别等AI应用领域取得了突破性进展。这些技术不仅在学术研究中表现优异，也在工业界得到了广泛应用，为人类社会带来了巨大的变革和便利。"
    }
    
    for text_type, text in test_texts.items():
        print(f"\n📏 测试 {text_type} (长度: {len(text)} 字符):")
        print(f"  文本: {text[:50]}...")
        
        try:
            # 多次测试取平均值
            times = []
            for _ in range(3):
                start_time = time.time()
                embedding = embedding_model._get_text_embedding(text)
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"  平均耗时: {avg_time:.3f}秒")
            print(f"  最快耗时: {min_time:.3f}秒")
            print(f"  最慢耗时: {max_time:.3f}秒")
            print(f"  向量维度: {len(embedding)}")
            
            # 计算吞吐率
            throughput = len(text) / avg_time
            print(f"  处理速度: {throughput:.1f} 字符/秒")
            
        except Exception as e:
            print(f"  ❌ 性能测试异常: {e}")


def test_model_consistency(embedding_model: LocalEmbeddingModel):
    """测试模型一致性"""
    print("\n" + "=" * 60)
    print("🔄 测试模型一致性")
    print("=" * 60)
    
    test_text = "测试模型输出一致性"
    print(f"测试文本: {test_text}")
    
    try:
        embeddings = []
        print("\n进行5次嵌入测试:")
        
        for i in range(5):
            embedding = embedding_model._get_text_embedding(test_text)
            embeddings.append(embedding)
            print(f"  第{i+1}次: 前3个值 {embedding[:3]}")
        
        # 检查一致性
        if all(np.array_equal(embeddings[0], emb) for emb in embeddings[1:]):
            print("  ✅ 模型输出完全一致")
        else:
            # 计算相似度
            similarities = []
            for i in range(1, len(embeddings)):
                sim = cosine_similarity([embeddings[0]], [embeddings[i]])[0][0]
                similarities.append(sim)
            
            avg_similarity = sum(similarities) / len(similarities)
            print(f"  📊 平均相似度: {avg_similarity:.6f}")
            
            if avg_similarity > 0.999:
                print("  ✅ 模型输出高度一致")
            else:
                print("  ⚠️  模型输出存在差异")
                
    except Exception as e:
        print(f"❌ 一致性测试异常: {e}")


def main():
    """主测试函数"""
    print("🚀 本地 Embedding 模型测试开始")
    print(f"📋 当前配置:")
    print(f"  模型类型: {EMBED_MODEL_TYPE}")
    print(f"  模型名称: {LOCAL_EMBED_MODEL_CONFIG['model_name']}")
    
    # 检查环境
    if EMBED_MODEL_TYPE != "local":
        print("⚠️  当前配置不是本地模型，请设置 EMBED_MODEL_TYPE=local")
        return
    
    # 1. 基本功能测试
    embedding_model = test_basic_embedding()
    if not embedding_model:
        print("❌ 基本功能测试失败，终止测试")
        return
    
    # 2. 查询嵌入测试
    test_query_embedding(embedding_model)
    
    # 3. 批量嵌入测试
    embeddings = test_batch_embedding(embedding_model)
    
    # 4. 相似度计算测试
    if embeddings:
        test_similarity_calculation(embeddings)
    
    # 5. 向量质量测试
    test_vector_quality(embedding_model)
    
    # 6. 性能基准测试
    test_performance_benchmark(embedding_model)
    
    # 7. 模型一致性测试
    test_model_consistency(embedding_model)
    
    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)
    
    # 总结建议
    print("\n💡 使用建议:")
    print("  1. 确保 ollama 服务正常运行")
    print("  2. 根据业务需求选择合适的模型")
    print("  3. 监控嵌入质量和性能指标")
    print("  4. 定期测试模型一致性")


if __name__ == "__main__":
    main() 