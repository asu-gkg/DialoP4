import os
import json
import dspy
import uuid
from pathlib import Path
import faiss
import numpy as np
from typing import List, Dict, Any, Tuple
from .base_agent import BaseAgent

class Document:
    """表示知识库中的文档"""
    
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}
        self.id = metadata.get('id', str(uuid.uuid4()))

class RAGResult:
    """表示RAG检索结果"""
    
    def __init__(self, query: str, documents: List[Document], context: str = None):
        self.query = query
        self.documents = documents
        self.context = context or self._build_context(documents)
    
    def _build_context(self, documents: List[Document]) -> str:
        """从检索到的文档构建上下文字符串"""
        context = "以下是与查询相关的信息：\n\n"
        
        for i, doc in enumerate(documents):
            context += f"文档[{i+1}]: {doc.content}\n\n"
            # 添加元数据（如果有）
            if doc.metadata and len(doc.metadata) > 0:
                context += f"元数据: {json.dumps(doc.metadata, ensure_ascii=False)}\n\n"
        
        return context

class EnhancedQueryGenerator(dspy.Signature):
    """生成增强的查询"""
    original_query = dspy.InputField(desc="用户原始查询")
    paper_context = dspy.InputField(desc="论文相关上下文信息")
    enhanced_queries = dspy.OutputField(desc="增强后的查询列表，每个查询侧重不同方面")

class RelevanceAnalyzer(dspy.Signature):
    """分析检索结果的相关性和可靠性"""
    query = dspy.InputField(desc="查询")
    context = dspy.InputField(desc="检索到的上下文")
    relevance_analysis = dspy.OutputField(desc="每个检索结果的相关性分析")
    reliability_score = dspy.OutputField(desc="上下文整体可靠性评分(0-10)")

class KnowledgeIntegrator(dspy.Signature):
    """将检索到的知识与当前任务集成"""
    query = dspy.InputField(desc="原始查询")
    context = dspy.InputField(desc="检索到的上下文")
    integrated_knowledge = dspy.OutputField(desc="整合后的知识，组织良好并与当前任务相关")

class RAGEngine(BaseAgent):
    """检索增强生成引擎，提供专业领域知识支持"""
    
    def __init__(self, config):
        super().__init__(config, name="rag_engine")
        
        # 获取RAG特定配置
        self.chunk_size = int(self.config['agents'].get('rag_engine', {}).get('chunk_size', 1000))
        self.chunk_overlap = int(self.config['agents'].get('rag_engine', {}).get('chunk_overlap', 200))
        
        # 初始化向量存储
        self._init_vector_store()
        
        # 初始化DSPy模块
        self.query_generator = dspy.Predict(EnhancedQueryGenerator)
        self.relevance_analyzer = dspy.Predict(RelevanceAnalyzer)
        self.knowledge_integrator = dspy.Predict(KnowledgeIntegrator)
    
    def _load_prompts(self):
        """加载Agent特定的提示模板"""
        self.prompts = {
            "enhance_query": """
你是一位专业的网络研究助手。你需要根据用户的原始查询和论文上下文，生成更加详细和多角度的查询。
这些查询将用于从知识库中检索相关信息。
生成的查询应该:
1. 更具体，包含专业术语
2. 从不同角度探索问题
3. 考虑网络研究中常见的技术和方法
            """,
            "analyze_relevance": """
分析以下检索结果与查询的相关性。
对每个检索结果评估:
1. 内容相关性 - 信息与查询的直接相关程度
2. 可靠性 - 信息的准确性和权威性
3. 时效性 - 信息是否最新
4. 专业性 - 技术内容的深度和广度

最后给出整体可靠性评分(0-10分)。
            """,
            "integrate_knowledge": """
将检索到的知识与当前查询进行整合。你的任务是:
1. 去除冗余信息
2. 组织知识使其连贯
3. 确保整合后的知识直接回应查询
4. 突出与网络研究相关的核心概念和技术细节
5. 添加必要的上下文以确保清晰度
            """
        }
    
    def _init_vector_store(self):
        """初始化向量存储"""
        # 向量维度 (OpenAI embedding model)
        self.vector_dim = 1536
        
        # 创建一个空的FAISS索引
        self.index = faiss.IndexFlatL2(self.vector_dim)
        
        # 存储文档内容和元数据
        self.documents = []
        
        # 加载现有知识库（如果存在）
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """加载现有知识库"""
        kb_path = Path(self.config['storage']['vector_db_path'])
        index_path = kb_path / "index.faiss"
        docs_path = kb_path / "documents.json"
        
        if index_path.exists() and docs_path.exists():
            try:
                # 加载FAISS索引
                self.index = faiss.read_index(str(index_path))
                
                # 加载文档
                with open(docs_path, 'r', encoding='utf-8') as f:
                    docs_data = json.load(f)
                
                # 重建文档对象
                self.documents = [
                    Document(doc['content'], doc['metadata'])
                    for doc in docs_data
                ]
                
                print(f"已加载知识库，包含 {len(self.documents)} 个文档")
            except Exception as e:
                print(f"加载知识库时出错: {e}")
                # 初始化一个新的知识库
                self.index = faiss.IndexFlatL2(self.vector_dim)
                self.documents = []
    
    def _save_knowledge_base(self):
        """保存知识库"""
        kb_path = Path(self.config['storage']['vector_db_path'])
        kb_path.mkdir(parents=True, exist_ok=True)
        
        index_path = kb_path / "index.faiss"
        docs_path = kb_path / "documents.json"
        
        # 保存FAISS索引
        faiss.write_index(self.index, str(index_path))
        
        # 保存文档
        docs_data = [
            {
                'content': doc.content,
                'metadata': doc.metadata
            }
            for doc in self.documents
        ]
        
        with open(docs_path, 'w', encoding='utf-8') as f:
            json.dump(docs_data, f, ensure_ascii=False, indent=2)
    
    def add_document(self, content: str, metadata: Dict[str, Any] = None):
        """
        添加文档到知识库
        
        Args:
            content (str): 文档内容
            metadata (dict, optional): 文档元数据
        """
        # 创建文档对象
        doc = Document(content, metadata)
        
        # 获取嵌入
        embedding = self._get_embedding(content)
        
        # 添加到索引
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # 存储文档
        self.documents.append(doc)
        
        # 保存知识库
        self._save_knowledge_base()
        
        return doc.id
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        获取文本的嵌入向量
        
        Args:
            text (str): 输入文本
            
        Returns:
            np.ndarray: 嵌入向量
        """
        # 这里使用OpenAI的嵌入模型
        # 注意：实际实现中应使用真实的API调用
        # 为简化演示，这里使用随机向量
        # TODO: 实现真实的嵌入调用
        
        # 当需要实现真实的API调用时，应该考虑BASE_URL配置:
        # from langchain_openai import OpenAIEmbeddings
        # api_key = self.config['api']['openai_api_key']
        # base_url = self.config['api'].get('base_url', '')
        # model_name = self.config['models']['embedding_model']
        # 
        # # 配置OpenAI嵌入模型，支持BASE_URL
        # if base_url:
        #     embeddings = OpenAIEmbeddings(
        #         model=model_name,
        #         openai_api_key=api_key,
        #         openai_api_base=base_url
        #     )
        # else:
        #     embeddings = OpenAIEmbeddings(
        #         model=model_name,
        #         openai_api_key=api_key
        #     )
        # 
        # embedding_vector = embeddings.embed_query(text)
        # return np.array(embedding_vector, dtype=np.float32)
        
        # 目前使用随机向量
        return np.random.random(self.vector_dim).astype(np.float32)
    
    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        搜索相关文档
        
        Args:
            query (str): 查询文本
            top_k (int): 返回的最大文档数
            
        Returns:
            List[Document]: 检索到的文档列表
        """
        if len(self.documents) == 0:
            return []
        
        # 获取查询的嵌入
        query_embedding = self._get_embedding(query)
        
        # 搜索最相似的向量
        top_k = min(top_k, len(self.documents))
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32), 
            top_k
        )
        
        # 返回检索到的文档
        results = [self.documents[idx] for idx in indices[0]]
        return results
    
    def add_paper_to_knowledge_base(self, paper_analysis, conversation_id=''):
        """
        将论文分析结果添加到知识库
        
        Args:
            paper_analysis (dict): 论文分析结果
            conversation_id (str): 会话ID
            
        Returns:
            list: 添加的文档ID列表
        """
        document_ids = []
        
        # 提取标题和作者
        title = paper_analysis.get('title', '')
        authors = paper_analysis.get('authors', [])
        
        # 基本元数据
        base_metadata = {
            'title': title,
            'authors': authors,
            'source_type': 'paper_analysis',
            'conversation_id': conversation_id
        }
        
        # 添加摘要
        summary = paper_analysis.get('summary', '')
        if summary:
            doc_id = self.add_document(
                content=f"论文摘要: {summary}",
                metadata={**base_metadata, 'content_type': 'summary'}
            )
            document_ids.append(doc_id)
        
        # 添加关键概念
        concepts = paper_analysis.get('analysis', {}).get('concepts', {})
        if concepts:
            # 关键概念
            key_concepts = concepts.get('key_concepts', '')
            if key_concepts:
                doc_id = self.add_document(
                    content=f"论文关键概念: {key_concepts}",
                    metadata={**base_metadata, 'content_type': 'key_concepts'}
                )
                document_ids.append(doc_id)
            
            # 创新点
            innovations = concepts.get('innovations', '')
            if innovations:
                doc_id = self.add_document(
                    content=f"论文创新点: {innovations}",
                    metadata={**base_metadata, 'content_type': 'innovations'}
                )
                document_ids.append(doc_id)
            
            # 技术细节
            technical_details = concepts.get('technical_details', '')
            if technical_details:
                doc_id = self.add_document(
                    content=f"论文技术细节: {technical_details}",
                    metadata={**base_metadata, 'content_type': 'technical_details'}
                )
                document_ids.append(doc_id)
        
        # 添加架构信息
        architecture = paper_analysis.get('analysis', {}).get('architecture', {})
        if architecture:
            # 系统架构
            arch_overview = architecture.get('overview', '')
            if arch_overview:
                doc_id = self.add_document(
                    content=f"系统架构: {arch_overview}",
                    metadata={**base_metadata, 'content_type': 'architecture_overview'}
                )
                document_ids.append(doc_id)
            
            # 数据流
            data_flow = architecture.get('data_flow', '')
            if data_flow:
                doc_id = self.add_document(
                    content=f"数据流: {data_flow}",
                    metadata={**base_metadata, 'content_type': 'data_flow'}
                )
                document_ids.append(doc_id)
            
            # 关键机制
            key_mechanisms = architecture.get('key_mechanisms', '')
            if key_mechanisms:
                doc_id = self.add_document(
                    content=f"关键机制: {key_mechanisms}",
                    metadata={**base_metadata, 'content_type': 'key_mechanisms'}
                )
                document_ids.append(doc_id)
        
        # 添加实现细节
        implementation = paper_analysis.get('analysis', {}).get('implementation', {})
        if implementation:
            # 关键算法
            key_algorithms = implementation.get('key_algorithms', '')
            if key_algorithms:
                doc_id = self.add_document(
                    content=f"关键算法: {key_algorithms}",
                    metadata={**base_metadata, 'content_type': 'key_algorithms'}
                )
                document_ids.append(doc_id)
            
            # NS3实现要点
            ns3_requirements = implementation.get('ns3_requirements', '')
            if ns3_requirements:
                doc_id = self.add_document(
                    content=f"NS3实现要点: {ns3_requirements}",
                    metadata={**base_metadata, 'content_type': 'ns3_requirements'}
                )
                document_ids.append(doc_id)
            
            # P4实现要点
            p4_requirements = implementation.get('p4_requirements', '')
            if p4_requirements:
                doc_id = self.add_document(
                    content=f"P4实现要点: {p4_requirements}",
                    metadata={**base_metadata, 'content_type': 'p4_requirements'}
                )
                document_ids.append(doc_id)
        
        return document_ids
    
    def process(self, query, paper_context=None, conversation_id=''):
        """
        处理查询并返回增强的结果
        
        Args:
            query (str): 用户查询
            paper_context (dict, optional): 论文上下文信息
            conversation_id (str): 会话ID
            
        Returns:
            dict: 处理结果
        """
        # 生成增强查询
        if paper_context:
            paper_context_str = json.dumps(paper_context, ensure_ascii=False)
            enhanced_queries_result = self.query_generator(
                original_query=query,
                paper_context=paper_context_str
            )
            enhanced_queries = enhanced_queries_result.enhanced_queries.split('\n')
        else:
            enhanced_queries = [query]
        
        # 保留原始查询
        if query not in enhanced_queries:
            enhanced_queries.append(query)
        
        # 对每个查询搜索文档
        all_docs = []
        for q in enhanced_queries[:3]:  # 限制使用前3个查询
            docs = self.search(q, top_k=3)
            all_docs.extend(docs)
        
        # 去重
        unique_docs = []
        doc_ids = set()
        for doc in all_docs:
            if doc.id not in doc_ids:
                unique_docs.append(doc)
                doc_ids.add(doc.id)
        
        # 最多保留5个最相关的文档
        retrieved_docs = unique_docs[:5]
        
        # 创建RAG结果
        rag_result = RAGResult(query=query, documents=retrieved_docs)
        
        # 分析相关性
        if len(retrieved_docs) > 0:
            relevance_result = self.relevance_analyzer(
                query=query,
                context=rag_result.context
            )
            
            # 整合知识
            integration_result = self.knowledge_integrator(
                query=query,
                context=rag_result.context
            )
            
            # 构建最终结果
            result = {
                "query": query,
                "enhanced_queries": enhanced_queries,
                "retrieved_documents": [
                    {"content": doc.content, "metadata": doc.metadata}
                    for doc in retrieved_docs
                ],
                "relevance_analysis": relevance_result.relevance_analysis,
                "reliability_score": relevance_result.reliability_score,
                "integrated_knowledge": integration_result.integrated_knowledge
            }
        else:
            # 没有找到相关文档
            result = {
                "query": query,
                "enhanced_queries": enhanced_queries,
                "retrieved_documents": [],
                "relevance_analysis": "没有找到相关文档",
                "reliability_score": "0",
                "integrated_knowledge": "没有足够的知识来回答此查询"
            }
        
        # 保存结果
        result_path = self.save_result(
            result=result,
            result_type="rag_result",
            conversation_id=conversation_id
        )
        
        # 将文件路径添加到结果中
        result["result_path"] = result_path
        result["result_id"] = os.path.basename(result_path).split("_")[1].split(".")[0]
        
        return result 