import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
from pathlib import Path

# 添加项目根目录到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from app.agents.coordinator import AgentCoordinator
from app.utils.pdf_processor import PDFProcessor
from app.utils.config import load_config

# 配置Flask应用
app = Flask(__name__, static_folder='../frontend')
CORS(app)  # 允许跨域请求

# 加载配置
config = load_config()

# 初始化Agent协调器
coordinator = AgentCoordinator(config)

# 初始化PDF处理器
pdf_processor = PDFProcessor(config)

@app.route('/')
def serve_frontend():
    """提供前端静态文件"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理用户聊天请求"""
    data = request.json
    message = data.get('message', '')
    conversation_id = data.get('conversation_id', '')
    
    # 获取Agent回复
    response = coordinator.process_message(message, conversation_id)
    
    return jsonify({
        'response': response,
        'conversation_id': conversation_id
    })

@app.route('/api/upload-paper', methods=['POST'])
def upload_paper():
    """处理论文上传"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    conversation_id = request.form.get('conversation_id', '')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.pdf'):
        # 保存PDF文件
        paper_path = pdf_processor.save_pdf(file, conversation_id)
        
        # 解析PDF文件
        paper_content = pdf_processor.parse_pdf(paper_path)
        
        # 处理论文内容
        analysis = coordinator.analyze_paper(paper_content, conversation_id)
        
        return jsonify({
            'message': '论文上传并解析成功',
            'analysis': analysis,
            'conversation_id': conversation_id
        })
    
    return jsonify({'error': '不支持的文件格式，请上传PDF文件'}), 400

@app.route('/api/generate-code', methods=['POST'])
def generate_code():
    """生成代码实现"""
    data = request.json
    paper_id = data.get('paper_id', '')
    code_type = data.get('code_type', 'python')  # 'python', 'ns3', 'p4'
    conversation_id = data.get('conversation_id', '')
    
    code = coordinator.generate_code(paper_id, code_type, conversation_id)
    
    return jsonify({
        'code': code,
        'code_type': code_type,
        'conversation_id': conversation_id
    })

@app.route('/api/evaluate-implementation', methods=['POST'])
def evaluate_implementation():
    """评估实现"""
    data = request.json
    paper_id = data.get('paper_id', '')
    code_id = data.get('code_id', '')
    conversation_id = data.get('conversation_id', '')
    
    evaluation = coordinator.evaluate_implementation(paper_id, code_id, conversation_id)
    
    return jsonify({
        'evaluation': evaluation,
        'conversation_id': conversation_id
    })

@app.route('/api/refine-implementation', methods=['POST'])
def refine_implementation():
    """优化实现"""
    data = request.json
    paper_id = data.get('paper_id', '')
    code_id = data.get('code_id', '')
    feedback = data.get('feedback', '')
    conversation_id = data.get('conversation_id', '')
    
    refined_code = coordinator.refine_implementation(
        paper_id, code_id, feedback, conversation_id
    )
    
    return jsonify({
        'refined_code': refined_code,
        'conversation_id': conversation_id
    })

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug) 