# 智能作业助手

一个基于 Kimi API 的 eLearning 英语作业助手。程序会登录 eLearning，筛选近一周内的英语类作业，提取作业要求，生成英文答案，并导出为 Word 文档。

## 当前版本特点

- 仅保留安全输入版入口
- 用户名、密码、模型、API 密钥均在运行时输入
- 敏感信息不写入仓库文件
- 输出统一格式的 Word 文档

## 环境要求

- Python 3.10+
- 可访问 eLearning 和 Kimi API 的网络环境
- 已安装 Chromium 浏览器驱动

## 安装

```bash
cd homework_agent
pip install -r requirements.txt
playwright install chromium
```

## 运行

```bash
python ai_homework_safe.py
```

运行后会依次提示输入：

- eLearning 用户名
- eLearning 密码
- Kimi API 密钥
- 模型选择
- 浏览器模式

## 安全说明

- 密码和 API 密钥通过隐藏输入读取
- 敏感信息只保存在当前进程内存中

## 可选模型

- `moonshot-v1-8k`
- `moonshot-v1-32k`
- `moonshot-v1-128k`

## 项目结构

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
    │   └── document.py
    └── platforms/
        ├── base.py
        └── canvas.py
```

## 主要文件

- [ai_homework_safe.py](file:///Users/mirong/Documents/TRAE/homework_agent/ai_homework_safe.py): 唯一保留的主入口
- [canvas.py](file:///Users/mirong/Documents/TRAE/homework_agent/agent/platforms/canvas.py): eLearning 登录与课程/作业抓取
- [document.py](file:///Users/mirong/Documents/TRAE/homework_agent/agent/generators/document.py): Word 文档生成
- [base.py](file:///Users/mirong/Documents/TRAE/homework_agent/agent/platforms/base.py): 课程与作业数据模型

