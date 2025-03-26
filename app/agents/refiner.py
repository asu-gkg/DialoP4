import os
import json
import dspy
from pathlib import Path
from .base_agent import BaseAgent

class RefinementPlanner(dspy.Signature):
    """为代码优化制定计划"""
    code = dspy.InputField(desc="原始代码")
    evaluation = dspy.InputField(desc="评估结果和改进建议")
    user_feedback = dspy.InputField(desc="用户反馈（如果有）")
    refinement_plan = dspy.OutputField(desc="详细的优化计划，包括具体要修改的部分和优化方向")
    prioritized_changes = dspy.OutputField(desc="按优先级排序的变更列表")

class CodeRefiner(dspy.Signature):
    """执行代码优化"""
    original_code = dspy.InputField(desc="原始代码")
    refinement_plan = dspy.InputField(desc="优化计划")
    prioritized_changes = dspy.InputField(desc="优先级变更列表")
    refined_code = dspy.OutputField(desc="优化后的代码")
    changelog = dspy.OutputField(desc="详细的变更日志，说明做了哪些修改")

class SelfEvaluator(dspy.Signature):
    """评估优化结果"""
    original_code = dspy.InputField(desc="原始代码")
    refined_code = dspy.InputField(desc="优化后的代码")
    refinement_plan = dspy.InputField(desc="优化计划")
    original_evaluation = dspy.InputField(desc="原始评估")
    improvement_assessment = dspy.OutputField(desc="改进评估，包括解决了哪些问题")
    comparison = dspy.OutputField(desc="与原始代码的详细比较")
    remaining_issues = dspy.OutputField(desc="仍然存在的问题")

class Refiner(BaseAgent):
    """迭代优化代码的Agent"""
    
    def __init__(self, config):
        super().__init__(config, name="refiner")
        
        # 初始化DSPy模块
        self.planner = dspy.Predict(RefinementPlanner)
        self.refiner = dspy.Predict(CodeRefiner)
        self.evaluator = dspy.Predict(SelfEvaluator)
        
        # 获取最大迭代次数
        self.max_iterations = int(self.config['agents'].get('refiner', {}).get('max_iterations', 3))
    
    def _load_prompts(self):
        """加载Agent特定的提示模板"""
        self.prompts = {
            "plan_refinement": """
作为一名网络代码优化专家，你需要基于评估结果和反馈制定详细的代码优化计划。
你的计划应:
1. 明确识别需要修改的代码部分
2. 对每个变更提供明确的方向和目标
3. 考虑变更之间的依赖关系
4. 对变更进行优先级排序，先处理最关键的问题
5. 考虑代码结构和架构的整体一致性
            """,
            
            "refine_code": """
根据优化计划对代码进行改进。你应当:
1. 仔细遵循计划中的优先级
2. 保持代码风格一致性
3. 对每个变更添加必要的注释
4. 确保修改不会引入新的问题
5. 记录所有变更，包括修改原因和预期效果
            """,
            
            "evaluate_refinement": """
评估优化后的代码是否达到了预期目标。分析:
1. 原始问题是否得到解决
2. 性能是否提升
3. 代码质量是否改善
4. 是否引入了新问题
5. 与原始评估中指出的问题进行比较

提供客观、全面的评估，指出任何仍需改进的地方。
            """
        }
    
    def process(self, code_result, evaluation_result, user_feedback='', conversation_id=''):
        """
        优化代码实现
        
        Args:
            code_result (dict): 原始代码结果
            evaluation_result (dict): 评估结果
            user_feedback (str): 用户反馈
            conversation_id (str): 会话ID
            
        Returns:
            dict: 优化后的代码结果
        """
        # 提取代码类型和内容
        code_type = code_result.get('code_type', 'python')
        
        # 获取代码内容
        if code_type in ['ns3', 'p4']:
            # 对于NS3和P4，使用完整实现
            original_code = code_result.get('implementation', {}).get('code', '')
        else:  # python
            original_code = code_result.get('implementation', {}).get('code', '')
        
        # 提取评估结果
        evaluation_json = json.dumps(evaluation_result, ensure_ascii=False)
        
        # 初始化迭代历史
        refinement_history = []
        
        # 开始迭代优化
        current_code = original_code
        
        for iteration in range(self.max_iterations):
            # 制定优化计划
            plan_result = self.planner(
                code=current_code,
                evaluation=evaluation_json,
                user_feedback=user_feedback
            )
            
            # 执行代码优化
            refine_result = self.refiner(
                original_code=current_code,
                refinement_plan=plan_result.refinement_plan,
                prioritized_changes=plan_result.prioritized_changes
            )
            
            # 评估优化结果
            evaluate_result = self.evaluator(
                original_code=original_code,
                refined_code=refine_result.refined_code,
                refinement_plan=plan_result.refinement_plan,
                original_evaluation=evaluation_json
            )
            
            # 记录本次迭代
            iteration_record = {
                "iteration": iteration + 1,
                "plan": {
                    "refinement_plan": plan_result.refinement_plan,
                    "prioritized_changes": plan_result.prioritized_changes
                },
                "changes": {
                    "refined_code": refine_result.refined_code,
                    "changelog": refine_result.changelog
                },
                "evaluation": {
                    "improvement_assessment": evaluate_result.improvement_assessment,
                    "comparison": evaluate_result.comparison,
                    "remaining_issues": evaluate_result.remaining_issues
                }
            }
            
            refinement_history.append(iteration_record)
            
            # 更新当前代码
            current_code = refine_result.refined_code
            
            # 如果没有剩余问题或者全部是低优先级问题，提前结束迭代
            remaining_issues = evaluate_result.remaining_issues.lower()
            if "no remaining issues" in remaining_issues or (
                "low priority" in remaining_issues and iteration >= 1):
                break
            
            # 更新用户反馈为空，以避免重复使用
            user_feedback = ''
        
        # 构建最终结果
        refined_code_result = {
            "title": code_result.get('title', ''),
            "code_type": code_type,
            "original_code": original_code,
            "refined_code": current_code,
            "refinement_history": refinement_history
        }
        
        # 保存结果
        result_path = self.save_result(
            result=refined_code_result,
            result_type=f"{code_type}_refined",
            conversation_id=conversation_id
        )
        
        # 将文件路径添加到结果中
        refined_code_result["result_path"] = result_path
        refined_code_result["result_id"] = os.path.basename(result_path).split("_")[1].split(".")[0]
        
        # 保存代码文件
        self._save_refined_code(refined_code_result, code_type, conversation_id)
        
        return refined_code_result
    
    def _save_refined_code(self, refined_result, code_type, conversation_id):
        """
        保存优化后的代码文件
        
        Args:
            refined_result (dict): 优化结果
            code_type (str): 代码类型
            conversation_id (str): 会话ID
        """
        # 创建代码存储路径
        code_dir = Path(self.config['storage']['code_store_path']) / conversation_id / f"{code_type}_refined"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存最终优化代码
        if code_type == 'ns3':
            # 保存NS3代码
            with open(code_dir / "ns3_refined.cc", 'w', encoding='utf-8') as f:
                f.write(refined_result['refined_code'])
                
        elif code_type == 'p4':
            # 保存P4代码
            with open(code_dir / "p4_refined.p4", 'w', encoding='utf-8') as f:
                f.write(refined_result['refined_code'])
                
        else:  # python
            # 保存Python代码
            with open(code_dir / "python_refined.py", 'w', encoding='utf-8') as f:
                f.write(refined_result['refined_code'])
        
        # 保存优化过程文档
        with open(code_dir / "refinement_process.md", 'w', encoding='utf-8') as f:
            f.write(f"# {refined_result.get('title', '代码')}优化过程\n\n")
            
            for i, iteration in enumerate(refined_result['refinement_history']):
                f.write(f"## 迭代 {i+1}\n\n")
                
                f.write("### 优化计划\n\n")
                f.write(f"{iteration['plan']['refinement_plan']}\n\n")
                
                f.write("### 优先变更\n\n")
                changes = iteration['plan']['prioritized_changes']
                if isinstance(changes, str):
                    changes = changes.split('\n')
                for change in changes:
                    if change.strip():
                        f.write(f"- {change.strip()}\n")
                f.write("\n")
                
                f.write("### 变更日志\n\n")
                f.write(f"{iteration['changes']['changelog']}\n\n")
                
                f.write("### 改进评估\n\n")
                f.write(f"{iteration['evaluation']['improvement_assessment']}\n\n")
                
                f.write("### 剩余问题\n\n")
                f.write(f"{iteration['evaluation']['remaining_issues']}\n\n")
                
                if i < len(refined_result['refinement_history']) - 1:
                    f.write("---\n\n")
        
        # 保存差异比较
        with open(code_dir / "code_diff.md", 'w', encoding='utf-8') as f:
            f.write(f"# {refined_result.get('title', '代码')}优化前后对比\n\n")
            f.write("## 优化前\n\n")
            f.write("```\n")
            f.write(refined_result['original_code'])
            f.write("\n```\n\n")
            
            f.write("## 优化后\n\n")
            f.write("```\n")
            f.write(refined_result['refined_code'])
            f.write("\n```\n\n")
            
            if refined_result['refinement_history']:
                last_iteration = refined_result['refinement_history'][-1]
                f.write("## 主要改进\n\n")
                f.write(f"{last_iteration['evaluation']['comparison']}\n\n") 