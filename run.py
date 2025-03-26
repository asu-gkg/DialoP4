#!/usr/bin/env python
"""
DialoP4 启动脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到sys.path
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))

from app.backend.server import app

if __name__ == "__main__":
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"启动DialoP4服务器...")
    print(f"访问地址: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    
    app.run(host=host, port=port, debug=debug) 