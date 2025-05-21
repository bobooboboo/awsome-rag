import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# 检查必要的环境变量是否存在
def check_required_env_vars():
    """检查必要的环境变量是否存在"""
    # 获取向量库类型
    vector_store_type = os.getenv("VECTOR_STORE_TYPE", "pg_vector")
    embed_model_type = os.getenv("EMBED_MODEL_TYPE", "aliyun")

    missing_vars = []

    # 检查向量库相关配置
    if vector_store_type == "pg_vector":
        required_vars = [
            "PG_HOST", "PG_PORT", "PG_USER", "PG_PASSWORD", "PG_DATABASE", "PG_VECTOR_TABLE"
        ]

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

    elif vector_store_type == "milvus":
        required_vars = [
            "MILVUS_HOST", "MILVUS_PORT", "MILVUS_COLLECTION", "MILVUS_USERNAME", "MILVUS_PASSWORD"
        ]

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

    # 检查嵌入模型相关配置
    if embed_model_type == "local":
        if not os.getenv("LOCAL_EMBED_MODEL"):
            missing_vars.append("LOCAL_EMBED_MODEL")

    elif embed_model_type == "aliyun":
        required_vars = [
            "ALIYUN_API_KEY", "ALIYUN_EMBED_MODEL"
        ]

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

    if missing_vars:
        print(f"警告: 以下环境变量未设置: {', '.join(missing_vars)}")
        print("将使用默认值，确保生产环境中正确设置这些变量")

    return len(missing_vars) == 0


# 封装环境变量获取函数
def get_env(key, default=None):
    """
    获取环境变量，如果不存在则返回默认值
    """
    return os.getenv(key, default)
