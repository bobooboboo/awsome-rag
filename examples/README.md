# 向量检索示例

本目录包含多种检索方式的示例代码，用于演示系统中实现的向量检索、全文检索和混合检索功能。

## 主要示例文件

1. **pg_search_example.py** - PostgreSQL向量库的基本检索示例
   - 演示如何使用向量检索、全文检索和混合检索
   - 包含添加示例数据、执行查询并清理数据的完整流程

2. **pg_fulltext_setup.py** - PostgreSQL全文索引设置工具
   - 用于创建和优化PostgreSQL的全文检索功能
   - 支持中文全文检索（如果安装了zhparser扩展）
   - 自动处理llama-index添加的"data_"表名前缀

3. **search_comparison.py** - 检索方式对比测试
   - 使用多种测试数据和查询场景
   - 对比不同检索方式在各种场景下的效果
   - 生成详细的对比报告和性能分析

## 环境准备

在运行示例之前，请确保：

1. PostgreSQL数据库已正确配置（参见`app/config/config.py`中的`PG_CONFIG`）
2. PostgreSQL已安装pgvector扩展（用于向量操作）
3. 建议安装zhparser扩展以支持中文全文搜索（非必须）

### pgvector安装

```bash
# 在PostgreSQL服务器上执行
sudo apt-get install postgresql-server-dev-14  # Ubuntu/Debian，根据你的PostgreSQL版本调整
# 或
sudo dnf install postgresql-devel               # Fedora
# 或
sudo yum install postgresql-devel               # CentOS/RHEL

git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install

# 在PostgreSQL中启用扩展
psql -U postgres -d your_database -c "CREATE EXTENSION vector;"
```

### zhparser中文分词扩展安装

zhparser是PostgreSQL的中文分词扩展，用于支持高质量的中文全文检索。安装步骤：

#### Ubuntu/Debian系统:

```bash
# 1. 安装SCWS依赖
sudo apt-get install libscws-dev

# 2. 安装zhparser
git clone https://github.com/amutu/zhparser.git
cd zhparser
make && make install

# 3. 在PostgreSQL中配置
psql -U postgres -d your_database -c "CREATE EXTENSION zhparser;"
psql -U postgres -d your_database -c "CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);"
psql -U postgres -d your_database -c "ALTER TEXT SEARCH CONFIGURATION chinese ADD MAPPING FOR n,v,a,i,e,l,j WITH simple;"
```

#### CentOS/RHEL系统:

```bash
# 1. 安装开发工具和依赖
sudo yum groupinstall "Development Tools"
sudo yum install postgresql-devel

# 2. 安装SCWS
wget http://www.xunsearch.com/scws/down/scws-1.2.3.tar.bz2
tar xvf scws-1.2.3.tar.bz2
cd scws-1.2.3
./configure
make
sudo make install

# 3. 安装zhparser
git clone https://github.com/amutu/zhparser.git
cd zhparser
# 确保系统能找到SCWS库
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
make && sudo make install

# 4. 在PostgreSQL中配置
psql -U postgres -d your_database -c "CREATE EXTENSION zhparser;"
psql -U postgres -d your_database -c "CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);"
psql -U postgres -d your_database -c "ALTER TEXT SEARCH CONFIGURATION chinese ADD MAPPING FOR n,v,a,i,e,l,j WITH simple;"
```

#### Fedora系统:

```bash
# 1. 安装开发工具和依赖
sudo dnf install postgresql-devel gcc make wget

# 2. 安装SCWS
wget http://www.xunsearch.com/scws/down/scws-1.2.3.tar.bz2
tar xvf scws-1.2.3.tar.bz2
cd scws-1.2.3
./configure
make
sudo make install

# 3. 安装zhparser
git clone https://github.com/amutu/zhparser.git
cd zhparser
make && sudo make install

# 4. 在PostgreSQL中配置
psql -U postgres -d your_database -c "CREATE EXTENSION zhparser;"
psql -U postgres -d your_database -c "CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);"
psql -U postgres -d your_database -c "ALTER TEXT SEARCH CONFIGURATION chinese ADD MAPPING FOR n,v,a,i,e,l,j WITH simple;"
```

#### macOS系统:

```bash
# 1. 安装SCWS依赖
brew install scws

# 2. 安装zhparser
git clone https://github.com/amutu/zhparser.git
cd zhparser
# 可能需要设置SCWS路径
export SCWS_HOME=/usr/local/Cellar/scws/1.2.3  # 根据实际安装路径调整
make && make install

# 3. 在PostgreSQL中配置
psql -U postgres -d your_database -c "CREATE EXTENSION zhparser;"
psql -U postgres -d your_database -c "CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);"
psql -U postgres -d your_database -c "ALTER TEXT SEARCH CONFIGURATION chinese ADD MAPPING FOR n,v,a,i,e,l,j WITH simple;"
```

**注意**: 
- 如果无法安装zhparser，全文检索将退回使用英文分词器，对中文检索效果会有影响。
- 在某些系统上，可能需要将PostgreSQL服务器重启以识别新安装的扩展。
- 安装zhparser后，pg_fulltext_setup.py会自动识别并使用它。

## 表名前缀说明

**重要**：llama-index在使用PostgreSQL时会自动在表名前添加"data_"前缀。例如：

- 如果在`config.py`中配置的表名是`document_embeddings`
- 实际在PostgreSQL中创建的表名将是`data_document_embeddings`

`pg_fulltext_setup.py`工具已经针对这种情况进行了适配，会自动添加前缀。

## 运行示例

首先，建议设置全文索引以优化全文检索性能：

```bash
python examples/pg_fulltext_setup.py
```

然后，可以运行基本示例：

```bash
python examples/pg_search_example.py
```

要进行详细的检索方式对比测试：

```bash
python examples/search_comparison.py
```

## 自定义测试

您可以修改示例文件中的测试数据和查询，以评估系统在特定场景下的表现。例如，在`search_comparison.py`中修改`TEST_DOCS`和`TEST_QUERIES`变量，可以测试系统对特定领域文档的检索效果。

## 注意事项

- 这些示例会在运行后自动清理测试数据，不会影响数据库中的其他数据
- 全文检索的效果受到数据库全文索引配置的影响
- 混合检索的alpha参数控制向量检索和关键词检索的权重比例，0.0完全使用关键词检索，1.0完全使用向量检索 