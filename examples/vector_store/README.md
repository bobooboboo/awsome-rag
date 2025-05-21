# 向量存储测试示例

本目录包含用于测试向量存储实现的示例代码。

## 环境要求

### Milvus测试
- 已安装并启动Milvus服务（可以使用Docker快速启动）
- 安装Milvus Python客户端: `pip install pymilvus`

### PostgreSQL/PGVector测试
- 已安装并启动PostgreSQL服务（需要安装pgvector扩展）
- 安装PostgreSQL Python客户端: `pip install psycopg2-binary`

## 配置设置

测试代码从项目的配置文件中获取数据库连接参数，这些配置最终来源于环境变量或`.env`文件。

### 配置方式

1. 创建或编辑项目根目录下的`.env`文件
2. 设置以下参数（示例）:

```
# 向量库类型配置
VECTOR_STORE_TYPE=pg_vector  # 或 milvus

# PostgreSQL向量库配置
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_DATABASE=postgres
PG_VECTOR_TABLE=test_vector_store

# Milvus向量库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=test_collection
MILVUS_USERNAME=
MILVUS_PASSWORD=

# 向量维度配置
VECTOR_EMBED_DIM=1536
```

## 运行测试

### Milvus测试

1. 确保Milvus服务已启动
2. 在`.env`文件中设置正确的Milvus连接参数
3. 运行测试:
```bash
python examples/vector_store/test_milvus.py
```

### PGVector测试

1. 确保PostgreSQL服务已启动，并已安装pgvector扩展
2. 在`.env`文件中设置正确的PostgreSQL连接参数
3. 运行测试:
```bash
python examples/vector_store/test_pg_vector.py
```

## 使用Docker快速启动测试环境

### Milvus

```bash
# 拉取并启动Milvus Standalone
docker run -d --name milvus_standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:v2.3.3 standalone
```

### PostgreSQL with pgvector

```bash
# 拉取并启动PostgreSQL
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector
```

## 测试内容

这些测试示例包含以下功能的验证：

1. 初始化向量存储
2. 添加数据（TextNode对象）
3. 通过ID获取数据
4. 通过过滤条件获取数据
5. 文本语义搜索
6. 删除数据（通过ID和过滤条件）

## 注意事项

- 测试会创建新的集合/表，如果同名集合/表已存在，将被覆盖（通过overwrite=True参数）
- 测试完成后，建议清理测试数据（删除测试集合/表） 