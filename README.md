# 佛学问答 CLI 工具 | fo_ai_cli

一个基于 DeepSeek API 的佛学问答命令行工具，支持多轮对话、流式输出、对话管理，以及 RAG 检索增强生成。

## 功能特性

- **多轮对话**：保持上下文记忆，支持连续追问
- **流式输出**：实时显示 AI 回答，体验流畅
- **RAG 检索增强**：基于 ChromaDB + BAAI/bge-small-zh 本地向量模型，从佛学知识库中检索相关内容增强回答质量
- **对话管理**：支持保存/加载对话历史（/save /load /list）
- **模型切换**：支持 chat / reasoner 两种模型
- **净土宗专精**：System Prompt 偏重净土宗，引用《印光大师文钞》等论典

## 技术栈

| 组件 | 用途 |
|------|------|
| DeepSeek API | 大语言模型调用 |
| ChromaDB | 向量数据库，存储知识库文档 |
| BAAI/bge-small-zh | 本地中文 Embedding 模型 |
| sentence-transformers | Embedding 模型加载 |
| Rich | 终端美化输出 |
| python-dotenv | 环境变量管理 |

## 安装

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY
```

可选配置项（.env）：

```env
ENABLE_RAG=true          # 是否启用 RAG，默认 true
RAG_TOP_K=3              # 检索返回文档数，默认 3
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh  # 向量模型
```

## 使用

```bash
python cli_v1.py
```

## 命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/clear` | 清空对话历史 |
| `/save [文件名]` | 保存当前对话 |
| `/load [文件名]` | 加载已有对话 |
| `/list` | 列出已保存的对话 |
| `/model chat\|reasoner` | 切换模型 |
| `/rag` | 查看知识库状态 |
| `/rag-rebuild` | 重建知识库索引 |
| `/exit` | 退出 |

## 知识库

RAG 功能依赖 `knowledge_base.json` 文件，格式如下：

```json
[
  {
    "content": "佛学知识文本内容",
    "source": "《经论名称》",
    "category": "戒律/教义/禅修/其他"
  }
]
```

启动时自动加载并构建向量索引，问答时从知识库检索相关内容增强回答。
