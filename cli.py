"""
命令行界面 - 完整版本
"""
import asyncio
import re
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from .config import ConfigManager
from .platforms import CanvasPlatform, ChaoxingPlatform
from .agent.executor import TaskExecutor

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """智能作业助手 - 自动完成Canvas和超星学习通作业"""
    pass


@cli.command()
@click.option('--config', type=click.Path(), help='配置文件路径')
def setup(config):
    """交互式配置"""
    config_manager = ConfigManager(config)
    config_manager.update_from_interactive()


@cli.command()
@click.option('--config', type=click.Path(), help='配置文件路径')
@click.option('--platform', type=click.Choice(['canvas', 'chaoxing', 'all']), default='all',
              help='选择平台')
@click.option('--course', type=str, help='指定课程ID')
def list_assignments(config, platform, course):
    """列出所有作业"""
    asyncio.run(_list_assignments(config, platform, course))


async def _list_assignments(config_path: Optional[str], platform: str, course: Optional[str]):
    """列出作业的异步实现"""
    console.print("\n📋 正在获取作业列表...\n", style="cyan")

    config_manager = ConfigManager(config_path)
    config_obj = config_manager.get_config()

    assignments = []

    if platform in ['canvas', 'all']:
        if config_obj.canvas.username and config_obj.canvas.password:
            console.print("🌐 正在登录Canvas...", style="yellow")

            canvas_config = {
                'url': config_obj.canvas.url,
                'headless': config_obj.canvas.headless
            }

            canvas = CanvasPlatform(
                config_obj.canvas.username,
                config_obj.canvas.password,
                canvas_config
            )

            try:
                if await canvas.login():
                    console.print("✅ Canvas登录成功\n", style="green")

                    console.print("📚 正在获取课程列表...", style="yellow")
                    courses = await canvas.get_courses()

                    if courses:
                        console.print(f"✅ 找到 {len(courses)} 门课程\n", style="green")

                        console.print("📝 正在获取作业列表...\n", style="yellow")
                        canvas_assignments = await canvas.get_assignments(course)

                        if canvas_assignments:
                            console.print(f"✅ 找到 {len(canvas_assignments)} 个作业\n", style="green")
                            assignments.extend(canvas_assignments)
                        else:
                            console.print("⚠️ 未找到作业\n", style="yellow")

                    else:
                        console.print("❌ 未找到课程\n", style="red")

                else:
                    console.print("❌ Canvas登录失败\n", style="red")

            except Exception as e:
                console.print(f"❌ Canvas错误: {e}\n", style="red")
                import traceback
                traceback.print_exc()
            finally:
                await canvas.logout()

    if platform in ['chaoxing', 'all']:
        if config_obj.chaoxing.username and config_obj.chaoxing.password:
            console.print("🌐 正在登录超星学习通...", style="yellow")

            chaoxing_config = {
                'url': config_obj.chaoxing.url,
                'headless': False
            }

            chaoxing = ChaoxingPlatform(
                config_obj.chaoxing.username,
                config_obj.chaoxing.password,
                chaoxing_config
            )

            try:
                if await chaoxing.login():
                    console.print("✅ 超星学习通登录成功\n", style="green")

                    chaoxing_assignments = await chaoxing.get_assignments(course)

                    if chaoxing_assignments:
                        console.print(f"✅ 找到 {len(chaoxing_assignments)} 个作业\n", style="green")
                        assignments.extend(chaoxing_assignments)
                    else:
                        console.print("⚠️ 未找到作业\n", style="yellow")

                else:
                    console.print("❌ 超星学习通登录失败\n", style="red")

            except Exception as e:
                console.print(f"❌ 超星学习通错误: {e}\n", style="red")
            finally:
                await chaoxing.logout()

    if assignments:
        _display_assignments(assignments)
    else:
        console.print("\n⚠️  未找到任何作业", style="yellow")
        console.print("请检查：\n")
        console.print("  1. 账号密码是否正确")
        console.print("  2. 网络连接是否正常")
        console.print("  3. 尝试运行: python diagnose_login.py\n")


def _display_assignments(assignments):
    """显示作业列表"""
    console.print("\n" + "=" * 80)
    console.print("📋 作业列表", style="bold cyan")
    console.print("=" * 80 + "\n")

    table = Table(title="")
    table.add_column("序号", style="cyan", no_wrap=True, width=5)
    table.add_column("课程", style="magenta", width=25)
    table.add_column("作业标题", style="green", width=35)
    table.add_column("截止日期", style="yellow", width=15)

    for i, assignment in enumerate(assignments, 1):
        due_date = assignment.due_date.strftime('%Y-%m-%d %H:%M') if assignment.due_date else '未设置'
        table.add_row(
            str(i),
            assignment.course_name[:25] if assignment.course_name else '未知',
            assignment.title[:35] if assignment.title else '未知',
            due_date
        )

    console.print(table)
    console.print(f"\n✅ 共找到 {len(assignments)} 个作业\n", style="bold green")


@cli.command()
@click.option('--config', type=click.Path(), help='配置文件路径')
def list_english_assignments(config):
    """列出英语类作业"""
    asyncio.run(_list_english_assignments(config))


async def _list_english_assignments(config_path: Optional[str]):
    """列出英语作业的异步实现"""
    console.print("\n📋 正在获取英语作业列表...\n", style="cyan")
    console.print("🔍 筛选条件：", style="yellow")
    console.print("  • 英语相关课程（英语精读、英语写作等）", style="yellow")
    console.print("  • 所有英语作业\n", style="yellow")

    config_manager = ConfigManager(config_path)
    config_obj = config_manager.get_config()

    english_courses = []
    english_assignments = []

    if config_obj.canvas.username and config_obj.canvas.password:
        console.print("🌐 正在登录Canvas...", style="yellow")

        canvas_config = {
            'url': config_obj.canvas.url,
            'headless': config_obj.canvas.headless
        }

        canvas = CanvasPlatform(
            config_obj.canvas.username,
            config_obj.canvas.password,
            canvas_config
        )

        try:
            if await canvas.login():
                console.print("✅ Canvas登录成功\n", style="green")

                console.print("📚 正在获取课程列表...", style="yellow")
                courses = await canvas.get_courses()

                if courses:
                    console.print(f"✅ 找到 {len(courses)} 门课程\n", style="green")

                    english_keywords = ['english', 'fore', '英语', 'writing', '写作', 'reading', '精读']

                    console.print("🔍 正在筛选英语类课程...\n", style="yellow")

                    for course in courses:
                        course_name_lower = course.name.lower()
                        if any(keyword.lower() in course_name_lower for keyword in english_keywords):
                            english_courses.append(course)
                            console.print(f"  ✅ 英语课程: {course.name[:50]}", style="green")

                    if not english_courses:
                        console.print("\n❌ 未找到英语类课程\n", style="red")
                        return

                    console.print(f"\n✅ 找到 {len(english_courses)} 门英语课程\n", style="green")

                    for course in english_courses:
                        console.print(f"\n📝 获取 [{course.name[:30]}...] 的作业...", style="yellow")

                        try:
                            url = f"{canvas_config['url']}/courses/{course.id}/assignments"
                            await canvas.page.goto(url, timeout=30000)
                            await asyncio.sleep(5)

                            assignment_links = await canvas.page.query_selector_all('a[href*="/assignments/"]')

                            for link in assignment_links:
                                try:
                                    href = await link.get_attribute('href')
                                    title = await link.inner_text()

                                    if href and '/assignments/' in href and title and len(title.strip()) > 3:
                                        match = re.search(r'/assignments/(\d+)', href)
                                        if match:
                                            assignment_id = match.group(1)

                                            english_assignments.append({
                                                'id': assignment_id,
                                                'title': title.strip(),
                                                'course_name': course.name,
                                                'course_id': course.id
                                            })
                                            console.print(f"    ✅ {title[:40]}", style="cyan")

                                except Exception as e:
                                    continue

                        except Exception as e:
                            console.print(f"    ⚠️  获取失败\n", style="yellow")
                            continue

                else:
                    console.print("❌ 未找到课程\n", style="red")

            else:
                console.print("❌ Canvas登录失败\n", style="red")

        except Exception as e:
            console.print(f"❌ Canvas错误: {e}\n", style="red")
            import traceback
            traceback.print_exc()
        finally:
            await canvas.logout()

    if english_assignments:
        _display_english_assignments(english_assignments)
    else:
        console.print("\n⚠️  未找到英语作业", style="yellow")


def _display_english_assignments(assignments):
    """显示英语作业列表"""
    console.print("\n" + "=" * 80)
    console.print("📚 英语作业列表", style="bold cyan")
    console.print("=" * 80 + "\n")

    table = Table(title="")
    table.add_column("序号", style="cyan", no_wrap=True, width=5)
    table.add_column("课程", style="magenta", width=30)
    table.add_column("作业标题", style="green", width=40)

    for i, assignment in enumerate(assignments, 1):
        table.add_row(
            str(i),
            assignment['course_name'][:30] if assignment['course_name'] else '未知',
            assignment['title'][:40] if assignment['title'] else '未知'
        )

    console.print(table)
    console.print(f"\n✅ 共找到 {len(assignments)} 个英语作业\n", style="bold green")
    console.print("💡 提示：运行 python auto_english_homework.py 生成这些作业的Word文档\n", style="yellow")


@cli.command()
@click.option('--config', type=click.Path(), help='配置文件路径')
@click.option('--assignment-id', type=str, help='作业ID')
@click.option('--all', 'all_assignments', is_flag=True, help='完成所有作业')
@click.option('--platform', type=click.Choice(['canvas', 'chaoxing']), help='指定平台')
def do_homework(config, assignment_id, all_assignments, platform):
    """执行作业生成"""
    console.print("\n🎯 开始生成作业...\n", style="bold cyan")
    console.print("📝 请使用 auto_english_homework.py 处理英语作业\n", style="yellow")


@cli.command()
@click.option('--directory', type=click.Path(), default='./homework_output',
              help='输出目录')
def list_output(directory):
    """查看已生成的作业文件"""
    output_path = Path(directory)

    if not output_path.exists():
        console.print(f"❌ 目录不存在: {directory}\n", style="red")
        return

    files = list(output_path.glob('*.docx')) + list(output_path.glob('*.txt'))

    if not files:
        console.print(f"⚠️  没有找到已生成的文件\n", style="yellow")
        console.print(f"   运行 python auto_english_homework.py 生成作业\n")
        return

    table = Table(title=f"📁 已生成文件 - {directory}")
    table.add_column("序号", style="cyan", no_wrap=True)
    table.add_column("文件名", style="green")
    table.add_column("大小", style="yellow")
    table.add_column("修改时间", style="magenta")

    for i, file in enumerate(sorted(files, key=lambda x: x.stat().st_mtime, reverse=True), 1):
        size = file.stat().st_size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"

        from datetime import datetime
        mtime = datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')

        table.add_row(str(i), file.name, size_str, mtime)

    console.print(table)
    console.print(f"\n✅ 共 {len(files)} 个文件\n", style="green")


if __name__ == '__main__':
    cli()
