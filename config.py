"""
配置管理模块
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PlatformConfig(BaseModel):
    """平台配置"""
    enabled: bool = True
    username: str = ""
    password: str = ""


class CanvasConfig(PlatformConfig):
    """Canvas配置"""
    url: str = "https://canvas.instructure.com"
    headless: bool = True


class ChaoxingConfig(PlatformConfig):
    """超星学习通配置"""
    url: str = "https://passport2.chaoxing.com"


class AIConfig(BaseModel):
    """AI配置"""
    provider: str = "auto"
    model: str = "auto"
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000


class OutputConfig(BaseModel):
    """输出配置"""
    format: str = "docx"
    directory: str = "./homework_output"
    filename_template: str = "{course}_{assignment}_{date}"


class AgentConfig(BaseModel):
    """Agent配置"""
    verbose: bool = True
    auto_review: bool = True
    max_retries: int = 3
    timeout: int = 300


class Config(BaseModel):
    """完整配置"""
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    chaoxing: ChaoxingConfig = Field(default_factory=ChaoxingConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.json"
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Config:
        """加载配置文件"""
        if not self.config_path.exists():
            return Config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Config(**data)
        except Exception as e:
            print(f"配置加载失败: {e}, 使用默认配置")
            return Config()

    def save_config(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config.model_dump(), f, indent=4, ensure_ascii=False)

    def get_config(self) -> Config:
        """获取配置对象"""
        return self.config

    def update_from_interactive(self):
        """交互式更新配置"""
        print("\n=== 平台配置 ===")

        print("\n1. Canvas LMS 配置:")
        self.config.canvas.url = input(f"   URL [{self.config.canvas.url}]: ") or self.config.canvas.url
        self.config.canvas.username = input(f"   用户名: ") or self.config.canvas.username
        self.config.canvas.password = input(f"   密码: ") or self.config.canvas.password

        print("\n2. 超星学习通配置:")
        self.config.chaoxing.username = input(f"   用户名: ") or self.config.chaoxing.username
        self.config.chaoxing.password = input(f"   密码: ") or self.config.chaoxing.password

        print("\n3. 输出配置:")
        self.config.output.directory = input(f"   输出目录 [{self.config.output.directory}]: ") or self.config.output.directory

        self.save_config()
        print("\n✓ 配置已保存")
