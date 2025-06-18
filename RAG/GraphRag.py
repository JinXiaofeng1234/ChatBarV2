import numpy as np
import requests
import json
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Entity:
    """实体类"""
    name: str
    description: str = ""
    embedding: Optional[np.ndarray] = None


@dataclass
class Triple:
    """三元组：(主体, 关系, 客体)"""
    subject: str
    relation: str
    object: str


class OllamaEmbeddings:
    """使用Ollama的bge-m3模型进行文本编码"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "bge-m3"

    def embed_text(self, text: str) -> np.ndarray:
        """对单个文本进行编码"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            embedding = response.json()["embedding"]
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            print(f"编码错误: {e}")
            # 返回随机向量作为后备方案
            return np.random.randn(1024).astype(np.float32)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """对多个文本进行编码"""
        embeddings = []
        for i, text in enumerate(texts):
            print(f"正在编码第 {i + 1}/{len(texts)} 个文本...")
            embedding = self.embed_text(text)
            embeddings.append(embedding)

        # 确保返回的是2D数组 (n_samples, n_features)
        if len(embeddings) == 1:
            return embeddings[0].reshape(1, -1)
        else:
            return np.stack(embeddings)  # 使用 stack 而不是 array


class GraphRAG:
    """基于手动定义关系的Graph RAG系统"""

    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.embeddings = OllamaEmbeddings(ollama_base_url)

        # 知识图谱：实体 -> [(关系, 目标实体), ...]
        self.knowledge_graph: Dict[str, List[Tuple[str, str]]] = {}

        # 实体信息
        self.entities: Dict[str, Entity] = {}

        # 文档库
        self.documents: List[str] = []
        self.doc_embeddings: Optional[np.ndarray] = None

    def add_entity(self, name: str, description: str = ""):
        """添加实体"""
        if name not in self.entities:
            entity = Entity(name=name, description=description)
            # 生成实体的embedding
            entity_text = f"{name} {description}".strip()
            entity.embedding = self.embeddings.embed_text(entity_text)
            self.entities[name] = entity
            self.knowledge_graph[name] = []
            print(f"添加实体: {name}")

    def add_relation(self, subject: str, relation: str, obj: str):
        """添加关系"""
        # 确保主体和客体都存在
        if subject not in self.entities:
            self.add_entity(subject)
        if obj not in self.entities:
            self.add_entity(obj)

        # 添加关系
        if (relation, obj) not in self.knowledge_graph[subject]:
            self.knowledge_graph[subject].append((relation, obj))
            print(f"添加关系: {subject} -[{relation}]-> {obj}")

    def add_document(self, text: str):
        """添加文档"""
        self.documents.append(text)
        print(f"添加文档: {text[:50]}...")

    def build_document_embeddings(self):
        """构建文档embeddings"""
        if self.documents:
            print("正在构建文档embeddings...")
            self.doc_embeddings = self.embeddings.embed_text(self.documents)
            print("文档embeddings构建完成")

    def find_similar_entities(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """找到与查询最相似的实体"""
        if not self.entities:
            return []

        query_embedding = self.embeddings.embed_text(query)

        similarities = []
        entity_names = []

        for name, entity in self.entities.items():
            if entity.embedding is not None:
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    entity.embedding.reshape(1, -1)
                )[0, 0]
                similarities.append(similarity)
                entity_names.append(name)

        # 按相似度排序
        if similarities:
            sorted_indices = np.argsort(similarities)[::-1]
            similar_entities = [(entity_names[i], similarities[i])
                                for i in sorted_indices[:top_k]]
            return similar_entities
        return []

    def find_similar_documents(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """找到与查询最相似的文档"""
        if not self.documents or self.doc_embeddings is None:
            return [(doc, 0.0) for doc in self.documents[:top_k]]

        query_embedding = self.embeddings.embed_text(query)

        # 调试输出
        print(f"Query embedding shape: {query_embedding.shape}")
        print(f"Doc embeddings shape: {self.doc_embeddings.shape}")

        # 强制重新构造为正确的形状
        query_embedding = query_embedding.reshape(1, -1)

        # 如果 doc_embeddings 是 1D，说明只有一个文档，需要 reshape
        if self.doc_embeddings.ndim == 1:
            doc_embeddings = self.doc_embeddings.reshape(1, -1)
        else:
            doc_embeddings = self.doc_embeddings

        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]

        sorted_indices = np.argsort(similarities)[::-1]
        similar_docs = [(self.documents[i], similarities[i])
                        for i in sorted_indices[:top_k]]
        return similar_docs

    def retrieve_subgraph(self, entities: List[str], max_hops: int = 1) -> List[Triple]:
        """检索实体相关的子图"""
        visited = set()
        current_entities = set(entities)
        all_triples = []

        for hop in range(max_hops + 1):
            next_entities = set()

            for entity in current_entities:
                if entity in visited or entity not in self.knowledge_graph:
                    continue

                visited.add(entity)

                # 获取该实体的所有关系
                for relation, target in self.knowledge_graph[entity]:
                    triple = Triple(subject=entity, relation=relation, object=target)
                    all_triples.append(triple)
                    next_entities.add(target)

            current_entities = next_entities

        return all_triples

    def query(self, question: str, top_k_entities: int = 5, top_k_docs: int = 3, max_hops: int = 1) -> str:
        """执行Graph RAG查询"""
        print(f"\n查询: {question}")
        print("=" * 50)

        # 1. 找到相似实体
        similar_entities = self.find_similar_entities(question, top_k_entities)
        print(f"找到 {len(similar_entities)} 个相似实体")

        # 2. 检索子图
        entity_names = [name for name, score in similar_entities]
        triples = self.retrieve_subgraph(entity_names, max_hops)
        print(f"检索到 {len(triples)} 个三元组")

        # 3. 找到相似文档
        similar_docs = self.find_similar_documents(question, top_k_docs)
        print(f"找到 {len(similar_docs)} 个相似文档")

        # 4. 构建上下文
        context = self._build_context(similar_entities, triples, similar_docs)

        # 5. 生成答案
        # answer = self._generate_answer(question, context)

        return context

    def _build_context(self, entities: List[Tuple[str, float]],
                       triples: List[Triple],
                       documents: List[Tuple[str, float]]) -> str:
        """构建查询上下文"""
        context_parts = []

        # 相关实体
        if entities:
            entity_info = "相关实体 (按相似度排序):\n"
            for name, score in entities:
                entity = self.entities.get(name)
                desc = entity.description if entity else ""
                entity_info += f"- {name} (相似度: {score:.3f}): {desc}\n"
            context_parts.append(entity_info)

        # 知识图谱三元组
        if triples:
            graph_info = "知识图谱信息:\n"
            for triple in triples:
                graph_info += f"- {triple.subject} -[{triple.relation}]-> {triple.object}\n"
            context_parts.append(graph_info)

        # 相关文档
        if documents:
            doc_info = "相关文档 (按相似度排序):\n"
            for i, (doc, score) in enumerate(documents, 1):
                doc_info += f"{i}. (相似度: {score:.3f}) {doc}\n"
            context_parts.append(doc_info)

        return "\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """生成答案"""
        try:
            prompt = f"""基于以下知识图谱和文档信息回答问题:

{context}

问题: {question}

请根据以上信息提供准确、详细的答案。如果信息不足以回答问题，请说明。
答案:"""

            response = requests.post(
                f"{self.embeddings.base_url}/api/generate",
                json={
                    "model": "qwen:7b",  # 使用生成模型
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                return self._fallback_answer(context)

        except Exception as e:
            print(f"生成答案时出错: {e}")
            return self._fallback_answer(context)

    def _fallback_answer(self, context: str) -> str:
        """后备答案"""
        return f"基于检索到的信息:\n\n{context}\n\n请根据以上知识图谱和文档信息进行分析。"


# 使用示例
def main():
    # 初始化Graph RAG系统
    graph_rag = GraphRAG()

    print("正在构建知识图谱...")

    # 添加实体和关系 (手动定义)

    # 添加公司实体
    graph_rag.add_entity("苹果公司", "美国的科技巨头，专注于消费电子产品")
    graph_rag.add_entity("微软", "美国的软件公司，Windows和Office的开发者")
    graph_rag.add_entity("谷歌", "美国的搜索引擎和云计算公司")

    # 添加人物实体
    graph_rag.add_entity("蒂姆·库克", "苹果公司的CEO")
    # graph_rag.add_entity("萨提亚·纳德拉", "微软的CEO")
    # graph_rag.add_entity("桑达尔·皮查伊", "谷歌的CEO")

    # 添加产品实体
    graph_rag.add_entity("iPhone", "苹果公司的智能手机产品")
#     graph_rag.add_entity("Windows", "微软的操作系统")
#     graph_rag.add_entity("Android", "谷歌的移动操作系统")

    # 添加关系
    graph_rag.add_relation("蒂姆·库克", "CEO_OF", "苹果公司")
#     graph_rag.add_relation("萨提亚·纳德拉", "CEO_OF", "微软")
    # graph_rag.add_relation("桑达尔·皮查伊", "CEO_OF", "谷歌")

    graph_rag.add_relation("苹果公司", "PRODUCES", "iPhone")
    # graph_rag.add_relation("微软", "PRODUCES", "Windows")
    # graph_rag.add_relation("谷歌", "PRODUCES", "Android")

    graph_rag.add_relation("iPhone", "RELEASED", "2007")
    # graph_rag.add_relation("苹果公司", "FOUNDED", "1976")
    # graph_rag.add_relation("微软", "FOUNDED", "1975")

    # 添加文档
    documents = [
        "苹果公司是一家美国跨国科技公司，总部位于加利福尼亚州库比蒂诺。",
        "蒂姆·库克自2011年起担任苹果公司CEO，接替史蒂夫·乔布斯。",
        "iPhone是苹果公司开发的智能手机系列，首款iPhone于2007年发布。",
        "微软是全球最大的软件公司之一，以Windows操作系统闻名。",
        "谷歌是全球最大的搜索引擎公司，同时也开发了Android操作系统。"
    ]

    for doc in documents:
        graph_rag.add_document(doc)

    # 构建文档embeddings
    graph_rag.build_document_embeddings()

    print(f"\n知识图谱构建完成！")
    print(f"实体数量: {len(graph_rag.entities)}")
    print(f"文档数量: {len(graph_rag.documents)}")

    # 查询示例
    questions = [
        "苹果公司的CEO是谁？",
        "iPhone是什么时候发布的？",
        "哪些公司生产操作系统？",
        "蒂姆·库克的工作是什么？"
    ]

    for question in questions:
        answer = graph_rag.query(question)
        print(f"\n问题: {question}")
        print(f"答案: {answer}")
        print("-" * 80)


if __name__ == "__main__":
    main()
