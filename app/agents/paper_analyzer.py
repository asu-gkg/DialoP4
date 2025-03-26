import os
import json
import dspy
from .base_agent import BaseAgent

class NetworkConceptExtractor(dspy.Signature):
    """提取网络论文中的关键概念和技术"""
    paper_content = dspy.InputField(desc="论文原始内容")
    concepts = dspy.OutputField(desc="提取的关键网络概念和技术，包括算法、协议、架构等")
    innovations = dspy.OutputField(desc="论文的创新点和贡献")
    technical_details = dspy.OutputField(desc="实现细节、参数设置、技术规格等")

class ArchitectureAnalyzer(dspy.Signature):
    """分析网络系统的架构设计"""
    paper_content = dspy.InputField(desc="论文原始内容")
    architecture = dspy.OutputField(desc="系统架构描述，包括组件和它们的交互方式")
    data_flow = dspy.OutputField(desc="数据在系统中如何流动")
    control_flow = dspy.OutputField(desc="控制信息在系统中如何流动")
    key_mechanisms = dspy.OutputField(desc="关键机制和算法的详细描述")

class EvaluationExtractor(dspy.Signature):
    """提取论文中的评估方法和结果"""
    paper_content = dspy.InputField(desc="论文原始内容")
    metrics = dspy.OutputField(desc="评估指标")
    methodology = dspy.OutputField(desc="评估方法论")
    results = dspy.OutputField(desc="主要评估结果")
    comparison = dspy.OutputField(desc="与其他系统的比较")

class CodeImplicationAnalyzer(dspy.Signature):
    """分析论文实现代码的需求"""
    paper_content = dspy.InputField(desc="论文原始内容")
    key_algorithms = dspy.OutputField(desc="需要实现的关键算法")
    ns3_requirements = dspy.OutputField(desc="NS3实现的要点和注意事项")
    p4_requirements = dspy.OutputField(desc="P4实现的要点和注意事项")
    python_requirements = dspy.OutputField(desc="Python实现的要点和注意事项")
    dependencies = dspy.OutputField(desc="实现可能需要的依赖库和工具")

class ComprehensivePaperAnalyzer(dspy.Module):
    """综合分析网络论文的DSPy模块"""
    
    def __init__(self):
        super().__init__()
        self.concept_extractor = dspy.Predict(NetworkConceptExtractor)
        self.architecture_analyzer = dspy.Predict(ArchitectureAnalyzer)
        self.evaluation_extractor = dspy.Predict(EvaluationExtractor)
        self.code_analyzer = dspy.Predict(CodeImplicationAnalyzer)
    
    def forward(self, paper_content):
        # 提取关键概念
        concept_result = self.concept_extractor(paper_content=paper_content)
        
        # 分析架构
        architecture_result = self.architecture_analyzer(paper_content=paper_content)
        
        # 提取评估方法和结果
        evaluation_result = self.evaluation_extractor(paper_content=paper_content)
        
        # 分析代码实现需求
        code_result = self.code_analyzer(paper_content=paper_content)
        
        # 合并结果
        result = {
            "concepts": {
                "key_concepts": concept_result.concepts,
                "innovations": concept_result.innovations,
                "technical_details": concept_result.technical_details
            },
            "architecture": {
                "overview": architecture_result.architecture,
                "data_flow": architecture_result.data_flow,
                "control_flow": architecture_result.control_flow,
                "key_mechanisms": architecture_result.key_mechanisms
            },
            "evaluation": {
                "metrics": evaluation_result.metrics,
                "methodology": evaluation_result.methodology,
                "results": evaluation_result.results,
                "comparison": evaluation_result.comparison
            },
            "implementation": {
                "key_algorithms": code_result.key_algorithms,
                "ns3_requirements": code_result.ns3_requirements,
                "p4_requirements": code_result.p4_requirements,
                "python_requirements": code_result.python_requirements,
                "dependencies": code_result.dependencies
            }
        }
        
        return result

class PaperSummarizer(dspy.Signature):
    """生成论文的人类可读摘要"""
    analysis = dspy.InputField(desc="论文的详细分析结果")
    title = dspy.InputField(desc="论文标题")
    summary = dspy.OutputField(desc="论文的人类可读摘要，简明扼要地介绍论文的重点内容")

class PaperAnalyzer(BaseAgent):
    """负责解析和理解学术论文内容的Agent"""
    
    def __init__(self, config):
        super().__init__(config, name="paper_analyzer")
        
        # 初始化DSPy模块
        self.analyzer = ComprehensivePaperAnalyzer()
        self.summarizer = dspy.Predict(PaperSummarizer)
    
    def _load_prompts(self):
        """加载Agent特定的提示模板"""
        self.prompts = {
            "analyze": """
你是一位专业的网络研究论文分析专家。你需要仔细阅读这篇论文，并提取关键信息。
请特别关注：
1. 网络概念和创新点
2. 系统架构和数据流
3. 评估方法和结果
4. 实现细节和算法

请以结构化的方式组织你的分析，以便后续可以用于生成代码实现。
            """,
            "summarize": """
为以下网络论文分析生成一个简明的摘要。
摘要应该包含论文的主要创新点、关键技术和主要成果。
保持专业性的同时，使用通俗易懂的语言，帮助非专业人士理解论文的价值。
限制在300字以内。
            """
        }
    
    def process(self, paper_content, conversation_id=''):
        """
        分析论文内容
        
        Args:
            paper_content (dict): 论文内容，包含标题、作者、摘要、章节等
            conversation_id (str): 会话ID
            
        Returns:
            dict: 分析结果
        """
        # 准备完整的论文文本
        full_text = f"标题：{paper_content['title']}\n\n"
        full_text += f"作者：{', '.join(paper_content['authors'])}\n\n"
        full_text += f"摘要：{paper_content['abstract']}\n\n"
        
        # 添加章节内容
        for section in paper_content['sections']:
            full_text += f"{section['title']}\n{section['content']}\n\n"
        
        # 分析论文
        analysis = self.analyzer(full_text)
        
        # 生成人类可读摘要
        summary_result = self.summarizer(
            analysis=json.dumps(analysis, ensure_ascii=False),
            title=paper_content['title']
        )
        
        # 构建最终结果
        result = {
            "title": paper_content['title'],
            "authors": paper_content['authors'],
            "analysis": analysis,
            "summary": summary_result.summary,
            "pdf_path": paper_content.get('pdf_path', '')
        }
        
        # 保存结果
        result_path = self.save_result(
            result=result,
            result_type="paper_analysis",
            conversation_id=conversation_id
        )
        
        # 将文件路径添加到结果中
        result["result_path"] = result_path
        result["result_id"] = os.path.basename(result_path).split("_")[1].split(".")[0]
        
        return result 