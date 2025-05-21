#!/bin/bash

# 向量存储测试运行脚本

# 确保在项目根目录运行
cd "$(dirname "$0")/../.." || exit

echo "===== 开始向量存储测试 ====="

# 运行Milvus测试
echo -e "\n===== 测试Milvus向量存储 ====="
python examples/vector_store/test_milvus.py

# 运行PGVector测试
echo -e "\n===== 测试PGVector向量存储 ====="
python examples/vector_store/test_pg_vector.py

echo -e "\n===== 所有测试完成 =====" 