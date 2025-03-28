# API 文档

## DeepSeek API 配置

### 基本设置
- API端点: `https://api.deepseek.com`
- 模型名称: `deepseek-chat`

### 认证
- 需要API密钥
- 在config.py中配置

## 使用方法

### 初始化
```python
from src.markdown_cleaner import MarkdownCleaner

cleaner = MarkdownCleaner(api_key="your_api_key")
```

### 清洗单个文件
```python
cleaner.clean_file("path/to/file.md")
```
