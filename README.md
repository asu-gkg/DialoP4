# DialoP4 - 网络研究智能代理系统

DialoP4是一个基于大型语言模型的智能代理系统，专为网络研究设计。系统能够解析NSDI/SIGCOMM等顶级会议的网络论文，并自动生成对应的NS3模拟代码、P4代码、Python实现、评估报告和交互式可视化界面。

## 系统架构

系统采用多Agent架构，包括：

- **Paper Analyzer**：负责解析和理解学术论文内容
- **RAG Engine**：基于检索增强生成技术，提供专业领域知识支持
- **Code Generator**：生成NS3、P4和Python代码实现
- **Evaluator**：评估生成代码的正确性和性能
- **Iterative-Refiner**：进行多轮自我优化和迭代改进

## 核心特性

- **多Agent协同**：各个Agent负责不同职能，相互协作完成复杂任务
- **迭代式思考**：通过多轮自我优化避免浅层思考和"思维捷径"
- **检索增强生成**：融合网络领域专业知识库提升输出质量
- **人机协作循环**：支持人类专家反馈和指导

## 如何使用

1. 安装依赖：`pip install -r requirements.txt`
2. 配置环境变量：复制`.env.example`为`.env`并填入必要的API密钥
3. 启动服务器：`python app/backend/server.py`
4. 访问Web界面：打开浏览器访问`http://localhost:5000`

## 使用场景

- 快速原型研发：将网络研究论文转化为可执行代码
- 教学辅助：帮助学生理解复杂网络概念和实现
- 研究验证：复现和验证已发表论文的实验结果
- 创新探索：启发新的网络架构和算法设计 