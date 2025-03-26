import os
import json
import dspy
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from .base_agent import BaseAgent

class CodeCorrectness(dspy.Signature):
    """评估代码正确性"""
    paper_analysis = dspy.InputField(desc="论文分析结果")
    code = dspy.InputField(desc="生成的代码")
    code_type = dspy.InputField(desc="代码类型（python、ns3、p4）")
    correctness_score = dspy.OutputField(desc="正确性评分（0-10）")
    correctness_analysis = dspy.OutputField(desc="正确性分析，包括对论文要点的实现程度")
    identified_issues = dspy.OutputField(desc="识别出的问题列表")

class PerformanceEstimator(dspy.Signature):
    """估计代码性能"""
    code = dspy.InputField(desc="生成的代码")
    code_type = dspy.InputField(desc="代码类型")
    paper_evaluation = dspy.InputField(desc="论文中的评估方法和结果")
    performance_estimation = dspy.OutputField(desc="性能估计")
    bottlenecks = dspy.OutputField(desc="可能的性能瓶颈")
    optimization_suggestions = dspy.OutputField(desc="优化建议")

class ImprovementSuggestions(dspy.Signature):
    """提供改进建议"""
    code = dspy.InputField(desc="生成的代码")
    correctness_analysis = dspy.InputField(desc="正确性分析")
    performance_estimation = dspy.InputField(desc="性能估计")
    improvement_areas = dspy.OutputField(desc="需要改进的关键领域")
    specific_suggestions = dspy.OutputField(desc="具体的改进建议")
    priority_ranking = dspy.OutputField(desc="建议的优先级排序")

class Evaluator(BaseAgent):
    """评估代码实现的Agent"""
    
    def __init__(self, config):
        super().__init__(config, name="evaluator")
        
        # 初始化DSPy模块
        self.correctness_evaluator = dspy.Predict(CodeCorrectness)
        self.performance_estimator = dspy.Predict(PerformanceEstimator)
        self.improvement_suggester = dspy.Predict(ImprovementSuggestions)
    
    def _load_prompts(self):
        """加载Agent特定的提示模板"""
        self.prompts = {
            "evaluate_correctness": """
作为一名严格的网络代码审核专家，评估以下代码实现是否正确反映了论文中描述的算法和协议。
你的评估应基于:
1. 所有关键功能是否都已实现
2. 实现是否忠实于论文描述
3. 代码逻辑是否正确
4. 边缘情况是否已处理

对每个问题提供详细说明和改进建议。最后给出0-10分的评分。
            """,
            
            "estimate_performance": """
分析这段代码的潜在性能特性。基于你对类似系统的了解，估计:
1. 计算复杂度
2. 内存使用
3. 可扩展性
4. 并行化潜力
5. 与论文中报告的性能期望的对比

识别潜在的性能瓶颈，并提出优化建议。
            """,
            
            "suggest_improvements": """
基于前面的分析，提出具体的改进建议。
你的建议应:
1. 针对具体的代码段或功能
2. 包含改进的明确方向
3. 考虑正确性和性能的平衡
4. 根据重要性排序，突出最关键的问题

对每个建议提供具体的实施思路。
            """
        }
    
    def process(self, paper_analysis, code_result, conversation_id=''):
        """
        评估代码实现
        
        Args:
            paper_analysis (dict): 论文分析结果
            code_result (dict): 代码生成结果
            conversation_id (str): 会话ID
            
        Returns:
            dict: 评估结果
        """
        # 提取代码类型和代码
        code_type = code_result.get('code_type', 'python')
        
        # 获取代码内容
        if code_type in ['ns3', 'p4']:
            # 对于NS3和P4，使用完整实现
            code = code_result.get('implementation', {}).get('code', '')
        else:  # python
            code = code_result.get('implementation', {}).get('code', '')
        
        # 获取论文中的评估方法和结果
        paper_evaluation = json.dumps(
            paper_analysis.get('analysis', {}).get('evaluation', {}), 
            ensure_ascii=False
        )
        
        # 评估代码正确性
        correctness_result = self.correctness_evaluator(
            paper_analysis=json.dumps(paper_analysis, ensure_ascii=False),
            code=code,
            code_type=code_type
        )
        
        # 估计代码性能
        performance_result = self.performance_estimator(
            code=code,
            code_type=code_type,
            paper_evaluation=paper_evaluation
        )
        
        # 提供改进建议
        improvement_result = self.improvement_suggester(
            code=code,
            correctness_analysis=correctness_result.correctness_analysis,
            performance_estimation=performance_result.performance_estimation
        )
        
        # 构建评估结果
        evaluation_result = {
            "code_type": code_type,
            "correctness": {
                "score": correctness_result.correctness_score,
                "analysis": correctness_result.correctness_analysis,
                "issues": correctness_result.identified_issues
            },
            "performance": {
                "estimation": performance_result.performance_estimation,
                "bottlenecks": performance_result.bottlenecks,
                "optimization": performance_result.optimization_suggestions
            },
            "improvements": {
                "areas": improvement_result.improvement_areas,
                "suggestions": improvement_result.specific_suggestions,
                "priorities": improvement_result.priority_ranking
            }
        }
        
        # 生成可视化评估报告
        report_path = self._generate_evaluation_report(
            evaluation_result, 
            code_result, 
            conversation_id
        )
        
        # 保存评估结果
        result_path = self.save_result(
            result=evaluation_result,
            result_type=f"{code_type}_evaluation",
            conversation_id=conversation_id
        )
        
        # 将文件路径添加到结果中
        evaluation_result["result_path"] = result_path
        evaluation_result["result_id"] = os.path.basename(result_path).split("_")[1].split(".")[0]
        evaluation_result["report_path"] = report_path
        
        return evaluation_result
    
    def _generate_evaluation_report(self, evaluation_result, code_result, conversation_id):
        """
        生成评估报告
        
        Args:
            evaluation_result (dict): 评估结果
            code_result (dict): 代码结果
            conversation_id (str): 会话ID
            
        Returns:
            str: 报告文件路径
        """
        # 创建报告目录
        report_dir = Path(self.config['storage']['evaluation_store_path']) / conversation_id
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建报告文件
        code_type = evaluation_result['code_type']
        report_path = report_dir / f"{code_type}_evaluation_report.md"
        
        # 生成Markdown报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# {code_result.get('title', '代码')}评估报告\n\n")
            
            # 正确性评估
            f.write("## 1. 正确性评估\n\n")
            f.write(f"**评分**: {evaluation_result['correctness']['score']}/10\n\n")
            f.write("### 分析\n\n")
            f.write(f"{evaluation_result['correctness']['analysis']}\n\n")
            f.write("### 发现的问题\n\n")
            issues = evaluation_result['correctness']['issues']
            if isinstance(issues, str):
                issues = issues.split('\n')
            for issue in issues:
                if issue.strip():
                    f.write(f"- {issue.strip()}\n")
            f.write("\n")
            
            # 性能评估
            f.write("## 2. 性能评估\n\n")
            f.write("### 性能估计\n\n")
            f.write(f"{evaluation_result['performance']['estimation']}\n\n")
            f.write("### 性能瓶颈\n\n")
            bottlenecks = evaluation_result['performance']['bottlenecks']
            if isinstance(bottlenecks, str):
                bottlenecks = bottlenecks.split('\n')
            for bottleneck in bottlenecks:
                if bottleneck.strip():
                    f.write(f"- {bottleneck.strip()}\n")
            f.write("\n")
            f.write("### 优化建议\n\n")
            f.write(f"{evaluation_result['performance']['optimization']}\n\n")
            
            # 改进建议
            f.write("## 3. 改进建议\n\n")
            f.write("### 需改进的领域\n\n")
            f.write(f"{evaluation_result['improvements']['areas']}\n\n")
            f.write("### 具体建议\n\n")
            suggestions = evaluation_result['improvements']['suggestions']
            if isinstance(suggestions, str):
                suggestions = suggestions.split('\n')
            for suggestion in suggestions:
                if suggestion.strip():
                    f.write(f"- {suggestion.strip()}\n")
            f.write("\n")
            f.write("### 优先级排序\n\n")
            f.write(f"{evaluation_result['improvements']['priorities']}\n\n")
        
        # 创建可视化
        self._create_visualizations(evaluation_result, report_dir, code_type)
        
        return str(report_path)
    
    def _create_visualizations(self, evaluation_result, report_dir, code_type):
        """
        创建评估可视化
        
        Args:
            evaluation_result (dict): 评估结果
            report_dir (Path): 报告目录
            code_type (str): 代码类型
        """
        try:
            # 创建雷达图
            self._create_radar_chart(evaluation_result, report_dir, code_type)
            
            # 创建问题优先级图
            self._create_priority_chart(evaluation_result, report_dir, code_type)
            
        except Exception as e:
            print(f"创建可视化时出错: {e}")
    
    def _create_radar_chart(self, evaluation_result, report_dir, code_type):
        """创建评估雷达图"""
        # 提取评分
        correctness_score = float(evaluation_result['correctness']['score'])
        
        # 从文本中估计其他评分 (示例实现)
        performance_score = 7.0  # 默认值
        maintainability_score = 8.0  # 默认值
        scalability_score = 7.5  # 默认值
        completeness_score = 8.5  # 默认值
        
        # 创建雷达图
        categories = ['正确性', '性能', '可维护性', '可扩展性', '完整性']
        values = [correctness_score, performance_score, maintainability_score, 
                scalability_score, completeness_score]
        
        # 创建角度
        N = len(categories)
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
        values += values[:1]  # 闭合雷达图
        angles += angles[:1]  # 闭合雷达图
        
        # 绘图
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.plot(angles, values, linewidth=2, linestyle='solid')
        ax.fill(angles, values, alpha=0.25)
        
        # 添加标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['2', '4', '6', '8', '10'])
        ax.set_ylim(0, 10)
        
        # 添加标题
        plt.title(f'{code_type.upper()} 代码质量评估', size=15, y=1.1)
        
        # 保存图表
        plt.tight_layout()
        plt.savefig(report_dir / f"{code_type}_quality_radar.png")
        plt.close()
    
    def _create_priority_chart(self, evaluation_result, report_dir, code_type):
        """创建问题优先级图"""
        # 提取改进建议（示例实现）
        priorities = evaluation_result['improvements']['priorities']
        if isinstance(priorities, str):
            # 简单解析文本
            priorities_list = [p.strip() for p in priorities.split('\n') if p.strip()]
            
            # 示例数据
            priority_data = {
                '高优先级': 3,
                '中优先级': 2,
                '低优先级': 1
            }
        else:
            # 假设priorities是结构化数据
            priority_data = priorities
        
        # 创建条形图
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(
            priority_data.keys(),
            priority_data.values(),
            color=['#ff6b6b', '#feca57', '#1dd1a1']
        )
        
        # 添加标签
        ax.set_xlabel('优先级')
        ax.set_ylabel('问题数量')
        ax.set_title(f'{code_type.upper()} 代码问题优先级分布')
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'{height}',
                ha='center', va='bottom'
            )
        
        # 保存图表
        plt.tight_layout()
        plt.savefig(report_dir / f"{code_type}_issues_priority.png")
        plt.close() 