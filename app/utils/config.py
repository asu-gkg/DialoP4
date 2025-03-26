import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def load_config():
    """
    加载配置信息，优先从环境变量中获取，如果不存在则使用默认值
    
    Returns:
        dict: 配置字典
    """
    config = {
        'app': {
            'env': os.getenv('APP_ENV', 'development'),
            'debug': os.getenv('DEBUG', 'True').lower() == 'true',
            'secret_key': os.getenv('SECRET_KEY', 'default_secret_key'),
        },
        'api': {
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', ''),
            'base_url': os.getenv('BASE_URL', ''),
        },
        'models': {
            'default_model': os.getenv('DEFAULT_MODEL', 'gpt-4o'),
            'embedding_model': os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large'),
        },
        'storage': {
            'vector_db_path': os.getenv('VECTOR_DB_PATH', './app/data/vector_store'),
            'document_store_path': os.getenv('DOCUMENT_STORE_PATH', './app/data/documents'),
            'code_store_path': os.getenv('CODE_STORE_PATH', './app/data/code'),
            'evaluation_store_path': os.getenv('EVALUATION_STORE_PATH', './app/data/evaluations'),
        },
        'server': {
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': int(os.getenv('PORT', 5000)),
        },
        'agents': {
            'paper_analyzer': {
                'model': os.getenv('PAPER_ANALYZER_MODEL', 'gpt-4o'),
                'temperature': float(os.getenv('PAPER_ANALYZER_TEMP', 0.2)),
            },
            'rag_engine': {
                'model': os.getenv('RAG_ENGINE_MODEL', 'gpt-4o'),
                'temperature': float(os.getenv('RAG_ENGINE_TEMP', 0.2)),
                'chunk_size': int(os.getenv('RAG_CHUNK_SIZE', 1000)),
                'chunk_overlap': int(os.getenv('RAG_CHUNK_OVERLAP', 200)),
            },
            'code_generator': {
                'model': os.getenv('CODE_GENERATOR_MODEL', 'gpt-4o'),
                'temperature': float(os.getenv('CODE_GENERATOR_TEMP', 0.3)),
            },
            'evaluator': {
                'model': os.getenv('EVALUATOR_MODEL', 'gpt-4o'),
                'temperature': float(os.getenv('EVALUATOR_TEMP', 0.1)),
            },
            'refiner': {
                'model': os.getenv('REFINER_MODEL', 'gpt-4o'),
                'temperature': float(os.getenv('REFINER_TEMP', 0.3)),
                'max_iterations': int(os.getenv('REFINER_MAX_ITERATIONS', 5)),
            },
        }
    }
    
    # 确保存储路径存在
    for path_key, path_value in config['storage'].items():
        Path(path_value).mkdir(parents=True, exist_ok=True)
    
    return config

def get_agent_config(agent_name):
    """
    获取特定Agent的配置
    
    Args:
        agent_name (str): Agent名称
        
    Returns:
        dict: Agent配置字典
    """
    config = load_config()
    return config['agents'].get(agent_name, {}) 