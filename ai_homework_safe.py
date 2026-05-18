#!/usr/bin/env python3
"""
智能作业助手 - 安全输入版
支持运行时输入敏感信息，保护用户隐私
"""
import asyncio
import os
import re
import json
import getpass
from pathlib import Path
from datetime import datetime, timedelta

os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
os.environ['OPENAI_API_KEY'] = 'ollama'
os.environ['OPENAI_API_BASE'] = 'http://localhost:11434/v1'

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.platforms.canvas import CanvasPlatform
from agent.generators.document import DocumentGenerator
from bs4 import BeautifulSoup


class AIHomeworkAssistant:
    """AI作业助手"""

    def __init__(self, api_key: str = "", model: str = "moonshot-v1-8k"):
        self.model = model
        self.use_kimi = True
        self.api_key = api_key

    async def generate_answer(self, assignment_title: str, assignment_requirements: str, course_name: str) -> str:
        """使用AI生成作业答案"""
        print(f"\n🤖 正在调用{self.model}生成答案...")
        print(f"   作业: {assignment_title[:30]}...")
        print(f"   课程: {course_name}")

        prompt = f"""You are a professional English course assignment assistant. Please write a high-quality assignment answer in English based on the following requirements.

## Assignment Requirements
{assignment_requirements}

## Requirements
1. Write your entire answer in English (English title, English content, everything)
2. Be detailed, professional, and in-depth
3. Word count: 800-1500 words
4. Clear structure with proper paragraphs
5. Use proper academic English
6. Include introduction, body paragraphs, and conclusion

## Assignment Title
{assignment_title}

## Your Answer (Write in English Only)

"""

        try:
            if self.use_kimi and self.api_key:
                answer = await self._call_kimi(prompt)
            else:
                print("   ⚠️  未配置API密钥，使用模板答案...")
                answer = self._generate_template_answer(assignment_title, assignment_requirements, course_name)

            print(f"   ✅ AI答案生成成功！")
            return answer

        except Exception as e:
            print(f"   ⚠️  AI调用失败: {e}")
            print(f"   使用模板答案...")
            return self._generate_template_answer(assignment_title, assignment_requirements, course_name)

    async def _call_kimi(self, prompt: str) -> str:
        """调用Kimi API"""
        import aiohttp
        import ssl

        if not self.api_key:
            raise Exception("未配置API密钥")

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': '你是一个专业的大学课程作业助手，能够根据作业要求生成高质量的答案。'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                'https://api.moonshot.cn/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    raise Exception(f"API错误: {response.status} - {error_text}")

    def _generate_template_answer(self, title: str, requirements: str, course: str) -> str:
        """生成模板答案"""
        return f"""
{course}课程作业

作业标题：{title}

一、作业概述

本作业主要围绕{title}展开，要求学生深入理解课程相关概念，并结合实际进行分析。

二、作业要求分析

{requirements}

三、具体内容

【此处应由AI模型生成详细答案】

由于当前AI模型调用失败，建议您：
1. 手动查看作业要求
2. 根据要求撰写答案
3. 或者配置正确的API密钥后重新运行

四、总结与思考

通过对本作业的分析和完成，我对{course}课程的核心内容有了更深入的理解。
"""

    def extract_assignment_requirements(self, html_content: str) -> str:
        """从HTML中提取作业要求"""
        soup = BeautifulSoup(html_content, 'html.parser')

        requirements = []

        desc_elem = soup.find(['div', 'section'], class_=re.compile(r'description|content|instructions', re.I))
        if desc_elem:
            requirements.append(desc_elem.get_text(strip=True))

        assignment_details = soup.find_all(['div', 'p', 'span'])
        for elem in assignment_details:
            text = elem.get_text(strip=True)
            if len(text) > 50 and text not in requirements:
                requirements.append(text)

        return '\n\n'.join(requirements[:3]) if requirements else "请根据课程要求完成作业"


async def process_homework(assignment_data: dict, platform: CanvasPlatform, assistant: AIHomeworkAssistant, generator: DocumentGenerator):
    """处理单个作业"""
    assignment_id = assignment_data['id']
    course_id = assignment_data['course_id']
    title = assignment_data['title']
    course_name = assignment_data['course_name']

    print(f"\n{'='*80}")
    print(f"📝 处理作业: {title}")
    print(f"   课程: {course_name}")
    print(f"{'='*80}")

    try:
        print(f"\n🔍 正在爬取作业详情...")
        url = f"https://elearning.fudan.edu.cn/courses/{course_id}/assignments/{assignment_id}"
        await platform.page.goto(url, timeout=20000)
        await asyncio.sleep(3)

        html_content = await platform.page.content()

        requirements = assistant.extract_assignment_requirements(html_content)

        if requirements and len(requirements) > 20:
            print(f"   ✅ 已提取作业要求 (约{len(requirements)}字)")
            print(f"   📄 要求预览: {requirements[:100]}...")
        else:
            print(f"   ⚠️  未找到详细要求，使用标题作为提示")
            requirements = title

        print(f"\n🤖 正在生成答案...")
        answer = await assistant.generate_answer(title, requirements, course_name)

        print(f"\n📄 正在生成Word文档...")

        from agent.platforms.base import Assignment

        assignment = Assignment(
            id=assignment_id,
            title=title,
            course_name=course_name,
            course_id=course_id,
            description=requirements,
            due_date=None,
            points_possible=100,
            submission_types=['online_text_entry'],
            instructions=requirements,
            attachments=[]
        )

        content = f"""
{answer}
"""

        output_path = await generator.generate(assignment, content, 'docx')

        print(f"   ✅ 文档已生成: {output_path.name}")
        return True

    except Exception as e:
        print(f"   ❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_user_input():
    """获取用户输入的敏感信息"""
    print("=" * 80)
    print("🎓 智能作业助手 - 安全输入版")
    print("=" * 80)
    print()
    print("🔒 安全提示：所有输入的敏感信息仅在内存中使用，不会保存到文件")
    print()

    config = {}

    print("📧 请输入eLearning登录信息：")
    username = input("   学号: ").strip()
    while not username:
        print("   ❌ 学号不能为空")
        username = input("   学号: ").strip()
    config['username'] = username

    password = getpass.getpass("   密码: ").strip()
    while not password:
        print("   ❌ 密码不能为空")
        password = getpass.getpass("   密码: ").strip()
    config['password'] = password

    print()
    print("🤖 请输入AI配置：")
    api_key = getpass.getpass("   Kimi API密钥: ").strip()
    while not api_key:
        print("   ❌ API密钥不能为空")
        api_key = getpass.getpass("   Kimi API密钥: ").strip()
    config['api_key'] = api_key

    print()
    print("📦 请选择AI模型：")
    print("   1. moonshot-v1-8k (推荐，快速且便宜)")
    print("   2. moonshot-v1-32k (中等上下文)")
    print("   3. moonshot-v1-128k (长文本，较贵)")
    
    model_choice = input("   请输入选择 (1/2/3): ").strip()
    model_map = {
        '1': 'moonshot-v1-8k',
        '2': 'moonshot-v1-32k',
        '3': 'moonshot-v1-128k'
    }
    config['model'] = model_map.get(model_choice, 'moonshot-v1-8k')

    print()
    print("⚙️ 请选择浏览器模式：")
    print("   1. 显示浏览器窗口 (调试模式)")
    print("   2. 后台运行 (静默模式)")
    
    browser_choice = input("   请输入选择 (1/2): ").strip()
    config['headless'] = browser_choice == '2'

    print()
    print("✅ 配置完成！")
    print(f"   学号: {username}")
    print(f"   模型: {config['model']}")
    print(f"   浏览器: {'后台' if config['headless'] else '显示'}")
    print()

    return config


async def main():
    config = get_user_input()

    print("功能说明:")
    print("  1. 自动登录eLearning")
    print("  2. 筛选英语类课程")
    print("  3. 爬取作业要求")
    print(f"  4. 调用{config['model']}生成答案")
    print("  5. 生成Word文档")
    print()

    platform_config = {
        'url': 'https://elearning.fudan.edu.cn',
        'headless': config['headless']
    }

    platform = CanvasPlatform(config['username'], config['password'], platform_config)
    generator = DocumentGenerator(platform_config)
    assistant = AIHomeworkAssistant(api_key=config['api_key'], model=config['model'])

    print("📋 步骤1: 登录...")
    if not await platform.login():
        print("❌ 登录失败！")
        return

    print("✅ 登录成功！\n")

    print("📚 步骤2: 获取课程和作业...")
    courses = await platform.get_courses()

    english_courses = []
    for course in courses:
        course_name_lower = course.name.lower()
        if any(keyword in course_name_lower for keyword in ['english', 'fore', 'writing', 'reading', '英语', '精读', '写作']):
            english_courses.append(course)
            print(f"  ✅ 英语课程: {course.name[:50]}...")

    if not english_courses:
        print("❌ 未找到英语类课程！")
        return

    print(f"\n📝 步骤3: 获取英语课程作业（近一周）...")

    one_week_ago = datetime.now() - timedelta(days=7)
    one_week_later = datetime.now() + timedelta(days=7)

    print(f"   📅 筛选时间范围: {one_week_ago.strftime('%Y-%m-%d')} 至 {one_week_later.strftime('%Y-%m-%d')}")
    print(f"   📅 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    all_assignments = []

    for course in english_courses:
        try:
            url = f"{platform_config['url']}/courses/{course.id}/assignments"
            await platform.page.goto(url, timeout=20000)
            await asyncio.sleep(3)

            assignment_items = await platform.page.query_selector_all('li.assignment, div.assignment, tr.assignment')

            for item in assignment_items:
                try:
                    link = await item.query_selector('a[href*="/assignments/"]')
                    if not link:
                        continue

                    href = await link.get_attribute('href')
                    title = await link.inner_text()

                    if href and '/assignments/' in href and title and len(title.strip()) > 3:
                        match = re.search(r'/assignments/(\d+)', href)
                        if match:
                            assignment_id = match.group(1)

                            within_week = False
                            found_date = None
                            due_date_text = ""

                            due_elements = await item.query_selector_all('span, div, td')
                            for elem in due_elements:
                                text = await elem.inner_text()
                                if any(keyword in text for keyword in ['截止', 'due', '日期', '日', '月', '至', '前', '周']):
                                    due_date_text += text + " "

                            due_date_text = due_date_text.strip()

                            if due_date_text:
                                try:
                                    date_patterns = [
                                        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                                        r'(\d{1,2})/(\d{1,2})/(\d{4})',
                                        r'(\d{4})-(\d{1,2})-(\d{1,2})',
                                        r'(\d{4})/(\d{1,2})/(\d{1,2})',
                                        r'(\d{1,2})月(\d{1,2})日',
                                        r'(\d{1,2})-(\d{1,2})'
                                    ]
                                    for pattern in date_patterns:
                                        date_match = re.search(pattern, due_date_text)
                                        if date_match:
                                            groups = date_match.groups()
                                            if len(groups) == 3:
                                                if len(date_match.group(1)) == 4:
                                                    year, month, day = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                                                else:
                                                    year, month, day = int(date_match.group(3)), int(date_match.group(1)), int(date_match.group(2))
                                                found_date = datetime(year, month, day)
                                            elif len(groups) == 2:
                                                month, day = int(date_match.group(1)), int(date_match.group(2))
                                                year = datetime.now().year
                                                found_date = datetime(year, month, day)
                                            break

                                    if found_date and one_week_ago <= found_date <= one_week_later:
                                        within_week = True
                                except Exception:
                                    pass

                            if within_week:
                                all_assignments.append({
                                    'id': assignment_id,
                                    'title': title.strip(),
                                    'course_name': course.name,
                                    'course_id': course.id
                                })
                                print(f"  ✅ 作业: {title[:40]}...")

                except Exception as e:
                    continue

        except Exception as e:
            print(f"  ⚠️  获取失败")
            continue

    print(f"\n✅ 找到 {len(all_assignments)} 个作业（近一周）\n")

    if len(all_assignments) == 0:
        print("❌ 没有找到作业！")
        return

    print("📦 步骤4: 处理作业（AI生成答案）...")

    Path('./homework_output').mkdir(exist_ok=True)

    success_count = 0
    for i, assignment in enumerate(all_assignments, 1):
        print(f"\n[{i}/{len(all_assignments)}]")
        success = await process_homework(assignment, platform, assistant, generator)
        if success:
            success_count += 1

    print("\n" + "=" * 80)
    print("🎉 作业处理完成！")
    print("=" * 80)
    print(f"\n✅ 成功处理 {success_count}/{len(all_assignments)} 个作业")
    print(f"📁 所有文件已保存到: ./homework_output/")

    print("\n⚠️  重要提醒：")
    print("1. 请打开生成的Word文档查看AI答案")
    print("2. 根据实际情况修改和完善答案")
    print("3. 检查格式和内容是否符合要求")
    print("4. 按时提交到eLearning平台")

    await asyncio.sleep(5)
    await platform.logout()
    print("\n程序结束！")


if __name__ == '__main__':
    asyncio.run(main())