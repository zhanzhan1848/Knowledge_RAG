#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge RAG 项目 - 全故事验证工具

功能：
- 验证所有用户故事的草稿质量
- 基于故事草稿检查清单进行评估
- 生成综合验证报告
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class StoryDraftValidator:
    """故事草稿验证器 - 基于BMAD故事草稿检查清单"""

    def __init__(self, stories_dir: str):
        self.stories_dir = Path(stories_dir)
        self.validation_criteria = {
            "goal_context_clarity": "目标和上下文清晰度",
            "technical_guidance": "技术实施指导",
            "reference_effectiveness": "引用有效性",
            "self_containment": "自包含性评估",
            "testing_guidance": "测试指导",
        }

    def validate_story(self, story_path: Path) -> Dict[str, Any]:
        """验证单个用户故事"""
        try:
            with open(story_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return {"error": f"故事文件未找到: {story_path}"}

        # 验证结果
        validation_result = {
            "story_path": str(story_path),
            "story_name": story_path.name,
            "validation_details": {},
            "issues": [],
            "overall_status": "READY",
            "clarity_score": 10,
        }

        # 1. 目标和上下文清晰度
        goal_clarity = self._check_goal_context_clarity(content)
        validation_result["validation_details"]["goal_context_clarity"] = goal_clarity

        # 2. 技术实施指导
        tech_guidance = self._check_technical_guidance(content)
        validation_result["validation_details"]["technical_guidance"] = tech_guidance

        # 3. 引用有效性
        reference_effectiveness = self._check_reference_effectiveness(content)
        validation_result["validation_details"][
            "reference_effectiveness"
        ] = reference_effectiveness

        # 4. 自包含性评估
        self_containment = self._check_self_containment(content)
        validation_result["validation_details"]["self_containment"] = self_containment

        # 5. 测试指导
        testing_guidance = self._check_testing_guidance(content)
        validation_result["validation_details"]["testing_guidance"] = testing_guidance

        # 计算总体评分和状态
        self._calculate_overall_assessment(validation_result)

        return validation_result

    def _check_goal_context_clarity(self, content: str) -> Dict[str, Any]:
        """检查目标和上下文清晰度"""
        issues = []
        score = 10

        # 检查故事格式
        if not all(
            phrase in content for phrase in ["**As a**", "**I want**", "**so that**"]
        ):
            issues.append("缺少标准的用户故事格式 (As a... I want... so that...)")
            score -= 3

        # 检查业务价值说明
        if "so that" in content:
            so_that_section = content.split("so that")[1].split("\n")[0]
            if len(so_that_section.strip()) < 20:
                issues.append("业务价值说明过于简短")
                score -= 2

        # 检查Epic关联
        if "Epic" not in content and "epic" not in content:
            issues.append("未明确说明与Epic的关联")
            score -= 1

        # 检查依赖关系
        if (
            "依赖" not in content
            and "depends" not in content.lower()
            and "requires" not in content.lower()
        ):
            # 对于非基础故事，应该有依赖说明
            story_id = re.search(r"Story (\d+\.\d+)", content)
            if story_id and not story_id.group(1).startswith("1."):
                issues.append("未明确说明对其他故事的依赖关系")
                score -= 1

        status = "PASS" if score >= 8 else "PARTIAL" if score >= 6 else "FAIL"

        return {"status": status, "score": max(1, score), "issues": issues}

    def _check_technical_guidance(self, content: str) -> Dict[str, Any]:
        """检查技术实施指导"""
        issues = []
        score = 10

        # 检查技术栈说明
        tech_keywords = [
            "Python",
            "FastAPI",
            "Docker",
            "PostgreSQL",
            "Redis",
            "Neo4j",
            "Weaviate",
        ]
        if not any(keyword in content for keyword in tech_keywords):
            issues.append("缺少具体的技术栈说明")
            score -= 2

        # 检查文件/组件说明
        if (
            "文件" not in content
            and "组件" not in content
            and "service" not in content.lower()
        ):
            issues.append("未说明需要创建或修改的关键文件/组件")
            score -= 2

        # 检查API接口说明
        if "API" in content or "api" in content:
            if "接口" not in content and "endpoint" not in content.lower():
                issues.append("提到API但未详细说明接口设计")
                score -= 1

        # 检查数据模型
        if "数据" in content or "model" in content.lower():
            if "模型" not in content and "schema" not in content.lower():
                issues.append("提到数据但未说明数据模型或结构")
                score -= 1

        # 检查配置说明
        if (
            "配置" not in content
            and "config" not in content.lower()
            and "环境变量" not in content
        ):
            issues.append("缺少配置或环境变量说明")
            score -= 1

        status = "PASS" if score >= 8 else "PARTIAL" if score >= 6 else "FAIL"

        return {"status": status, "score": max(1, score), "issues": issues}

    def _check_reference_effectiveness(self, content: str) -> Dict[str, Any]:
        """检查引用有效性"""
        issues = []
        score = 10

        # 检查文档引用
        doc_references = re.findall(r"docs/[\w\-/]+\.md", content)
        if not doc_references:
            issues.append("缺少对相关文档的引用")
            score -= 2
        else:
            # 检查引用格式
            for ref in doc_references:
                if "#" not in ref:
                    issues.append(f"引用 {ref} 未指向具体章节")
                    score -= 1

        # 检查架构文档引用
        if "architecture.md" not in content:
            issues.append("未引用架构文档")
            score -= 1

        # 检查前置故事引用
        story_refs = re.findall(r"Story \d+\.\d+", content)
        if len(story_refs) > 1:  # 除了自己
            # 应该有对前置故事的说明
            if "完成" not in content and "实现" not in content:
                issues.append("引用了其他故事但未说明依赖关系")
                score -= 1

        status = "PASS" if score >= 8 else "PARTIAL" if score >= 6 else "FAIL"

        return {"status": status, "score": max(1, score), "issues": issues}

    def _check_self_containment(self, content: str) -> Dict[str, Any]:
        """检查自包含性"""
        issues = []
        score = 10

        # 检查核心信息完整性
        required_sections = [
            "## Story",
            "## Acceptance Criteria",
            "## Tasks",
            "## Dev Notes",
        ]
        missing_sections = [
            section for section in required_sections if section not in content
        ]
        if missing_sections:
            issues.append(f"缺少必需章节: {', '.join(missing_sections)}")
            score -= len(missing_sections) * 2

        # 检查验收标准数量
        ac_lines = [
            line
            for line in content.split("\n")
            if line.strip() and re.match(r"^\d+\.", line.strip())
        ]
        if len(ac_lines) < 3:
            issues.append("验收标准数量不足，建议至少3个")
            score -= 2

        # 检查任务分解
        task_lines = [
            line for line in content.split("\n") if line.strip().startswith("- [ ]")
        ]
        if len(task_lines) < 3:
            issues.append("任务分解不够详细，建议至少3个主要任务")
            score -= 1

        # 检查开发注释
        if "## Dev Notes" in content:
            dev_notes_section = content.split("## Dev Notes")[1].split("##")[0]
            if len(dev_notes_section.strip()) < 100:
                issues.append("开发注释过于简短，缺少技术实施细节")
                score -= 1

        # 检查术语解释
        technical_terms = ["GraphRAG", "向量化", "知识图谱", "实体提取", "语义检索"]
        used_terms = [term for term in technical_terms if term in content]
        if used_terms and "说明" not in content and "解释" not in content:
            issues.append("使用了专业术语但缺少解释说明")
            score -= 1

        status = "PASS" if score >= 8 else "PARTIAL" if score >= 6 else "FAIL"

        return {"status": status, "score": max(1, score), "issues": issues}

    def _check_testing_guidance(self, content: str) -> Dict[str, Any]:
        """检查测试指导"""
        issues = []
        score = 10

        # 检查测试章节
        if "Testing" not in content and "测试" not in content:
            issues.append("缺少测试指导章节")
            score -= 3

        # 检查测试类型说明
        test_types = [
            "单元测试",
            "集成测试",
            "端到端测试",
            "unit",
            "integration",
            "e2e",
        ]
        if not any(test_type in content.lower() for test_type in test_types):
            issues.append("未说明测试类型和策略")
            score -= 2

        # 检查测试框架
        test_frameworks = ["pytest", "unittest", "testcontainers", "locust"]
        if not any(framework in content.lower() for framework in test_frameworks):
            issues.append("未指定测试框架")
            score -= 1

        # 检查测试场景
        if "场景" not in content and "scenario" not in content.lower():
            issues.append("缺少具体的测试场景说明")
            score -= 1

        # 检查成功标准
        if "覆盖率" not in content and "coverage" not in content.lower():
            issues.append("未说明测试覆盖率要求")
            score -= 1

        status = "PASS" if score >= 8 else "PARTIAL" if score >= 6 else "FAIL"

        return {"status": status, "score": max(1, score), "issues": issues}

    def _calculate_overall_assessment(self, validation_result: Dict[str, Any]):
        """计算总体评估"""
        details = validation_result["validation_details"]

        # 计算平均分
        total_score = sum(detail["score"] for detail in details.values())
        avg_score = total_score / len(details)

        # 收集所有问题
        all_issues = []
        for detail in details.values():
            all_issues.extend(detail["issues"])

        # 确定状态
        fail_count = sum(1 for detail in details.values() if detail["status"] == "FAIL")
        partial_count = sum(
            1 for detail in details.values() if detail["status"] == "PARTIAL"
        )

        if fail_count > 0:
            overall_status = "BLOCKED"
        elif partial_count > 2:
            overall_status = "NEEDS REVISION"
        elif len(all_issues) > 5:
            overall_status = "NEEDS REVISION"
        else:
            overall_status = "READY"

        validation_result["overall_status"] = overall_status
        validation_result["clarity_score"] = round(avg_score, 1)
        validation_result["issues"] = all_issues

    def validate_all_stories(self) -> List[Dict[str, Any]]:
        """验证所有故事"""
        story_files = sorted(self.stories_dir.glob("*.md"))
        results = []

        print(f"\n📋 开始验证 {len(story_files)} 个用户故事...")
        print("=" * 60)

        for story_file in story_files:
            print(f"\n🔍 验证故事: {story_file.name}")
            result = self.validate_story(story_file)
            results.append(result)

            # 显示验证结果
            if "error" in result:
                print(f"  ❌ 错误: {result['error']}")
            else:
                status_icon = {
                    "READY": "✅",
                    "NEEDS REVISION": "⚠️",
                    "BLOCKED": "🚫",
                }.get(result["overall_status"], "❓")

                print(f"  {status_icon} 状态: {result['overall_status']}")
                print(f"  📊 评分: {result['clarity_score']}/10")

                if result["issues"]:
                    print(f"  ⚠️  问题数量: {len(result['issues'])}")
                    for issue in result["issues"][:3]:  # 只显示前3个问题
                        print(f"     - {issue}")
                    if len(result["issues"]) > 3:
                        print(f"     ... 还有 {len(result['issues']) - 3} 个问题")

        return results

    def generate_comprehensive_report(
        self, validation_results: List[Dict[str, Any]]
    ) -> str:
        """生成综合验证报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 统计数据
        total_stories = len([r for r in validation_results if "error" not in r])
        ready_count = sum(
            1 for r in validation_results if r.get("overall_status") == "READY"
        )
        needs_revision_count = sum(
            1 for r in validation_results if r.get("overall_status") == "NEEDS REVISION"
        )
        blocked_count = sum(
            1 for r in validation_results if r.get("overall_status") == "BLOCKED"
        )

        avg_score = sum(
            r.get("clarity_score", 0) for r in validation_results if "error" not in r
        ) / max(total_stories, 1)

        report = f"""# Knowledge RAG 项目 - 全故事草稿验证报告

**验证时间**: {timestamp}  
**验证工具**: BMAD 故事草稿检查清单  
**验证范围**: 全部用户故事  
**验证故事数量**: {total_stories}

---

## 📊 验证摘要

### 总体状态分布
- ✅ **准备就绪**: {ready_count} ({ready_count/max(total_stories,1)*100:.1f}%)
- ⚠️ **需要修订**: {needs_revision_count} ({needs_revision_count/max(total_stories,1)*100:.1f}%)
- 🚫 **阻塞状态**: {blocked_count} ({blocked_count/max(total_stories,1)*100:.1f}%)

### 质量指标
- **平均清晰度评分**: {avg_score:.1f}/10
- **验证通过率**: {ready_count/max(total_stories,1)*100:.1f}%
- **需要改进率**: {(needs_revision_count + blocked_count)/max(total_stories,1)*100:.1f}%

---

## 📋 详细验证结果

"""

        # 按Epic分组显示结果
        epics = {}
        for result in validation_results:
            if "error" in result:
                continue

            story_name = result["story_name"]
            epic_id = story_name.split(".")[0]
            if epic_id not in epics:
                epics[epic_id] = []
            epics[epic_id].append(result)

        epic_names = {
            "1": "Epic 1: 基础架构和核心服务建设",
            "2": "Epic 2: 智能检索和知识图谱构建",
            "3": "Epic 3: GraphRAG和智能问答系统",
            "4": "Epic 4: API接口和服务集成",
            "5": "Epic 5: 高级功能和个性化服务",
            "6": "Epic 6: 第三方集成和MCP协议实现",
            "7": "Epic 7: 性能优化和系统扩展",
            "8": "Epic 8: 安全加固和合规认证",
        }

        for epic_id in sorted(epics.keys()):
            epic_stories = epics[epic_id]
            epic_name = epic_names.get(epic_id, f"Epic {epic_id}")

            report += f"### {epic_name}\n\n"

            for result in sorted(epic_stories, key=lambda x: x["story_name"]):
                status_icon = {
                    "READY": "✅",
                    "NEEDS REVISION": "⚠️",
                    "BLOCKED": "🚫",
                }.get(result["overall_status"], "❓")

                report += f"#### {status_icon} {result['story_name']}\n\n"
                report += f"**状态**: {result['overall_status']}  \n"
                report += f"**清晰度评分**: {result['clarity_score']}/10  \n"

                # 详细验证结果
                report += f"\n**验证详情**:\n"
                for criteria, details in result["validation_details"].items():
                    criteria_name = self.validation_criteria[criteria]
                    status_icon_detail = {
                        "PASS": "✅",
                        "PARTIAL": "⚠️",
                        "FAIL": "❌",
                    }.get(details["status"], "❓")
                    report += f"- {status_icon_detail} {criteria_name}: {details['status']} ({details['score']}/10)\n"

                if result["issues"]:
                    report += f"\n**需要改进的问题**:\n"
                    for issue in result["issues"]:
                        report += f"- {issue}\n"

                report += "\n---\n\n"

        # 添加改进建议
        report += self._generate_improvement_recommendations(validation_results)

        return report

    def _generate_improvement_recommendations(
        self, validation_results: List[Dict[str, Any]]
    ) -> str:
        """生成改进建议"""
        # 统计常见问题
        issue_counts = {}
        for result in validation_results:
            if "error" in result:
                continue
            for issue in result.get("issues", []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        # 获取最常见的问题
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        recommendations = """## 🎯 改进建议

### 常见问题分析

"""

        for issue, count in common_issues:
            recommendations += f"- **{issue}** (影响 {count} 个故事)\n"

        recommendations += """

### 优先改进建议

1. **加强技术实施指导**
   - 明确指定需要创建或修改的关键文件和组件
   - 详细说明API接口设计和数据模型
   - 提供具体的配置和环境变量说明

2. **完善测试指导**
   - 明确测试类型和策略
   - 指定测试框架和工具
   - 定义测试覆盖率要求和成功标准

3. **优化引用效果**
   - 引用文档时指向具体章节
   - 在故事中总结关键信息，减少对外部文档的依赖
   - 明确说明与其他故事的依赖关系

4. **增强自包含性**
   - 确保所有必需章节完整
   - 提供充分的验收标准（建议至少3个）
   - 详细的任务分解和开发注释

### 质量保证建议

- **建立故事审查流程**: 在实施前进行同行评审
- **定期质量检查**: 每个Sprint结束后回顾故事质量
- **模板标准化**: 基于高质量故事创建标准模板
- **培训和指导**: 为故事编写者提供最佳实践培训

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**验证工具版本**: BMAD Story Draft Checklist v1.0  
**下次建议验证**: 故事更新后或每周定期验证
"""

        return recommendations


def main():
    """主函数"""
    print("Knowledge RAG 项目 - 全故事草稿验证工具")
    print("=" * 50)

    # 初始化验证器
    stories_dir = "/Users/zhanyuanwei/Desktop/Knowledge_RAG/docs/stories"
    validator = StoryDraftValidator(stories_dir)

    # 验证所有故事
    results = validator.validate_all_stories()

    # 生成报告
    print("\n📝 生成综合验证报告...")
    report = validator.generate_comprehensive_report(results)

    # 保存报告
    report_path = "/Users/zhanyuanwei/Desktop/Knowledge_RAG/docs/comprehensive-story-draft-validation-report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ 验证报告已保存: {report_path}")

    # 显示统计信息
    total_stories = len([r for r in results if "error" not in r])
    ready_count = sum(1 for r in results if r.get("overall_status") == "READY")
    needs_revision_count = sum(
        1 for r in results if r.get("overall_status") == "NEEDS REVISION"
    )
    blocked_count = sum(1 for r in results if r.get("overall_status") == "BLOCKED")

    print("\n📊 验证统计:")
    print(f"   总故事数: {total_stories}")
    print(f"   准备就绪: {ready_count} ({ready_count/max(total_stories,1)*100:.1f}%)")
    print(
        f"   需要修订: {needs_revision_count} ({needs_revision_count/max(total_stories,1)*100:.1f}%)"
    )
    print(
        f"   阻塞状态: {blocked_count} ({blocked_count/max(total_stories,1)*100:.1f}%)"
    )

    if ready_count == total_stories:
        print("\n🎉 所有故事验证通过，可以开始实施！")
    elif needs_revision_count > 0:
        print(f"\n⚠️  有 {needs_revision_count} 个故事需要修订")
    if blocked_count > 0:
        print(f"\n🚫 有 {blocked_count} 个故事处于阻塞状态，需要立即处理")


if __name__ == "__main__":
    main()
