import os
import json
import dspy
import uuid
from pathlib import Path

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
        # 获取OpenAI API密钥
        api_key = self.config['api']['openai_api_key']
        
        # 获取BASE_URL(如果存在)
        base_url = self.config['api'].get('base_url', '')
        
        # 从agent特定配置或全局配置获取模型名称
        model_name = (self.config['agents'].get(self.name.lower(), {}).get('model') or 
                    self.config['models']['default_model'])
        
        # 从agent特定配置或使用默认温度
        temperature = float(self.config['agents'].get(self.name.lower(), {}).get('temperature', 0.3))
        
        # 使用DSPy最新API
        model_path = model_name
        # 如果使用非默认API基础URL，将模型名称设置为openai前缀
        if base_url:
            model_path = f"openai/{model_name}"
        
        # 创建LM实例
        lm = dspy.LM(
            model_path, 
            api_key=api_key,
            temperature=temperature
        )
        
        # 如果有自定义API基础URL
        if base_url:
            lm.api_base = base_url
        
        # 配置DSPy
        dspy.configure(lm=lm)
        
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
        
        # 添加元数据
        result_with_meta = {
            'id': result_id,
            'type': result_type,
            'agent': self.name,
            'timestamp': dspy.utils.now_str(),
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
            except:
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