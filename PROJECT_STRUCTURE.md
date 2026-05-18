# 项目结构说明

## 当前保留结构

```text
homework_agent/
├── ai_homework_safe.py
├── api_config.json
├── config.json
├── requirements.txt
├── README.md
├── PROJECT_STRUCTURE.md
└── agent/
    ├── generators/
    │   ├── __init__.py
    │   └── document.py
    └── platforms/
        ├── __init__.py
        ├── base.py
        └── canvas.py
```

## 入口文件

- [ai_homework_safe.py](file:///Users/mirong/Documents/TRAE/homework_agent/ai_homework_safe.py): 项目唯一入口，运行时安全输入用户名、密码、模型和 API 密钥。

## 平台模块

- [base.py](file:///Users/mirong/Documents/TRAE/homework_agent/agent/platforms/base.py): 定义 [Assignment](file:///Users/mirong/Documents/TRAE/homework_agent/agent/platforms/base.py#L10-L25) 和 [Course](file:///Users/mirong/Documents/TRAE/homework_agent/agent/platforms/base.py#L28-L35) 数据结构。
- [canvas.py](file:///Users/mirong/Documents/TRAE/homework_agent/agent/platforms/canvas.py): 负责 eLearning 登录、课程抓取、作业抓取。

## 生成模块

- [document.py](file:///Users/mirong/Documents/TRAE/homework_agent/agent/generators/document.py): 负责生成统一格式的 Word 文档。

## 配置文件

- [api_config.json](file:///Users/mirong/Documents/TRAE/homework_agent/api_config.json): 已脱敏，仅保留空白示例。
- [config.json](file:///Users/mirong/Documents/TRAE/homework_agent/config.json): 已脱敏，仅保留通用默认值。

## 已清理内容

以下内容已从仓库移除：

- 旧主程序入口
- 超星相关代码
- 调试截图和调试 HTML
- IDE 工程文件
- 旧 CLI 和冗余脚本

## 运行方式

```bash
python ai_homework_safe.py
```
