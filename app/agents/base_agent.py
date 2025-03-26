import os
import json
import dspy
import uuid
import logging
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseAgent:
    """所有Agent的基类，提供通用功能"""
    
    def __init__(self, config, name=None):
        """
        初始化Agent
        
        Args:
            config (dict): 配置字典
            name (str, optional): Agent名称
        """
        self.config = config
        self.name = name or self.__class__.__name__
        
        # 初始化DSPy模型
        self._init_model()
        
        # 初始化存储路径
        self.storage_path = Path(config['storage'].get(f'{self.name.lower()}_store_path',
                                                    config['storage']['document_store_path']))
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _init_model(self):
        """初始化LLM模型"""
        # 获取API配置
        api_config = self.config['api']
        api_key = api_config['openai_api_key']
        base_url = api_config.get('base_url', '')
        
        # 获取模型配置
        if 'models' not in self.config:
            default_model = os.getenv('DEFAULT_MODEL', 'deepseek-reasoner')
            self.config['models'] = {'default_model': default_model}
            logger.warning(f"配置中缺少'models'键，使用环境变量或默认值: {default_model}")
        
        # 获取agent特定配置
        agent_config = self.config['agents'].get(self.name.lower(), {})
        model_name = agent_config.get('model') or self.config['models']['default_model']
        temperature = float(agent_config.get('temperature', 0.3))
        
        logger.info(f'模型名称: {model_name}')
        
        # 创建LM实例
        lm_kwargs = {
            'api_key': api_key,
            'temperature': temperature
        }
        
        if base_url:
            model_path = f"openai/{model_name}"
            lm_kwargs['api_base'] = base_url
            logger.info(f"使用自定义API基础URL: {base_url}")
            logger.info(f"模型路径: {model_path}")
            lm = dspy.LM(model_path, **lm_kwargs)
        else:
            lm = dspy.LM(model_name, **lm_kwargs)
        
        # 配置DSPy
        dspy.configure(lm=lm)
        logger.info(f"DSPy已配置，使用模型: {model_name}")
        
        # 创建Prompt模板管理器
        self._load_prompts()
    
    def _load_prompts(self):
        """加载Agent的提示模板"""
        # 这个方法应该被子类重写以加载特定的提示模板
        self.prompts = {}
    
    def generate_id(self):
        """生成唯一ID"""
        return str(uuid.uuid4())
    
    def save_result(self, result, result_type, conversation_id):
        """
        保存Agent的处理结果
        
        Args:
            result: 要保存的结果
            result_type (str): 结果类型
            conversation_id (str): 会话ID
            
        Returns:
            str: 保存的文件路径
        """
        # 确保会话目录存在
        conversation_dir = self.storage_path / conversation_id
        conversation_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名和路径
        result_id = self.generate_id()
        file_name = f"{result_type}_{result_id}.json"
        file_path = conversation_dir / file_name
        
        # 获取当前时间
        timestamp = datetime.now().isoformat()
        
        # 添加元数据
        result_with_meta = {
            'id': result_id,
            'type': result_type,
            'agent': self.name,
            'timestamp': timestamp,
            'data': result
        }
        
        # 保存到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result_with_meta, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def load_result(self, result_id, conversation_id):
        """
        加载保存的结果
        
        Args:
            result_id (str): 结果ID
            conversation_id (str): 会话ID
            
        Returns:
            dict: 加载的结果，如果不存在则返回None
        """
        # 搜索会话目录下所有结果文件
        conversation_dir = self.storage_path / conversation_id
        if not conversation_dir.exists():
            return None
        
        # 查找包含指定ID的文件
        for file_path in conversation_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                if result.get('id') == result_id:
                    return result
            except Exception as e:
                logger.error(f"加载结果文件出错: {e}")
                continue
        
        return None
    
    def process(self, input_data, conversation_id=''):
        """
        处理输入数据的主方法
        
        Args:
            input_data: 要处理的输入数据
            conversation_id (str): 会话ID
            
        Returns:
            处理结果
        """
        # 这个方法应该被子类重写以实现特定的处理逻辑
        raise NotImplementedError("子类必须实现process方法") 
    
    
if __name__ == "__main__":
    # 测试BaseAgent
    config = {
        "agents": {
            "base_agent": {
                "model": "deepseek-chat"
            },
            "test_agent": {
                "model": "deepseek-chat",
                "temperature": 0.5
            }
        },
        "api": {
            "openai_api_key": "sk-e34ed2a31fdf42da8cf706fee552f16f",
            "base_url": "https://api.deepseek.com/v1",
        },
        "models": {
            "default_model": "deepseek-chat"
        },
        "storage": {
            "document_store_path": "../data/documents"
        }
    }
    
    class TestAgent(BaseAgent):
        """演示如何扩展BaseAgent的测试代理"""
        
        def _load_prompts(self):
            """加载测试Agent的提示模板"""
            self.prompts = {
                "greeting": "你好，我是一个测试Agent。",
                "farewell": "再见，感谢使用测试Agent。",
            }
        
        def process(self, input_data, conversation_id=''):
            """
            处理输入数据
            
            Args:
                input_data (str): 用户输入文本
                conversation_id (str): 会话ID
                
            Returns:
                dict: 处理结果
            """
            logger.info(f"TestAgent正在处理: {input_data}")
            
            # 简单的回复逻辑
            if "你好" in input_data or "hello" in input_data.lower():
                response = self.prompts["greeting"]
            elif "再见" in input_data or "bye" in input_data.lower():
                response = self.prompts["farewell"]
            else:
                try:
                    # 定义工具函数
                    def evaluate_math(expression: str):
                        """计算数学表达式的值"""
                        try:
                            # 安全地执行数学表达式
                            from ast import parse, literal_eval
                            parsed = parse(expression, mode='eval')
                            result = eval(compile(parsed, '<string>', 'eval'))
                            return str(result)
                        except Exception as e:
                            return f"计算错误: {str(e)}"
                    
                    def search_wikipedia(query: str):
                        results = dspy.ColBERTv2(url='http://20.102.90.50:2017/wiki17_abstracts')(query, k=3)
                        return [x['text'] for x in results]

                    def current_time():
                        """获取当前时间"""
                        now = datetime.now()
                        return now.strftime("%Y年%m月%d日 %H:%M:%S")
                    
                    # 使用ReAct模式构建Agent
                    react = dspy.ReAct(
                        "question -> answer", 
                        tools=[evaluate_math, current_time, search_wikipedia]
                    )
                    
                    # 运行推理
                    prediction = react(question=input_data)
                    response = prediction.answer
                
                except Exception as e:
                    logger.error(f"调用模型出错: {e}", exc_info=True)
                    response = f"抱歉，我遇到了一些问题: {str(e)}"
            
            # 准备结果
            result = {
                "input": input_data,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }

            return result

    # 仅当直接运行脚本时才执行测试代码
    try:
        # 测试前确保有有效的API密钥
        if config["api"]["openai_api_key"] == "YOUR_API_KEY_HERE":
            logger.warning("请提供有效的API密钥进行测试")
            import sys
            sys.exit(0)
            
        # 创建TestAgent实例
        agent = TestAgent(config, name="test_agent")
        
        # 处理一些测试输入
        test_cases = [
            ("你好，TestAgent！", "=== 测试1: 问候 ==="),
            ("你是谁", "=== 测试2: 问题 ==="),
            ("What is 123 + 456?", "=== 测试3: 计算 ==="),
            ("现在是什么时间？", "=== 测试4: 时间 ==="),
            ("再见，谢谢！", "=== 测试5: 告别 ===")
        ]
        
        for input_text, test_name in test_cases:
            print(f"\n\033[1;33m{'='*50}\n{test_name:^40}\n{'='*50}\033[0m")
            result = agent.process(input_text)
            print(f"\033[1;36m{'='*50}\n{'回复':^20}\n{result['response']:^40}\n{'='*50}\033[0m\n\n\n")
    except Exception as e:
        logger.error(f"测试过程中出错: {e}", exc_info=True)