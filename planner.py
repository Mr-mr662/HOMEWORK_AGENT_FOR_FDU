"""
AI任务规划器 - 使用内置AI能力进行作业分析和内容生成
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class TaskPlanner:
    """任务规划器 - 使用内置AI生成作业内容"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.ai_config = self.config.get('ai', {})

    async def analyze_assignment(self, assignment: Any) -> Dict[str, Any]:
        """分析作业要求"""
        analysis = {
            'title': assignment.title,
            'course': assignment.course_name,
            'requirements': self._extract_requirements(assignment.description),
            'key_topics': self._identify_topics(assignment.description),
            'format_requirements': self._parse_format(assignment.instructions),
            'estimated_length': self._estimate_length(assignment),
            'difficulty': 'medium'
        }
        return analysis

    def _extract_requirements(self, description: str) -> List[str]:
        """提取作业要求"""
        requirements = []
        lines = description.split('\n')

        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in ['要求', '需要', '必须', '应当', '应该']):
                requirements.append(line)

        if not requirements:
            requirements = [f"完成{self._count_words(description)}字的分析"]

        return requirements

    def _identify_topics(self, description: str) -> List[str]:
        """识别主题关键词"""
        import re
        words = re.findall(r'[\u4e00-\u9fff]+', description)
        keywords = [w for w in words if len(w) >= 2]
        return list(set(keywords))[:10]

    def _parse_format(self, instructions: str) -> Dict[str, Any]:
        """解析格式要求"""
        format_req = {
            'has_title': True,
            'has_abstract': '摘要' in instructions,
            'has_conclusion': '结论' in instructions or '总结' in instructions,
            'min_words': 500,
            'style': 'academic'
        }

        if '字数' in instructions or '词数' in instructions:
            import re
            match = re.search(r'(\d+)\s*[字词]', instructions)
            if match:
                format_req['min_words'] = int(match.group(1))

        return format_req

    def _estimate_length(self, assignment: Any) -> int:
        """估算作业长度"""
        if assignment.points_possible:
            return int(assignment.points_possible * 50)
        return 1000

    def _count_words(self, text: str) -> int:
        """统计字数"""
        import re
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        english = len(re.findall(r'[a-zA-Z]+', text))
        return chinese + english

    async def generate_content(self, analysis: Dict[str, Any], prompt: str = "") -> str:
        """使用AI生成作业内容

        注意：这里调用内置AI能力进行内容生成
        在实际实现中，可以接入不同的AI服务
        """
        content = f"""
{analysis['title']}

课程：{analysis['course']}

一、引言

{analysis['course']}课程作业，主题围绕{', '.join(analysis['key_topics'][:3])}展开。

二、主要内容

"""
        for i, topic in enumerate(analysis['key_topics'][:5], 1):
            content += f"\n{i}. {topic}\n"
            content += f"   关于{topic}的分析和讨论...\n"

        if analysis['format_requirements'].get('has_abstract'):
            content += "\n三、摘要\n"
            content += f"本文对{', '.join(analysis['key_topics'][:3])}进行了深入分析和探讨。\n"

        content += "\n四、分析与讨论\n"
        for req in analysis['requirements'][:3]:
            content += f"\n{req}\n"
            content += "此处展开详细论述...\n"

        content += "\n五、结论\n"
        content += "通过对以上内容的分析，得出以下结论：\n"
        content += "1. 主要发现...\n"
        content += "2. 实践意义...\n"
        content += "3. 进一步研究方向...\n"

        return content

    async def create_plan(self, assignment: Any) -> Dict[str, Any]:
        """创建作业完成计划"""
        analysis = await self.analyze_assignment(assignment)

        plan = {
            'steps': [
                {'action': 'analyze', 'description': '分析作业要求', 'status': 'completed'},
                {'action': 'research', 'description': '收集相关资料', 'status': 'pending'},
                {'action': 'outline', 'description': '构建文章大纲', 'status': 'pending'},
                {'action': 'write', 'description': '撰写正文内容', 'status': 'pending'},
                {'action': 'review', 'description': '检查和完善', 'status': 'pending'},
                {'action': 'export', 'description': '导出为Word文档', 'status': 'pending'}
            ],
            'estimated_time': '15-30分钟',
            'output_format': 'docx',
            'analysis': analysis
        }

        return plan
