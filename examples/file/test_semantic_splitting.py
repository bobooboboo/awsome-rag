from llama_index.core import Document
from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter

from app.data_indexing.file.document_loader.local_file import LocalFileLoader
from app.data_indexing.file.document_splitter.document_splitter_factory import DocumentSplitterFactory

if __name__ == '__main__':
    # 加载长文本测试文件
    file_path = "/Users/boboo/awsome_rag/awsome-rag/test_semantic_long.txt"
    documents = LocalFileLoader().load_documents(file_path)
    
    print("=" * 60)
    print("语义拆分效果测试 - 长文本")
    print("=" * 60)
    
    # 文档信息
    print(f"\n📄 原文档信息:")
    for i, doc in enumerate(documents):
        print(f"  文档 {i+1}: {len(doc.text)} 字符")
        print(f"  前200字符: {doc.text[:200]}...")
    
    # 测试不同的语义拆分配置
    configs = [
        {"name": "保守配置", "threshold": 95, "buffer": 1},
        {"name": "当前配置", "threshold": 90, "buffer": 2}, 
        {"name": "适中配置", "threshold": 80, "buffer": 1},
        {"name": "敏感配置", "threshold": 70, "buffer": 1},
        {"name": "极敏感配置", "threshold": 60, "buffer": 1}
    ]
    
    print(f"\n🔍 语义拆分测试:")
    for config in configs:
        print(f"\n--- {config['name']} (阈值: {config['threshold']}%, 缓冲: {config['buffer']}) ---")
        
        # 使用工厂方法创建语义拆分器，但我们需要手动设置参数
        from app.model.embedding_model import get_embedding_model
        splitter = SemanticSplitterNodeParser(
            breakpoint_percentile_threshold=config['threshold'],
            buffer_size=config['buffer'],
            embed_model=get_embedding_model()
        )
        
        nodes = splitter.get_nodes_from_documents(documents)
        print(f"  📊 节点数量: {len(nodes)}")
        
        for j, node in enumerate(nodes):
            # 获取节点的前50个字符作为预览
            preview = node.text.replace('\n', ' ').strip()[:80]
            print(f"    节点 {j+1}: {len(node.text)} 字符 - \"{preview}...\"")
    
    # 对比句子拆分效果
    print(f"\n📝 句子拆分对比:")
    sentence_configs = [
        {"name": "小块拆分", "chunk_size": 200, "overlap": 50},
        {"name": "中块拆分", "chunk_size": 400, "overlap": 80},
        {"name": "大块拆分", "chunk_size": 800, "overlap": 100}
    ]
    
    for config in sentence_configs:
        print(f"\n--- {config['name']} (块大小: {config['chunk_size']}, 重叠: {config['overlap']}) ---")
        splitter = SentenceSplitter(
            chunk_size=config['chunk_size'], 
            chunk_overlap=config['overlap']
        )
        nodes = splitter.get_nodes_from_documents(documents)
        print(f"  📊 节点数量: {len(nodes)}")
        
        for j, node in enumerate(nodes):
            preview = node.text.replace('\n', ' ').strip()[:80]
            print(f"    节点 {j+1}: {len(node.text)} 字符 - \"{preview}...\"")
    
    print(f"\n✅ 测试完成！")
    print(f"📝 总结:")
    print(f"  - 语义拆分会根据内容的语义相似度自动决定拆分点")
    print(f"  - 阈值越低，拆分越细粒度") 
    print(f"  - 句子拆分按固定大小拆分，不考虑语义连贯性")
    print(f"  - 建议根据实际应用场景选择合适的拆分策略") 