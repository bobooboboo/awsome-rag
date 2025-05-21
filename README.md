# RAG 检索系统

基于 llama-index 的文档检索系统，专注于高效的文本检索功能。

## 项目说明

本项目是一个专注于文档检索的 RAG (检索增强生成) 系统，核心功能包括：

1. 文档上传与管理
2. 文档解析和向量化
3. 基于语义的高效文本检索
4. 易用的 API 接口

该系统不生成回答内容，仅返回与查询相关的文档片段和参考源。

## 技术栈

- Python 3.10
- Flask Web框架
- llama-index 作为RAG核心框架
- 向量存储支持
  - PostgreSQL + pgvector
  - Milvus 向量数据库
- 嵌入模型支持
  - 本地 Sentence Transformers 模型
  - 阿里云百炼API嵌入服务

## 安装指南

### 环境要求

- Python 3.10+
- 向量数据库（任选其一）：
  - PostgreSQL 14+ (已安装 pgvector 扩展)
  - Milvus 2.3+
- Conda

### 设置步骤

1. 克隆项目

```bash
git clone https://github.com/your-username/awsome-rag.git
cd awsome-rag
```

2. 创建并激活conda环境

```bash
conda create -n awsome-rag python=3.10
conda activate awsome-rag
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置环境变量

复制示例环境变量文件并根据需要修改

```bash
cp app/config/env.example .env
```

5. 配置向量数据库

根据您选择的向量数据库进行配置：

**PostgreSQL + pgvector**:
```sql
CREATE EXTENSION vector;
```

**Milvus**:
确保Milvus服务已启动并可访问。

## 配置说明

系统通过 `.env` 文件进行配置，主要配置项包括：

### 向量库配置

```
# 向量库类型配置
VECTOR_STORE_TYPE=pg_vector  # 可选: pg_vector, milvus

# PostgreSQL向量库配置 (当VECTOR_STORE_TYPE=pg_vector时使用)
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_DATABASE=ragdb
PG_VECTOR_TABLE=document_embeddings

# Milvus向量库配置 (当VECTOR_STORE_TYPE=milvus时使用)
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=document_embeddings
```

### 嵌入模型配置

```
# 嵌入模型配置
EMBED_MODEL_TYPE=local  # 可选: local, aliyun

# 本地模型配置 (当EMBED_MODEL_TYPE=local时使用)
LOCAL_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# 阿里云百炼模型配置 (当EMBED_MODEL_TYPE=aliyun时使用)
ALIYUN_API_KEY=your_api_key
ALIYUN_API_SECRET=your_api_secret
ALIYUN_EMBED_MODEL=embedding-v1
ALIYUN_ENDPOINT=https://bailian.aliyuncs.com
```

## 使用方法

### 启动服务器

```bash
python main.py
```

服务默认在 http://localhost:5000 运行。

### API 接口

#### 文档上传

```
POST /api/data/upload
```

表单参数:
- `file`: 要上传的文件（目前支持PDF）
- `metadata`: 可选的JSON格式元数据

#### 文档查询

```
POST /api/data/query
```

JSON参数:
```json
{
  "query": "查询文本",
  "top_k": 5,  // 可选，返回结果数量
  "filter": {  // 可选，元数据过滤条件
    "metadata": {
      "document_id": "xxx" 
    }
  }
}
```

#### 文档列表

```
GET /api/data/documents
```

#### 删除文档

```
DELETE /api/data/documents/{document_id}
```

#### 健康检查

```
GET /health
```

## 项目结构

```
app/
├── api/                   # API接口
├── model/                 # 嵌入模型
├── query_processing/      # 查询处理
├── query_construction/    # 查询构建
├── data_indexing/         # 数据索引
├── data_source/           # 数据源
│   └── vector/            # 向量数据库
│       ├── base.py        # 向量数据库基类
│       ├── factory.py     # 向量数据库工厂
│       ├── pg_vector.py   # PostgreSQL向量库实现
│       └── milvus.py      # Milvus向量库实现
├── metadata/              # 元数据
└── config/                # 配置
```

## 许可证

MIT