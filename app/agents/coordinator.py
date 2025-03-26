import os
import json
import uuid
from pathlib import Path
from .paper_analyzer import PaperAnalyzer
from .rag_engine import RAGEngine
from .code_generator import CodeGenerator
from .evaluator import Evaluator
from .refiner import Refiner

class AgentCoordinator:
    """协调所有Agent工作的协调器"""
    
    def __init__(self, config):
        """
        初始化协调器
        
        Args:
            config (dict): 配置字典
        """
        self.config = config
        
        # 初始化所有Agent
        self.paper_analyzer = PaperAnalyzer(config)
        self.rag_engine = RAGEngine(config)
        self.code_generator = CodeGenerator(config)
        self.evaluator = Evaluator(config)
        self.refiner = Refiner(config)
        
        # 创建会话存储路径
        self.conversation_store = Path(config['storage'].get('document_store_path'))
        self.conversation_store.mkdir(parents=True, exist_ok=True)
    
    def process_message(self, message, conversation_id=''):
        """
        处理用户消息
        
        Args:
            message (str): 用户消息
            conversation_id (str): 会话ID
            
        Returns:
            str: 回复消息
        """
        # 确保会话ID存在
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        # 检查消息是否为查询
        if self._is_question(message):
            # 尝试从RAG获取回答
            try:
                # 获取会话上下文
                context = self._get_conversation_context(conversation_id)
                
                # 使用RAG生成回答
                rag_result = self.rag_engine.process(
                    query=message,
                    paper_context=context,
                    conversation_id=conversation_id
                )
                
                return rag_result.get('integrated_knowledge', '抱歉，我无法回答这个问题。')
            except Exception as e:
                return f"处理查询时出错: {str(e)}"
        else:
            # 对于非问题的消息，返回一个通用回复
            return "我已收到您的消息。如需分析论文或生成代码，请使用相应的功能。"
    
    def analyze_paper(self, paper_content, conversation_id=''):
        """
        分析论文内容
        
        Args:
            paper_content (dict): 论文内容
            conversation_id (str): 会话ID
            
        Returns:
            dict: 分析结果
        """
        # 确保会话ID存在
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        try:
            # 检查API密钥是否正确配置
            if not os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY').startswith('sk-e34ed'):
                return {'error': "API密钥未正确配置，请在.env文件中设置有效的OPENAI_API_KEY"}
            
            print(f"开始分析论文，会话ID: {conversation_id}")
            
            # 使用PaperAnalyzer分析论文
            analysis_result = self.paper_analyzer.process(
                paper_content=paper_content,
                conversation_id=conversation_id
            )
            
            print(f"论文分析完成，结果: {json.dumps(analysis_result, ensure_ascii=False)[:100]}...")
            
            # 将分析结果添加到RAG知识库
            self.rag_engine.add_paper_to_knowledge_base(
                paper_analysis=analysis_result,
                conversation_id=conversation_id
            )
            
            print("论文知识已添加到RAG知识库")
            
            # 保存会话上下文
            self._save_conversation_context(conversation_id, {
                'paper_analysis': analysis_result
            })
            
            return analysis_result
        except Exception as e:
            print(f"分析论文时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': f"分析论文时出错: {str(e)}"}
    
    def generate_code(self, paper_id, code_type, conversation_id=''):
        """
        生成代码实现
        
        Args:
            paper_id (str): 论文分析结果ID
            code_type (str): 代码类型 ('python', 'ns3', 'p4')
            conversation_id (str): 会话ID
            
        Returns:
            dict: 生成的代码
        """
        # 确保会话ID存在
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        try:
            # 加载论文分析结果
            paper_analysis = self._load_paper_analysis(paper_id, conversation_id)
            if not paper_analysis:
                return {'error': f"找不到论文分析结果: {paper_id}"}
            
            # 使用CodeGenerator生成代码
            code_result = self.code_generator.process(
                paper_analysis=paper_analysis,
                code_type=code_type,
                conversation_id=conversation_id
            )
            
            # 更新会话上下文
            context = self._get_conversation_context(conversation_id)
            if not context:
                context = {}
            
            if 'generated_code' not in context:
                context['generated_code'] = {}
            
            context['generated_code'][code_type] = {
                'code_id': code_result.get('result_id', ''),
                'result_path': code_result.get('result_path', '')
            }
            
            self._save_conversation_context(conversation_id, context)
            
            return code_result
        except Exception as e:
            return {'error': f"生成代码时出错: {str(e)}"}
    
    def evaluate_implementation(self, paper_id, code_id, conversation_id=''):
        """
        评估代码实现
        
        Args:
            paper_id (str): 论文分析结果ID
            code_id (str): 代码结果ID
            conversation_id (str): 会话ID
            
        Returns:
            dict: 评估结果
        """
        # 确保会话ID存在
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        try:
            # 加载论文分析结果
            paper_analysis = self._load_paper_analysis(paper_id, conversation_id)
            if not paper_analysis:
                return {'error': f"找不到论文分析结果: {paper_id}"}
            
            # 加载代码生成结果
            code_result = self._load_code_result(code_id, conversation_id)
            if not code_result:
                return {'error': f"找不到代码生成结果: {code_id}"}
            
            # 使用Evaluator评估代码
            evaluation_result = self.evaluator.process(
                paper_analysis=paper_analysis,
                code_result=code_result,
                conversation_id=conversation_id
            )
            
            # 更新会话上下文
            context = self._get_conversation_context(conversation_id)
            if not context:
                context = {}
            
            if 'evaluations' not in context:
                context['evaluations'] = {}
            
            code_type = code_result.get('code_type', 'unknown')
            context['evaluations'][code_type] = {
                'evaluation_id': evaluation_result.get('result_id', ''),
                'result_path': evaluation_result.get('result_path', '')
            }
            
            self._save_conversation_context(conversation_id, context)
            
            return evaluation_result
        except Exception as e:
            return {'error': f"评估代码时出错: {str(e)}"}
    
    def refine_implementation(self, paper_id, code_id, feedback, conversation_id=''):
        """
        优化代码实现
        
        Args:
            paper_id (str): 论文分析结果ID
            code_id (str): 代码结果ID
            feedback (str): 用户反馈
            conversation_id (str): 会话ID
            
        Returns:
            dict: 优化后的代码
        """
        # 确保会话ID存在
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        try:
            # 加载代码生成结果
            code_result = self._load_code_result(code_id, conversation_id)
            if not code_result:
                return {'error': f"找不到代码生成结果: {code_id}"}
            
            # 找到对应的评估结果
            code_type = code_result.get('code_type', 'unknown')
            evaluation_id = self._get_evaluation_id_for_code_type(code_type, conversation_id)
            
            if not evaluation_id:
                # 如果没有找到评估结果，先生成一个
                paper_analysis = self._load_paper_analysis(paper_id, conversation_id)
                if not paper_analysis:
                    return {'error': f"找不到论文分析结果: {paper_id}"}
                
                evaluation_result = self.evaluator.process(
                    paper_analysis=paper_analysis,
                    code_result=code_result,
                    conversation_id=conversation_id
                )
            else:
                # 加载现有的评估结果
                evaluation_result = self._load_evaluation_result(evaluation_id, conversation_id)
            
            # 使用Refiner优化代码
            refined_result = self.refiner.process(
                code_result=code_result,
                evaluation_result=evaluation_result,
                user_feedback=feedback,
                conversation_id=conversation_id
            )
            
            # 更新会话上下文
            context = self._get_conversation_context(conversation_id)
            if not context:
                context = {}
            
            if 'refined_code' not in context:
                context['refined_code'] = {}
            
            context['refined_code'][code_type] = {
                'refined_id': refined_result.get('result_id', ''),
                'result_path': refined_result.get('result_path', '')
            }
            
            self._save_conversation_context(conversation_id, context)
            
            return refined_result
        except Exception as e:
            return {'error': f"优化代码时出错: {str(e)}"}
    
    def _is_question(self, message):
        """判断消息是否为问题"""
        # 简单判断：以问号结尾或者包含疑问词
        question_words = ['什么', '如何', '为什么', '怎么', '哪个', '哪些', '谁', '何时', '何地', '是否']
        
        if message.strip().endswith('?') or message.strip().endswith('？'):
            return True
        
        for word in question_words:
            if word in message:
                return True
        
        return False
    
    def _save_conversation_context(self, conversation_id, context):
        """保存会话上下文"""
        context_path = self.conversation_store / conversation_id / 'context.json'
        context_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(context_path, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
    
    def _get_conversation_context(self, conversation_id):
        """获取会话上下文"""
        context_path = self.conversation_store / conversation_id / 'context.json'
        
        if context_path.exists():
            try:
                with open(context_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        
        return {}
    
    def _load_paper_analysis(self, paper_id, conversation_id):
        """加载论文分析结果"""
        # 尝试从上下文中找到结果路径
        context = self._get_conversation_context(conversation_id)
        paper_analysis = context.get('paper_analysis', {})
        
        # 如果上下文中存在结果，且ID匹配，直接返回
        if paper_analysis and paper_analysis.get('result_id') == paper_id:
            return paper_analysis
        
        # 否则直接加载文件
        try:
            analysis_path = self.conversation_store / conversation_id / f"paper_analysis_{paper_id}.json"
            if analysis_path.exists():
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    return result.get('data', {})
        except:
            pass
        
        # 使用paper_analyzer的load_result方法
        result = self.paper_analyzer.load_result(paper_id, conversation_id)
        if result:
            return result.get('data', {})
        
        return None
    
    def _load_code_result(self, code_id, conversation_id):
        """加载代码生成结果"""
        # 尝试使用code_generator的load_result方法
        result = self.code_generator.load_result(code_id, conversation_id)
        if result:
            return result.get('data', {})
        
        # 尝试从文件加载
        code_types = ['python', 'ns3', 'p4']
        for code_type in code_types:
            try:
                code_path = self.conversation_store / conversation_id / f"{code_type}_code_{code_id}.json"
                if code_path.exists():
                    with open(code_path, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        return result.get('data', {})
            except:
                continue
        
        return None
    
    def _load_evaluation_result(self, evaluation_id, conversation_id):
        """加载评估结果"""
        # 尝试使用evaluator的load_result方法
        result = self.evaluator.load_result(evaluation_id, conversation_id)
        if result:
            return result.get('data', {})
        
        # 尝试从文件加载
        code_types = ['python', 'ns3', 'p4']
        for code_type in code_types:
            try:
                eval_path = self.conversation_store / conversation_id / f"{code_type}_evaluation_{evaluation_id}.json"
                if eval_path.exists():
                    with open(eval_path, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        return result.get('data', {})
            except:
                continue
        
        return None
    
    def _get_evaluation_id_for_code_type(self, code_type, conversation_id):
        """获取特定代码类型的评估ID"""
        context = self._get_conversation_context(conversation_id)
        evaluations = context.get('evaluations', {})
        
        if code_type in evaluations:
            return evaluations[code_type].get('evaluation_id', '')
        
        return '' 