"""
RAG检索增强生成模块
使用ChromaDB向量数据库实现佛学知识库检索
使用本地BAAI/bge-small-zh模型进行embedding
"""
import os
import json
from typing import List, Tuple

# 设置HuggingFace使用离线模式，避免SSL问题
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME, CHROMA_DATA_DIR

# 使用本地中文embedding模型
embedding_model = None

def get_embedding_model():
    """获取单例embedding模型"""
    global embedding_model
    if embedding_model is None:
        print(f"正在加载embedding模型: {EMBEDDING_MODEL_NAME}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print(f"模型加载完成，维度: {embedding_model.get_embedding_dimension()}")
    return embedding_model

class FoRAG:
    def __init__(self, collection_name: str = "fo_knowledge"):
        """初始化RAG系统"""
        self.collection_name = collection_name
        from chromadb import PersistentClient
        self.client = PersistentClient(path=CHROMA_DATA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "佛学知识库"}
        )
        self._embedding_model = None

    def _get_embedding(self, text: str) -> List[float]:
        """使用本地模型获取文本embedding"""
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        embedding = self._embedding_model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def _get_embedding_dim(self) -> int:
        """获取embedding维度"""
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        return self._embedding_model.get_embedding_dimension()

    def add_documents(self, documents: List[dict], batch_size: int = 100):
        """
        添加文档到知识库
        documents: [{"content": "文本内容", "source": "出处", "category": "类别"}]
        """
        texts = [doc["content"] for doc in documents]
        ids = [f"doc_{i}" for i in range(len(documents))]
        metadatas = [{"source": doc.get("source", ""), "category": doc.get("category", "")} for doc in documents]

        # 批量获取embeddings
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                emb = self._get_embedding(text)
                embeddings.append(emb)

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )
        print(f"已添加 {len(documents)} 篇文档到知识库")

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """
        检索相关文档
        返回: [(content, source, score), ...]
        """
        query_embedding = self._get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        retrieved = []
        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                source = results["metadatas"][0][i]["source"]
                distance = results["distances"][0][i]
                # 将distance转换为相似度分数（0-1，越高越相似）
                score = 1 - distance / 2
                retrieved.append((doc, source, score))

        return retrieved

    def build_context(self, query: str, top_k: int = 3) -> str:
        """
        根据查询构建增强上下文
        """
        docs = self.retrieve(query, top_k)

        if not docs:
            return ""

        context_parts = ["【知识库检索结果】"]
        for i, (content, source, score) in enumerate(docs, 1):
            context_parts.append(f"\n参考{i} [{source}] (相关度:{score:.2f}):\n{content}")

        return "\n".join(context_parts)

    def get_collection_count(self) -> int:
        """获取知识库文档数量"""
        return self.collection.count()

    def clear(self):
        """清空知识库"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "佛学知识库"}
        )
        print("知识库已清空")

    def load_documents_from_file(self, filepath: str):
        """从JSON文件加载文档"""
        if not os.path.exists(filepath):
            print(f"文件不存在: {filepath}")
            return

        with open(filepath, "r", encoding="utf-8") as f:
            documents = json.load(f)

        if isinstance(documents, list):
            self.add_documents(documents)
        else:
            print("文档格式错误，应为列表")

    def rebuild_index(self, documents: List[dict]):
        """重建索引"""
        self.clear()
        self.add_documents(documents)


# 全局RAG实例
_rag_instance = None

def get_rag() -> FoRAG:
    """获取RAG单例"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = FoRAG()
    return _rag_instance
