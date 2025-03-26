import os
import json
import dspy
from pathlib import Path
from .base_agent import BaseAgent

class NS3SkeletonGenerator(dspy.Signature):
    """生成NS3模拟代码框架"""
    paper_analysis = dspy.InputField(desc="论文分析结果")
    architecture_details = dspy.InputField(desc="系统架构详情")
    code_skeleton = dspy.OutputField(desc="NS3模拟代码框架，包含主要类和函数")
    implementation_notes = dspy.OutputField(desc="实现注意事项和关键点")

class NS3FullImplementation(dspy.Signature):
    """生成完整的NS3实现"""
    code_skeleton = dspy.InputField(desc="NS3代码框架")
    paper_analysis = dspy.InputField(desc="论文分析结果")
    ns3_code = dspy.OutputField(desc="完整的NS3实现代码")
    build_instructions = dspy.OutputField(desc="编译和运行说明")

class P4SkeletonGenerator(dspy.Signature):
    """生成P4代码框架"""
    paper_analysis = dspy.InputField(desc="论文分析结果")
    data_plane_details = dspy.InputField(desc="数据平面处理细节")
    code_skeleton = dspy.OutputField(desc="P4代码框架，包含主要表和动作")
    control_plane_requirements = dspy.OutputField(desc="控制平面需求")

class P4FullImplementation(dspy.Signature):
    """生成完整的P4实现"""
    code_skeleton = dspy.InputField(desc="P4代码框架")
    paper_analysis = dspy.InputField(desc="论文分析结果")
    p4_code = dspy.OutputField(desc="完整的P4实现代码")
    control_plane_code = dspy.OutputField(desc="控制平面代码（如有必要）")
    deployment_instructions = dspy.OutputField(desc="部署和测试说明")

class PythonImplementation(dspy.Signature):
    """生成Python实现"""
    paper_analysis = dspy.InputField(desc="论文分析结果")
    key_algorithms = dspy.InputField(desc="关键算法详情")
    python_code = dspy.OutputField(desc="完整的Python实现")
    requirements = dspy.OutputField(desc="依赖要求")
    usage_example = dspy.OutputField(desc="使用示例")

class CodeGenerator(BaseAgent):
    """负责生成NS3、P4和Python代码实现的Agent"""
    
    def __init__(self, config):
        super().__init__(config, name="code_generator")
        
        # 初始化DSPy模块
        self.ns3_skeleton_generator = dspy.Predict(NS3SkeletonGenerator)
        self.ns3_full_implementation = dspy.Predict(NS3FullImplementation)
        self.p4_skeleton_generator = dspy.Predict(P4SkeletonGenerator)
        self.p4_full_implementation = dspy.Predict(P4FullImplementation)
        self.python_implementation = dspy.Predict(PythonImplementation)
    
    def _load_prompts(self):
        """加载Agent特定的提示模板"""
        self.prompts = {
            "ns3_skeleton": """
作为一名NS3专家，你需要为网络论文设计NS3模拟框架。
请分析论文要点，识别需要在NS3中建模的关键组件。
生成的代码框架应包括:
1. 必要的NS3模块和头文件
2. 主要类的定义和成员函数
3. 网络拓扑构建函数
4. 关键算法实现框架
5. 仿真参数设置
            """,
            
            "ns3_implementation": """
基于提供的NS3代码框架和论文分析，现在请实现完整的NS3代码。
确保代码:
1. 正确实现论文中描述的算法和协议
2. 使用NS3的标准编程实践
3. 包含必要的注释
4. 包括性能评估metrics的收集
5. 提供清晰的编译和运行说明
            """,
            
            "p4_skeleton": """
作为P4编程专家，你需要为论文中的网络功能设计P4代码框架。
关注:
1. 定义必要的头部
2. 设计表结构
3. 实现关键的数据处理动作
4. 规划控制流程
5. 考虑目标设备的限制(如BMv2、Tofino)
            """,
            
            "p4_implementation": """
基于提供的P4代码框架和论文分析，实现完整的P4数据平面程序。
你的实现应:
1. 符合P4_16标准
2. 正确实现论文中的数据平面功能
3. 考虑性能和资源限制
4. 包含必要的控制平面接口
5. 提供测试和部署指南
            """,
            
            "python_implementation": """
将论文中的算法转换为高效的Python实现。
你的代码应:
1. 使用现代Python功能和库
2. 实现论文中的关键算法和数据结构
3. 包含适当的错误处理
4. 提供清晰的文档字符串
5. 包括单元测试
6. 展示使用示例
            """
        }
    
    def process(self, paper_analysis, code_type='python', conversation_id=''):
        """
        根据论文分析生成代码实现
        
        Args:
            paper_analysis (dict): 论文分析结果
            code_type (str): 生成代码类型 ('python', 'ns3', 'p4')
            conversation_id (str): 会话ID
            
        Returns:
            dict: 生成的代码和相关信息
        """
        # 提取论文标题和分析结果
        title = paper_analysis.get('title', '')
        analysis_data = paper_analysis.get('analysis', {})
        
        # 转换为JSON字符串以便传递给DSPy模块
        paper_analysis_str = json.dumps(paper_analysis, ensure_ascii=False)
        
        # 根据代码类型生成不同的实现
        if code_type == 'ns3':
            # 提取架构详情
            architecture_details = json.dumps(analysis_data.get('architecture', {}), ensure_ascii=False)
            
            # 生成NS3框架
            skeleton_result = self.ns3_skeleton_generator(
                paper_analysis=paper_analysis_str,
                architecture_details=architecture_details
            )
            
            # 生成完整实现
            implementation_result = self.ns3_full_implementation(
                code_skeleton=skeleton_result.code_skeleton,
                paper_analysis=paper_analysis_str
            )
            
            # 构建结果
            code_result = {
                "title": title,
                "code_type": "ns3",
                "skeleton": {
                    "code": skeleton_result.code_skeleton,
                    "notes": skeleton_result.implementation_notes
                },
                "implementation": {
                    "code": implementation_result.ns3_code,
                    "build_instructions": implementation_result.build_instructions
                }
            }
            
        elif code_type == 'p4':
            # 提取数据平面详情
            data_plane_details = json.dumps({
                "architecture": analysis_data.get('architecture', {}),
                "technical_details": analysis_data.get('concepts', {}).get('technical_details', '')
            }, ensure_ascii=False)
            
            # 生成P4框架
            skeleton_result = self.p4_skeleton_generator(
                paper_analysis=paper_analysis_str,
                data_plane_details=data_plane_details
            )
            
            # 生成完整实现
            implementation_result = self.p4_full_implementation(
                code_skeleton=skeleton_result.code_skeleton,
                paper_analysis=paper_analysis_str
            )
            
            # 构建结果
            code_result = {
                "title": title,
                "code_type": "p4",
                "skeleton": {
                    "code": skeleton_result.code_skeleton,
                    "control_plane_requirements": skeleton_result.control_plane_requirements
                },
                "implementation": {
                    "code": implementation_result.p4_code,
                    "control_plane_code": implementation_result.control_plane_code,
                    "deployment_instructions": implementation_result.deployment_instructions
                }
            }
            
        else:  # python
            # 提取关键算法
            key_algorithms = json.dumps(analysis_data.get('implementation', {}).get('key_algorithms', ''), ensure_ascii=False)
            
            # 生成Python实现
            implementation_result = self.python_implementation(
                paper_analysis=paper_analysis_str,
                key_algorithms=key_algorithms
            )
            
            # 构建结果
            code_result = {
                "title": title,
                "code_type": "python",
                "implementation": {
                    "code": implementation_result.python_code,
                    "requirements": implementation_result.requirements,
                    "usage_example": implementation_result.usage_example
                }
            }
        
        # 保存结果
        result_path = self.save_result(
            result=code_result,
            result_type=f"{code_type}_code",
            conversation_id=conversation_id
        )
        
        # 将文件路径添加到结果中
        code_result["result_path"] = result_path
        code_result["result_id"] = os.path.basename(result_path).split("_")[1].split(".")[0]
        
        # 生成代码文件
        self._save_code_files(code_result, code_type, conversation_id)
        
        return code_result
    
    def _save_code_files(self, code_result, code_type, conversation_id):
        """
        将生成的代码保存到文件
        
        Args:
            code_result (dict): 代码生成结果
            code_type (str): 代码类型
            conversation_id (str): 会话ID
        """
        # 创建代码存储路径
        code_dir = Path(self.config['storage']['code_store_path']) / conversation_id / code_type
        code_dir.mkdir(parents=True, exist_ok=True)
        
        if code_type == 'ns3':
            # 保存NS3框架
            with open(code_dir / "ns3_skeleton.cc", 'w', encoding='utf-8') as f:
                f.write(code_result['skeleton']['code'])
            
            # 保存实现笔记
            with open(code_dir / "implementation_notes.md", 'w', encoding='utf-8') as f:
                f.write(code_result['skeleton']['notes'])
            
            # 保存完整实现
            with open(code_dir / "ns3_implementation.cc", 'w', encoding='utf-8') as f:
                f.write(code_result['implementation']['code'])
            
            # 保存构建说明
            with open(code_dir / "build_instructions.md", 'w', encoding='utf-8') as f:
                f.write(code_result['implementation']['build_instructions'])
                
        elif code_type == 'p4':
            # 保存P4框架
            with open(code_dir / "p4_skeleton.p4", 'w', encoding='utf-8') as f:
                f.write(code_result['skeleton']['code'])
            
            # 保存控制平面需求
            with open(code_dir / "control_plane_requirements.md", 'w', encoding='utf-8') as f:
                f.write(code_result['skeleton']['control_plane_requirements'])
            
            # 保存完整实现
            with open(code_dir / "p4_implementation.p4", 'w', encoding='utf-8') as f:
                f.write(code_result['implementation']['code'])
            
            # 保存控制平面代码（如果有）
            control_plane_code = code_result['implementation']['control_plane_code']
            if control_plane_code:
                with open(code_dir / "control_plane.py", 'w', encoding='utf-8') as f:
                    f.write(control_plane_code)
            
            # 保存部署说明
            with open(code_dir / "deployment_instructions.md", 'w', encoding='utf-8') as f:
                f.write(code_result['implementation']['deployment_instructions'])
                
        else:  # python
            # 创建Python包结构
            src_dir = code_dir / "src"
            src_dir.mkdir(exist_ok=True)
            
            # 提取代码并分割成多个文件
            python_code = code_result['implementation']['code']
            
            # 保存完整代码
            with open(code_dir / "full_implementation.py", 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            # 保存需求文件
            with open(code_dir / "requirements.txt", 'w', encoding='utf-8') as f:
                f.write(code_result['implementation']['requirements'])
            
            # 保存使用示例
            with open(code_dir / "usage_example.py", 'w', encoding='utf-8') as f:
                f.write(code_result['implementation']['usage_example'])
            
            # 创建README
            with open(code_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(f"# {code_result['title']} Python Implementation\n\n")
                f.write("## 安装\n\n")
                f.write("```bash\npip install -r requirements.txt\n```\n\n")
                f.write("## 使用示例\n\n")
                f.write("```python\n")
                f.write(code_result['implementation']['usage_example'])
                f.write("\n```\n") 