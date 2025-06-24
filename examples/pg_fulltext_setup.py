#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL全文索引设置工具

该脚本用于在PostgreSQL数据库中设置全文索引，以优化全文检索性能。
它适用于已使用llama-index的PGVectorStore创建的表格。
注意：llama-index会自动在表名前添加"data_"前缀。

全文索引依赖PostgreSQL的文本搜索功能。对于中文全文检索，建议安装zhparser扩展：
1. Ubuntu/Debian: sudo apt-get install libscws-dev
2. 然后: git clone https://github.com/amutu/zhparser.git && cd zhparser && make && make install
3. 在PostgreSQL中: CREATE EXTENSION zhparser;

如果未安装zhparser，将使用默认英文分词器，中文检索效果会受到影响。
"""

import argparse
import logging
import sys
from pathlib import Path

import psycopg2

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

# 正确导入配置
from app.config.config import PG_CONFIG, VECTOR_STORE_CONFIG

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

def create_table_if_not_exists(table_name=None, embed_dim=None):
    """
    创建包含text_search_tsv列的表，如果表不存在
    
    Args:
        table_name: 表名，默认使用配置中的表名
        embed_dim: 嵌入维度，默认使用配置中的值
    
    Returns:
        bool: 是否创建或确认了表
    """
    # 获取基础表名和维度
    base_table_name = table_name or PG_CONFIG.get("table_name", "document_embeddings")
    embed_dim = embed_dim or VECTOR_STORE_CONFIG.get("embed_dim", 1536)
    
    # 添加llama-index使用的前缀
    actual_table_name = f"data_{base_table_name}"
    
    logger.info(f"检查表 {actual_table_name} 是否存在...")
    
    try:
        # 连接数据库
        conn = psycopg2.connect(
            host=PG_CONFIG["host"],
            port=PG_CONFIG["port"],
            user=PG_CONFIG["user"],
            password=PG_CONFIG["password"],
            database=PG_CONFIG["database"]
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute(f"SELECT to_regclass('{actual_table_name}');")
        table_exists = cursor.fetchone()[0] is not None
        
        if not table_exists:
            logger.info(f"表 {actual_table_name} 不存在，创建新表...")
            
            # 确保pgvector扩展存在
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # 创建新表，包含text_search_tsv列
            create_table_sql = f"""
            CREATE TABLE {actual_table_name} (
                id SERIAL PRIMARY KEY,
                text TEXT,
                metadata_ JSONB,
                node_id TEXT,
                embedding vector({embed_dim}),
                text_search_tsv tsvector
            );
            """
            cursor.execute(create_table_sql)
            logger.info(f"表 {actual_table_name} 创建成功")
            
            # 创建embedding字段的索引
            cursor.execute(f"CREATE INDEX ON {actual_table_name} USING ivfflat (embedding vector_cosine_ops);")
            logger.info("向量索引创建成功")
            
            # 创建node_id字段的索引
            cursor.execute(f"CREATE INDEX ON {actual_table_name} (node_id);")
            logger.info("节点ID索引创建成功")
            
            # 确定要使用的文本搜索配置
            try:
                cursor.execute("SELECT cfgname FROM pg_ts_config WHERE cfgname = 'chinese';")
                ts_config = 'public.chinese' if cursor.fetchone() else 'pg_catalog.english'
            except:
                ts_config = 'pg_catalog.english'
            
            # 创建触发器，自动更新text_search_tsv列
            trigger_name = f"{actual_table_name}_text_vector_update"
            cursor.execute(f"""
            CREATE TRIGGER {trigger_name}
            BEFORE INSERT OR UPDATE ON {actual_table_name}
            FOR EACH ROW
            EXECUTE FUNCTION tsvector_update_trigger(text_search_tsv, '{ts_config}', text);
            """)
            logger.info("触发器创建成功")
            
            # 创建text_search_tsv的GIN索引
            tsv_index_name = f"idx_{actual_table_name}_text_search_tsv"
            cursor.execute(f"CREATE INDEX {tsv_index_name} ON {actual_table_name} USING gin(text_search_tsv);")
            logger.info(f"全文索引 {tsv_index_name} 创建成功")
            
        else:
            # 表已存在，检查是否有text_search_tsv列
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{actual_table_name}' AND column_name = 'text_search_tsv';")
            if not cursor.fetchone():
                logger.info(f"表 {actual_table_name} 已存在但缺少text_search_tsv列，将添加此列...")
                setup_fulltext_index(table_name, content_column='text')
            else:
                logger.info(f"表 {actual_table_name} 已存在且包含text_search_tsv列")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"创建或检查表时出错: {e}")
        return False

def setup_fulltext_index(table_name=None, content_column='text'):
    """
    为PostgreSQL表设置中文全文搜索索引
    
    Args:
        table_name: 表名，默认使用配置中的表名
        content_column: 文本内容列名
    """
    # 获取基础表名
    base_table_name = table_name or PG_CONFIG.get("table_name", "document_embeddings")
    
    # 添加llama-index使用的前缀
    actual_table_name = f"data_{base_table_name}"
    
    logger.info(f"基础表名: {base_table_name}")
    logger.info(f"实际表名: {actual_table_name} (llama-index自动添加'data_'前缀)")

    try:
        logger.info(f"正在为表 {actual_table_name} 的 {content_column} 列创建全文索引...")
        
        # 连接数据库
        conn = psycopg2.connect(
            host=PG_CONFIG["host"],
            port=PG_CONFIG["port"],
            user=PG_CONFIG["user"],
            password=PG_CONFIG["password"],
            database=PG_CONFIG["database"]
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 确认表是否存在
        cursor.execute(f"SELECT to_regclass('{actual_table_name}');")
        if not cursor.fetchone()[0]:
            logger.error(f"表 {actual_table_name} 不存在")
            return False

        # 检查列是否存在
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{actual_table_name}' AND column_name = '{content_column}';")
        if not cursor.fetchone():
            logger.error(f"列 {content_column} 在表 {actual_table_name} 中不存在")
            return False

        # 1. 创建全文搜索配置（支持中文）
        try:
            cursor.execute("SELECT cfgname FROM pg_ts_config WHERE cfgname = 'chinese';")
            if not cursor.fetchone():
                logger.info("中文全文搜索配置不存在，尝试创建...")
                try:
                    # 尝试创建中文配置（需要zhparser扩展）
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS zhparser;")
                    cursor.execute("CREATE TEXT SEARCH CONFIGURATION public.chinese (PARSER = zhparser);")
                    cursor.execute("ALTER TEXT SEARCH CONFIGURATION public.chinese ADD MAPPING FOR n,v,a,i,e,l,j WITH simple;")
                    logger.info("成功创建中文全文搜索配置")
                except Exception as e:
                    logger.warning(f"无法创建中文解析器，可能需要安装zhparser扩展: {e}")
                    logger.warning("将使用默认配置，中文检索效果可能受到影响")
        except Exception as e:
            logger.warning(f"检查中文配置时出错: {e}")

        # 2. 确定要使用的文本搜索配置
        try:
            cursor.execute("SELECT cfgname FROM pg_ts_config WHERE cfgname = 'chinese';")
            ts_config = 'public.chinese' if cursor.fetchone() else 'pg_catalog.english'
        except:
            ts_config = 'pg_catalog.english'
            
        logger.info(f"使用{ts_config}文本搜索配置")
        
        # 3. 检查并添加text_search_tsv列（llama-index全文检索需要）
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{actual_table_name}' AND column_name = 'text_search_tsv';")
        if not cursor.fetchone():
            logger.info(f"添加text_search_tsv列到表 {actual_table_name}")
            
            # 添加tsvector列
            cursor.execute(f"ALTER TABLE {actual_table_name} ADD COLUMN text_search_tsv tsvector;")
            
            # 更新现有数据
            logger.info(f"更新现有数据的text_search_tsv值")
            cursor.execute(f"UPDATE {actual_table_name} SET text_search_tsv = to_tsvector('{ts_config}', {content_column});")
            
            # 添加触发器以保持tsvector更新
            trigger_name = f"{actual_table_name}_text_vector_update"
            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {actual_table_name};")
            
            logger.info(f"创建自动更新触发器 {trigger_name}")
            cursor.execute(f"""
            CREATE TRIGGER {trigger_name}
            BEFORE INSERT OR UPDATE ON {actual_table_name}
            FOR EACH ROW
            EXECUTE FUNCTION tsvector_update_trigger(text_search_tsv, '{ts_config}', {content_column});
            """)
            logger.info("触发器创建成功")
        else:
            logger.info("text_search_tsv列已存在，无需创建")
        
        # 4. 创建两种索引
        # 4.1 创建text_search_tsv的GIN索引
        tsv_index_name = f"idx_{actual_table_name}_text_search_tsv"
        cursor.execute(f"DROP INDEX IF EXISTS {tsv_index_name};")
        cursor.execute(f"CREATE INDEX {tsv_index_name} ON {actual_table_name} USING gin(text_search_tsv);")
        logger.info(f"创建text_search_tsv索引 {tsv_index_name} 成功")
        
        # 4.2 创建内容列的全文索引
        content_index_name = f"idx_{actual_table_name}_{content_column}_fulltext"
        cursor.execute(f"DROP INDEX IF EXISTS {content_index_name};")
        cursor.execute(f"CREATE INDEX {content_index_name} ON {actual_table_name} USING gin(to_tsvector('{ts_config}', {content_column}));")
        
        # 5. 确认索引创建成功
        cursor.execute(f"SELECT indexname FROM pg_indexes WHERE tablename = '{actual_table_name}' AND indexname = '{content_index_name}';")
        if cursor.fetchone():
            logger.info(f"全文索引 {content_index_name} 创建成功")
        else:
            logger.error(f"全文索引创建失败")
            return False
        
        cursor.close()
        conn.close()
        
        logger.info("全文索引设置完成")
        return True
        
    except Exception as e:
        logger.error(f"设置全文索引时发生错误: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PostgreSQL全文索引设置工具")
    parser.add_argument("--table", "-t", help="表名(不包含data_前缀，会自动添加)", default=None)
    parser.add_argument("--column", "-c", help="文本内容列名", default="text")
    parser.add_argument("--create", "-r", help="如果表不存在，是否创建表", action="store_true")
    parser.add_argument("--embed-dim", "-d", help="嵌入向量维度", type=int, default=None)
    
    args = parser.parse_args()
    
    # 如果指定了--create，先创建表
    if args.create:
        if create_table_if_not_exists(args.table, args.embed_dim):
            logger.info("表创建或确认成功")
        else:
            logger.error("表创建失败")
            return
    
    # 然后设置全文索引
    if setup_fulltext_index(args.table, args.column):
        logger.info("全文索引设置成功")
    else:
        logger.error("全文索引设置失败")

if __name__ == "__main__":
    main() 