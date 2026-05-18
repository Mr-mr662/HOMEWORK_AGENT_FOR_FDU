"""
Canvas LMS 平台集成 - 支持复旦大学eLearning
"""
import asyncio
import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from .base import PlatformBase, Assignment, Course


class CanvasPlatform(PlatformBase):
    """Canvas LMS 平台实现 - 支持复旦大学eLearning"""

    def __init__(self, username: str, password: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(username, password, config)
        self.url = self.config.get('url', 'https://canvas.instructure.com')
        self.headless = self.config.get('headless', True)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.access_token: Optional[str] = None

    async def _init_browser(self):
        """初始化浏览器"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.page = await self.browser.new_page()
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

    async def login(self) -> bool:
        """登录Canvas - 支持复旦大学eLearning"""
        try:
            await self._init_browser()

            print(f"正在访问: {self.url}")
            await self.page.goto(self.url, timeout=30000)
            await asyncio.sleep(3)

            current_url = self.page.url
            print(f"当前页面URL: {current_url}")

            print("查找并点击登录按钮...")
            login_button_selectors = [
                'a:has-text("登录")',
                'button:has-text("登录")',
                '[href*="login"]'
            ]

            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = await self.page.query_selector(selector)
                    if login_button:
                        print(f"找到登录按钮")
                        await login_button.click()
                        print(f"已点击登录按钮")
                        await asyncio.sleep(3)
                        break
                except:
                    continue

            if not login_button:
                print("未找到登录按钮，尝试直接访问登录页...")
                await self.page.goto(f"{self.url}/login", timeout=30000)
                await asyncio.sleep(2)

            print(f"当前URL: {self.page.url}")

            if 'id.fudan.edu.cn' in self.page.url:
                print("检测到复旦统一身份认证页面...")
                return await self._login_id_fudan()
            elif '/login' in self.page.url:
                return await self._login_canvas_form()
            else:
                await self.page.goto(f"{self.url}/login", timeout=30000)
                await asyncio.sleep(2)
                if 'id.fudan.edu.cn' in self.page.url:
                    return await self._login_id_fudan()
                return await self._login_canvas_form()

        except Exception as e:
            print(f"Canvas登录失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _login_id_fudan(self) -> bool:
        """复旦大学统一身份认证登录"""
        try:
            current_url = self.page.url
            print(f"复旦统一身份认证页面: {current_url}")

            await asyncio.sleep(2)

            username_selectors = [
                'input[name="username"]',
                'input[id="username"]',
                'input[type="text"]'
            ]

            password_selectors = [
                'input[name="password"]',
                'input[id="password"]',
                'input[type="password"]'
            ]

            username_input = None
            for selector in username_selectors:
                username_input = await self.page.query_selector(selector)
                if username_input:
                    print(f"找到用户名输入框")
                    break

            password_input = None
            for selector in password_selectors:
                password_input = await self.page.query_selector(selector)
                if password_input:
                    print(f"找到密码输入框")
                    break

            if not username_input or not password_input:
                print("未找到登录表单，保存截图分析...")
                await self.page.screenshot(path='id_fudan_login_failed.png')

                content = await self.page.content()
                with open('id_fudan_login_failed.html', 'w', encoding='utf-8') as f:
                    f.write(content)

                print("已保存: id_fudan_login_failed.png 和 id_fudan_login_failed.html")
                return False

            print(f"正在填写登录信息...")
            await username_input.fill(self.username)
            await asyncio.sleep(0.3)
            await password_input.fill(self.password)

            await asyncio.sleep(1)

            submit_button = await self.page.query_selector('button[type="submit"]')
            if not submit_button:
                submit_button = await self.page.query_selector('button:has-text("登录")')

            if submit_button:
                print(f"找到提交按钮")
                await submit_button.click()
            else:
                print("未找到提交按钮，尝试提交表单...")
                form = await self.page.query_selector('form')
                if form:
                    await self.page.evaluate('form => form.submit()', form)
                else:
                    await self.page.keyboard.press('Enter')

            print("等待登录完成...")
            await asyncio.sleep(5)

            final_url = self.page.url
            print(f"登录后URL: {final_url}")

            if 'dash' in final_url or 'dashboard' in final_url or 'login_success' in final_url:
                self.logged_in = True
                print("✅ 登录成功！")
                return True
            elif 'elearning.fudan.edu.cn' in final_url and 'login' not in final_url.lower():
                self.logged_in = True
                print("✅ 登录成功！")
                return True
            else:
                print("❌ 登录失败")
                return False

        except Exception as e:
            print(f"登录失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _login_canvas_form(self) -> bool:
        """直接Canvas表单登录"""
        try:
            username_input = await self.page.query_selector('input[name="pseudonym_session[unique_id]"]')
            password_input = await self.page.query_selector('input[name="pseudonym_session[password]"]')

            if username_input and password_input:
                print("找到Canvas登录表单，正在填写...")
                await username_input.fill(self.username)
                await password_input.fill(self.password)

                await asyncio.sleep(0.5)

                submit_button = await self.page.query_selector('input[type="submit"][value="登录"]')
                if not submit_button:
                    submit_button = await self.page.query_selector('#login_form input[type="submit"]')

                if submit_button:
                    await self.page.evaluate('button => button.click()', submit_button)
                else:
                    await self.page.keyboard.press('Enter')

                print("等待登录完成...")
                await asyncio.sleep(5)

                final_url = self.page.url

                if 'uis.fudan.edu.cn' in final_url:
                    print("跳转到UIS认证...")
                    return await self._login_id_fudan()
                elif final_url != f"{self.url}/login/canvas" and 'login' not in final_url.lower():
                    self.logged_in = True
                    print("✅ Canvas登录成功")
                    return True
                else:
                    print("❌ Canvas登录失败")
                    return False
            else:
                print("未找到Canvas登录表单")
                return False

        except Exception as e:
            print(f"Canvas表单登录失败: {e}")
            return False

    async def get_courses(self) -> List[Course]:
        """获取课程列表"""
        await self.ensure_login()

        courses = []
        try:
            print("正在访问课程页面...")
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    print(f"尝试 {attempt + 1}/{max_retries}...")
                    await self.page.goto(f"{self.url}/courses", timeout=90000)
                    await asyncio.sleep(10)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"超时，重试中...")
                        await asyncio.sleep(5)
                        continue
                    else:
                        print(f"访问courses页面失败，尝试dashboard...")
                        try:
                            await self.page.goto(f"{self.url}/dashboard", timeout=90000)
                            await asyncio.sleep(10)
                        except:
                            print("dashboard也超时，但继续尝试解析当前页面...")
                            await asyncio.sleep(3)

            print(f"当前URL: {self.page.url}")
            print("正在查找课程...")

            course_selectors = [
                'a[href*="/courses/"]',
                '.course-card a',
                '.course-listing-item a',
                '[class*="course"] a[href*="/courses/"]',
                'li.course-list-item a',
                '.courses .course a'
            ]

            all_course_links = []
            for selector in course_selectors:
                links = await self.page.query_selector_all(selector)
                if links:
                    print(f"  使用选择器 '{selector}' 找到 {len(links)} 个链接")
                    all_course_links.extend(links)

            seen_ids = set()
            for link in all_course_links:
                try:
                    href = await link.get_attribute('href')
                    title = await link.inner_text()

                    if href and '/courses/' in href and title and len(title.strip()) > 2:
                        course_id = None
                        match = re.search(r'/courses/(\d+)', href)
                        if match:
                            course_id = match.group(1)

                        if course_id and course_id not in seen_ids:
                            seen_ids.add(course_id)
                            courses.append(Course(
                                id=course_id,
                                name=title.strip(),
                                code='',
                                instructor=None
                            ))
                            print(f"  找到课程: {title.strip()} (ID: {course_id})")
                except Exception as e:
                    continue

            print(f"\n共找到 {len(courses)} 门课程")

            if len(courses) == 0:
                print("提示：尝试访问dashboard获取课程...")
                await self.page.goto(f"{self.url}/dashboard", wait_until="networkidle", timeout=20000)
                await asyncio.sleep(3)

                links = await self.page.query_selector_all('a[href*="/courses/"]')
                print(f"Dashboard找到 {len(links)} 个课程链接")

                for link in links[:10]:
                    try:
                        href = await link.get_attribute('href')
                        title = await link.inner_text()

                        if href and '/courses/' in href and title and len(title.strip()) > 2:
                            match = re.search(r'/courses/(\d+)', href)
                            if match:
                                course_id = match.group(1)
                                courses.append(Course(
                                    id=course_id,
                                    name=title.strip(),
                                    code='',
                                    instructor=None
                                ))
                                print(f"  Dashboard课程: {title.strip()} (ID: {course_id})")
                    except:
                        continue

        except Exception as e:
            print(f"获取课程列表失败: {e}")
            import traceback
            traceback.print_exc()

        return courses

    async def get_assignments(self, course_id: Optional[str] = None) -> List[Assignment]:
        """获取作业列表"""
        await self.ensure_login()

        assignments = []
        try:
            if course_id:
                courses_to_check = [course_id]
            else:
                courses = await self.get_courses()
                courses_to_check = [c.id for c in courses[:10]]

            print(f"正在检查 {len(courses_to_check)} 门课程的作业...")

            for cid in courses_to_check:
                try:
                    url = f"{self.url}/courses/{cid}/assignments"
                    print(f"  检查课程 {cid} 的作业...")
                    await self.page.goto(url, timeout=30000)
                    await asyncio.sleep(3)

                    assignment_links = await self.page.query_selector_all('a[href*="/assignments/"]')

                    course_name = ''
                    course_title_elem = await self.page.query_selector('h1, h2, [class*="course-title"]')
                    if course_title_elem:
                        course_name = await course_title_elem.inner_text()

                    for link in assignment_links:
                        try:
                            href = await link.get_attribute('href')
                            title = await link.inner_text()

                            if title and len(title.strip()) > 2 and '/assignments/' in href:
                                assignment_id = href.split('/assignments/')[-1].split('/')[0]

                                if assignment_id.isdigit():
                                    assignments.append(Assignment(
                                        id=assignment_id,
                                        title=title.strip(),
                                        course_name=course_name.strip(),
                                        course_id=cid,
                                        description='',
                                        due_date=None,
                                        points_possible=None,
                                        submission_types=['online_text_entry'],
                                        instructions='',
                                        attachments=[]
                                    ))
                        except:
                            continue

                except Exception as e:
                    print(f"  获取课程 {cid} 的作业失败: {e}")
                    continue

            print(f"找到 {len(assignments)} 个作业")
            for assignment in assignments[:5]:
                print(f"  - [{assignment.course_name[:20]}] {assignment.title[:40]}")

        except Exception as e:
            print(f"获取作业列表失败: {e}")
            import traceback
            traceback.print_exc()

        return assignments

    async def get_assignment_details(self, assignment_id: str, course_id: str = None) -> Optional[Assignment]:
        """获取作业详情"""
        await self.ensure_login()

        try:
            if not course_id:
                courses = await self.get_courses()
                for course in courses[:5]:
                    url = f"{self.url}/courses/{course.id}/assignments"
                    await self.page.goto(url, wait_until="networkidle", timeout=10000)
                    await asyncio.sleep(1)

                    content = await self.page.content()
                    if assignment_id in content:
                        course_id = course.id
                        break

            if not course_id:
                print(f"未找到作业 {assignment_id} 所属课程")
                return None

            url = f"{self.url}/courses/{course_id}/assignments/{assignment_id}"
            await self.page.goto(url, wait_until="networkidle", timeout=10000)
            await asyncio.sleep(2)

            title_elem = await self.page.query_selector('h1, h2, [class*="title"]')
            title = await title_elem.inner_text() if title_elem else "Untitled"

            desc_elem = await self.page.query_selector('[class*="description"], .description, #description')
            description = await desc_elem.inner_text() if desc_elem else ''

            course_name = ''
            course_title_elem = await self.page.query_selector('h1, [class*="course-title"]')
            if course_title_elem:
                course_name = await course_title_elem.inner_text()

            return Assignment(
                id=assignment_id,
                title=title.strip(),
                course_name=course_name.strip(),
                course_id=course_id,
                description=description.strip(),
                due_date=None,
                points_possible=None,
                submission_types=['online_text_entry'],
                instructions=description.strip(),
                attachments=[]
            )

        except Exception as e:
            print(f"获取作业详情失败: {e}")
            return None

    async def logout(self):
        """登出"""
        if self.page:
            try:
                await self.page.close()
            except:
                pass
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        self.logged_in = False
        self.access_token = None
