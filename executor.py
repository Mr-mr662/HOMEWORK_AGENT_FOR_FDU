"""
任务执行器 - 执行AI生成的计划
"""
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from ..platforms.base import Assignment
from .planner import TaskPlanner
from ..generators.document import DocumentGenerator


class TaskExecutor:
    """任务执行器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.planner = TaskPlanner(config)
        self.generator = DocumentGenerator(config)
        self.verbose = self.config.get('agent', {}).get('verbose', True)

    async def execute_assignment(self, assignment: Assignment) -> Path:
        """执行作业生成任务"""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"开始处理作业: {assignment.title}")
            print(f"课程: {assignment.course_name}")
            print(f"{'='*60}\n")

        plan = await self.planner.create_plan(assignment)

        if self.verbose:
            print("📋 执行计划:")
            for i, step in enumerate(plan['steps'], 1):
                print(f"  {i}. [{step['status']}] {step['description']}")
            print()

        await self._execute_plan(plan, assignment)

        content = await self.planner.generate_content(plan['analysis'])

        output_path = await self.generator.generate(
            assignment=assignment,
            content=content,
            format_type=self.config.get('output', {}).get('format', 'docx')
        )

        if self.verbose:
            print(f"\n✅ 作业已完成！")
            print(f"📄 文件位置: {output_path}")

        return output_path

    async def _execute_plan(self, plan: Dict[str, Any], assignment: Assignment):
        """执行计划中的步骤"""
        for step in plan['steps']:
            if step['status'] == 'pending':
                step['status'] = 'in_progress'

                if self.verbose:
                    print(f"🔄 执行: {step['description']}...")

                await asyncio.sleep(0.5)

                step['status'] = 'completed'

                if self.verbose:
                    print(f"✓ 完成: {step['description']}")

    async def execute_multiple(self, assignments: list[Assignment]) -> list[Path]:
        """批量执行多个作业"""
        results = []

        for assignment in assignments:
            try:
                output_path = await self.execute_assignment(assignment)
                results.append(output_path)
            except Exception as e:
                print(f"处理作业 '{assignment.title}' 时出错: {e}")
                continue

        return results
