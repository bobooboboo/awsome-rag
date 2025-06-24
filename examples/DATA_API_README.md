# 数据API使用说明

本文档介绍如何使用RAG系统的数据管理API，包括文档上传、删除、查询和批量导入功能。

## API概览

数据API提供以下主要功能：

- **文档上传**: 单个文档上传和批量上传
- **目录导入**: 从指定目录批量导入文档
- **文档管理**: 查询文档列表、获取统计信息
- **文档查看**: 获取文档信息和下载文档
- **文档删除**: 支持按ID或条件删除文档

所有API都遵循RESTful设计，返回统一的JSON格式响应。

## 配置要求

### 环境变量配置

在使用前，请确保正确配置环境变量：

```bash
# 存储配置
PERSIST_DIR=./storage              # 数据持久化目录
UPLOAD_DIR=./storage/uploads       # 文档上传存储目录

# 向量库配置
VECTOR_STORE_TYPE=pg_vector        # 向量存储类型
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DATABASE=ragdb

# 全文搜索配置
FULLTEXT_STORE_TYPE=es             # 全文搜索类型
ES_HOST=localhost
ES_PORT=9200
```

### 支持的文件类型

- 文本文件: `.txt`
- PDF文档: `.pdf`
- Word文档: `.doc`, `.docx`
- 网页文件: `.html`, `.htm`
- Markdown文件: `.md`, `.markdown`
- Excel文件: `.xls`, `.xlsx`
- CSV文件: `.csv`

## API详细说明

### 1. 文档上传

#### 单个文档上传

**接口**: `POST /api/data/upload`

**请求类型**: `multipart/form-data`

**参数**:
- `file`: 文件对象（必需）
- `filename`: 自定义文件名（可选）
- `split_strategy`: 拆分策略（可选，默认: sentence）
  - `sentence`: 按句子拆分
  - `token`: 按token拆分
  - `semantic`: 语义拆分
  - `legal`: 法规拆分
- `chunk_size`: 块大小（可选，默认: 500）
- `chunk_overlap`: 块重叠（可选，默认: 50）
- `metadata`: JSON格式的额外元数据（可选）

**示例**:
```bash
curl -X POST http://localhost:5001/api/data/upload \
  -F "file=@document.pdf" \
  -F "split_strategy=sentence" \
  -F "chunk_size=500" \
  -F "chunk_overlap=50" \
  -F 'metadata={"category": "技术文档", "source": "external"}'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "file_id": "uuid-string",
    "file_name": "document.pdf",
    "document_count": 1,
    "node_count": 15,
    "processing_time": 2.34,
    "metadata": {...}
  },
  "message": "文档上传成功"
}
```

#### 批量文档上传

**接口**: `POST /api/data/batch_upload`

**请求类型**: `multipart/form-data`

**参数**:
- `files`: 多个文件对象（必需）
- 其他参数同单个上传

**示例**:
```bash
curl -X POST http://localhost:5001/api/data/batch_upload \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.txt" \
  -F "split_strategy=sentence" \
  -F 'metadata={"batch": "upload_1"}'
```

### 2. 目录导入

**接口**: `POST /api/data/import`

**请求类型**: `application/json`

**参数**:
```json
{
  "directory_path": "/path/to/documents",    // 目录路径（必需）
  "recursive": true,                         // 是否递归搜索（可选，默认: true）
  "file_pattern": "*.pdf",                  // 文件匹配模式（可选，默认: *）
  "split_strategy": "sentence",             // 拆分策略（可选）
  "chunk_size": 500,                        // 块大小（可选）
  "chunk_overlap": 50,                      // 块重叠（可选）
  "metadata": {                             // 额外元数据（可选）
    "source": "directory_import",
    "category": "technical"
  }
}
```

**示例**:
```bash
curl -X POST http://localhost:5001/api/data/import \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/Users/docs/technical",
    "recursive": true,
    "file_pattern": "*.pdf",
    "metadata": {"category": "technical", "source": "internal"}
  }'
```

### 3. 文档查询

#### 文档列表查询

**接口**: `GET /api/data/list`

**查询参数**:
- `page`: 页码（默认: 1）
- `page_size`: 每页大小（默认: 20）
- `file_name`: 文件名过滤
- `file_id`: 文件ID过滤
- `upload_time_start`: 上传时间开始

**示例**:
```bash
# 查询所有文档
curl "http://localhost:5001/api/data/list?page=1&page_size=10"

# 按文件名过滤
curl "http://localhost:5001/api/data/list?file_name=report"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "file_id": "uuid-string",
        "file_name": "document.pdf",
        "file_path": "/path/to/file",
        "upload_time": "2024-01-01T10:00:00",
        "split_strategy": "sentence",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "node_count": 15
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "message": "查询成功"
}
```

#### 统计信息

**接口**: `GET /api/data/stats`

**示例**:
```bash
curl "http://localhost:5001/api/data/stats"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_files": 100,
    "total_nodes": 5000,
    "storage_size": "1.2GB",
    "file_types": {
      "pdf": 50,
      "docx": 30,
      "txt": 20
    },
    "upload_timeline": "暂未实现"
  },
  "message": "统计信息获取成功"
}
```

### 4. 文档查看

#### 文档信息查询

**接口**: `GET /api/data/document/{file_id}`

**功能**: 获取指定文档的详细信息

**路径参数**:
- `file_id`: 文件唯一标识符

**示例**:
```bash
curl "http://localhost:5001/api/data/document/550e8400-e29b-41d4-a716-446655440000"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "document.pdf",
    "file_size": "1.2MB",
    "file_type": "pdf",
    "upload_time": "2024-01-01T10:00:00",
    "node_count": 15,
    "download_url": "/api/data/download/550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "category": "技术文档",
      "source": "external"
    }
  },
  "message": "文档信息获取成功"
}
```

#### 文档下载

**接口**: `GET /api/data/download/{file_id}`

**功能**: 下载原始文档文件

**路径参数**:
- `file_id`: 文件唯一标识符

**示例**:
```bash
# 直接下载
curl -O -J "http://localhost:5001/api/data/download/550e8400-e29b-41d4-a716-446655440000"

# 或在浏览器中直接访问
http://localhost:5001/api/data/download/550e8400-e29b-41d4-a716-446655440000
```

**响应**:
- **成功时**: 返回文件流，浏览器会自动下载文件
  - `Content-Type`: 根据文件类型设置的MIME类型
  - `Content-Disposition`: attachment; filename="原始文件名"
  - `Content-Length`: 文件大小
- **失败时**: 返回JSON错误信息

### 5. 文档删除

**接口**: `DELETE /api/data/delete`

**请求类型**: `application/json`

**参数**:
```json
{
  "file_ids": ["uuid1", "uuid2"],    // 按文件ID删除（可选）
  "filters": {                       // 按条件删除（可选）
    "file_name": "document.pdf",
    "category": "test"
  },
  "delete_files": true               // 是否同时删除物理文件（可选，默认: false）
}
```

**示例**:
```bash
# 按文件ID删除
curl -X DELETE http://localhost:5001/api/data/delete \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["uuid1", "uuid2"],
    "delete_files": true
  }'

# 按条件删除
curl -X DELETE http://localhost:5001/api/data/delete \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {"category": "test"},
    "delete_files": true
  }'
```

## 文档处理流程

系统的文档处理流程如下：

1. **文件上传**: 将文件保存到配置的存储目录
2. **文档加载**: 使用对应的文档加载器读取文件内容
3. **文档解析**: 解析文档结构和内容
4. **文档拆分**: 根据指定策略将文档拆分为块
5. **元数据添加**: 为每个块添加文件信息和用户元数据
6. **向量化存储**: 将文档块存储到向量数据库
7. **全文索引**: 将文档块索引到全文搜索引擎

## 测试工具

项目提供了完整的测试脚本 `test_data_api.py`，可以测试所有数据API功能：

```bash
python test_data_api.py
```

测试脚本会：
- 测试单个文档上传
- 测试批量文档上传
- 测试目录导入
- 测试文档查询
- 测试统计信息
- 自动清理测试数据

## 错误处理

所有API都会返回统一的错误格式：

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": 400
}
```

常见错误码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 性能优化建议

1. **批量操作**: 对于大量文件，优先使用批量上传或目录导入
2. **合理分块**: 根据文档类型选择合适的分块策略和大小
3. **元数据设计**: 合理设计元数据结构，便于后续查询和过滤
4. **存储清理**: 定期清理不需要的文档以节省存储空间

## 集成示例

### Python集成示例

```python
import requests
import json

# 上传文档
def upload_document(file_path, metadata=None):
    url = "http://localhost:5001/api/data/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'split_strategy': 'sentence',
            'chunk_size': '500',
            'metadata': json.dumps(metadata or {})
        }
        response = requests.post(url, files=files, data=data)
    
    return response.json()

# 查询文档
def list_documents(page=1, page_size=20, filters=None):
    url = "http://localhost:5001/api/data/list"
    params = {'page': page, 'page_size': page_size}
    
    if filters:
        params.update(filters)
    
    response = requests.get(url, params=params)
    return response.json()

# 获取文档信息
def get_document_info(file_id):
    url = f"http://localhost:5001/api/data/document/{file_id}"
    response = requests.get(url)
    return response.json()

# 下载文档
def download_document(file_id, save_path=None):
    url = f"http://localhost:5001/api/data/download/{file_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        # 从响应头获取文件名
        content_disposition = response.headers.get('Content-Disposition', '')
        filename = 'downloaded_file'
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        
        # 保存文件
        save_path = save_path or filename
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return {"success": True, "saved_path": save_path}
    else:
        return response.json()

# 删除文档
def delete_documents(file_ids, delete_files=True):
    url = "http://localhost:5001/api/data/delete"
    data = {
        'file_ids': file_ids,
        'delete_files': delete_files
    }
    
    response = requests.delete(url, json=data)
    return response.json()
```

### JavaScript/Node.js集成示例

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

// 上传文档
async function uploadDocument(filePath, metadata = {}) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('split_strategy', 'sentence');
  form.append('chunk_size', '500');
  form.append('metadata', JSON.stringify(metadata));

  try {
    const response = await axios.post(
      'http://localhost:5001/api/data/upload',
      form,
      { headers: form.getHeaders() }
    );
    return response.data;
  } catch (error) {
    console.error('Upload failed:', error.response?.data || error.message);
    throw error;
  }
}

// 查询文档列表
async function listDocuments(page = 1, pageSize = 20) {
  try {
    const response = await axios.get('http://localhost:5001/api/data/list', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  } catch (error) {
    console.error('List failed:', error.response?.data || error.message);
    throw error;
  }
}

// 获取文档信息
async function getDocumentInfo(fileId) {
  try {
    const response = await axios.get(`http://localhost:5001/api/data/document/${fileId}`);
    return response.data;
  } catch (error) {
    console.error('Get document info failed:', error.response?.data || error.message);
    throw error;
  }
}

// 下载文档
async function downloadDocument(fileId, savePath) {
  try {
    const response = await axios.get(`http://localhost:5001/api/data/download/${fileId}`, {
      responseType: 'stream'
    });
    
    // 在Node.js环境中保存文件
    if (savePath) {
      const writer = fs.createWriteStream(savePath);
      response.data.pipe(writer);
      
      return new Promise((resolve, reject) => {
        writer.on('finish', () => resolve({ success: true, saved_path: savePath }));
        writer.on('error', reject);
      });
    }
    
    return response.data;
  } catch (error) {
    console.error('Download failed:', error.response?.data || error.message);
    throw error;
  }
}
```

## 注意事项

1. **文件大小限制**: 根据服务器配置，可能存在单文件大小限制
2. **并发上传**: 避免同时上传过多文件，以免影响系统性能
3. **元数据一致性**: 保持元数据字段的一致性，便于后续查询
4. **备份策略**: 重要文档建议在删除前进行备份
5. **权限控制**: 在生产环境中应添加适当的权限控制机制 