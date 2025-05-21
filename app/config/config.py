import os
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
load_dotenv()

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"
SAMPLE_DIR = DATA_DIR / "samples"

# 向量库类型配置
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "pg_vector")

# 全文搜索引擎类型配置
FULLTEXT_STORE_TYPE = os.getenv("FULLTEXT_STORE_TYPE", "es")

# PostgreSQL向量库配置
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "user": os.getenv("PG_USER", "root"),
    "password": os.getenv("PG_PASSWORD", "123456"),
    "database": os.getenv("PG_DATABASE", "vector_db"),
    "table_name": os.getenv("PG_VECTOR_TABLE", "document_embeddings"),
}

# Milvus向量库配置
MILVUS_CONFIG = {
    "host": os.getenv("MILVUS_HOST", "localhost"),
    "port": int(os.getenv("MILVUS_PORT", "19530")),
    "collection": os.getenv("MILVUS_COLLECTION", "document_embeddings"),
    "username": os.getenv("MILVUS_USERNAME", ""),
    "password": os.getenv("MILVUS_PASSWORD", ""),
}

# Elasticsearch配置
ES_CONFIG = {
    "host": os.getenv("ES_HOST", "localhost"),
    "port": int(os.getenv("ES_PORT", "9200")),
    "scheme": os.getenv("ES_SCHEME", "http"),
    "index_name": os.getenv("ES_INDEX", "document_fulltext"),
    "username": os.getenv("ES_USERNAME", ""),
    "password": os.getenv("ES_PASSWORD", "")
}

# 向量存储通用配置
VECTOR_STORE_CONFIG = {
    "embed_dim": 1536,  # 默认使用1536维向量（与阿里云text-embedding-v2模型匹配）
}

# 全文搜索通用配置
FULLTEXT_STORE_CONFIG = {
    "embed_dim": 1536,  # 部分全文搜索引擎也需要向量维度（如Milvus和PG用作全文搜索）
}

# Milvus全文搜索特定配置
MILVUS_FULLTEXT_CONFIG = {
    "use_hybrid": os.getenv("MILVUS_FULLTEXT_HYBRID", "true").lower() == "true",  # 是否使用混合搜索
    "drop_ratio_search": float(os.getenv("MILVUS_DROP_RATIO_SEARCH", "0.2")),  # 丢弃低重要性词项的比例
}

# 嵌入模型配置
EMBED_MODEL_TYPE = os.getenv("EMBED_MODEL_TYPE", "aliyun")  # 使用阿里云嵌入模型

# 本地嵌入模型配置
LOCAL_EMBED_MODEL_CONFIG = {
    "model_name": os.getenv("LOCAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
}

# 阿里云百炼嵌入模型配置
ALIYUN_EMBED_MODEL_CONFIG = {
    "api_key": os.getenv("ALIYUN_API_KEY", "sk-c8aff9a84da24605b8cb98ab248e646a"),
    "model_name": os.getenv("ALIYUN_EMBED_MODEL", "text-embedding-v2"),
}

# 重排模型配置
RERANK_MODEL_TYPE = os.getenv("RERANK_MODEL_TYPE", "local")  # 重排模型类型：local或aliyun

# 本地重排模型配置
LOCAL_RERANK_MODEL_CONFIG = {
    "model_name": os.getenv("LOCAL_RERANK_MODEL", "BAAI/bge-reranker-large"),
    "top_n": int(os.getenv("RERANK_TOP_N", "5"))
}

# 阿里云重排模型配置
ALIYUN_RERANK_MODEL_CONFIG = {
    "api_key": os.getenv("ALIYUN_API_KEY", ""),  # 复用阿里云API Key
    "model_name": os.getenv("ALIYUN_RERANK_MODEL", "gte-rerank"),
    "top_n": int(os.getenv("RERANK_TOP_N", "5")),
}

# 外部API重排配置（仅当需要使用外部API时配置）
EXTERNAL_RERANK_API_URL = os.getenv("EXTERNAL_RERANK_API_URL", "")
EXTERNAL_RERANK_API_KEY = os.getenv("EXTERNAL_RERANK_API_KEY", "")

# 聊天模型配置
CHAT_MODEL_TYPE = os.getenv("CHAT_MODEL_TYPE", "aliyun")  # 聊天模型类型：local或aliyun

# 本地聊天模型配置
LOCAL_CHAT_MODEL_CONFIG = {
    "model_name": os.getenv("LOCAL_CHAT_MODEL", "Qwen/Qwen2.5-7B-Chat"),
    "temperature": float(os.getenv("CHAT_TEMPERATURE", "0.7")),
    "max_tokens": int(os.getenv("CHAT_MAX_TOKENS", "2048")),
    "context_window": int(os.getenv("CHAT_CONTEXT_WINDOW", "4096")),
}

# 阿里云聊天模型配置
ALIYUN_CHAT_MODEL_CONFIG = {
    "api_key": os.getenv("ALIYUN_API_KEY", ""),  # 复用阿里云API Key
    "model_name": os.getenv("ALIYUN_CHAT_MODEL", "qwen2.5-32b-instruct"),
    "temperature": float(os.getenv("CHAT_TEMPERATURE", "0.7")),
    "max_tokens": int(os.getenv("CHAT_MAX_TOKENS", "2048")),
}

# 文档处理配置
DOC_PROCESSING_CONFIG = {
    "chunk_size": 1024,
    "chunk_overlap": 20,
}

# 查询配置
QUERY_CONFIG = {
    "similarity_top_k": 5,
    "response_mode": "compact",
} 