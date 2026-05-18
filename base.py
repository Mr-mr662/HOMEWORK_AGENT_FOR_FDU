"""
平台基类定义
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Assignment:
    """作业信息"""
    id: str
    title: str
    course_name: str
    course_id: str
    description: str
    due_date: Optional[datetime]
    points_possible: Optional[float]
    submission_types: List[str]
    instructions: str
    attachments: List[Dict[str, Any]]

    def __str__(self):
        return f"[{self.course_name}] {self.title} (截止: {self.due_date.strftime('%Y-%m-%d %H:%M') if self.due_date else '无'})"


@dataclass
class Course:
    """课程信息"""
    id: str
    name: str
    code: str
    instructor: Optional[str] = None


class PlatformBase(ABC):
    """平台基类"""

    def __init__(self, username: str, password: str, config: Optional[Dict[str, Any]] = None):
        self.username = username
        self.password = password
        self.config = config or {}
        self.logged_in = False

    @abstractmethod
    async def login(self) -> bool:
        """登录平台"""
        pass

    @abstractmethod
    async def get_courses(self) -> List[Course]:
        """获取课程列表"""
        pass

    @abstractmethod
    async def get_assignments(self, course_id: Optional[str] = None) -> List[Assignment]:
        """获取作业列表"""
        pass

    @abstractmethod
    async def get_assignment_details(self, assignment_id: str) -> Assignment:
        """获取作业详情"""
        pass

    @abstractmethod
    async def logout(self):
        """登出"""
        pass

    async def ensure_login(self):
        """确保已登录"""
        if not self.logged_in:
            await self.login()
