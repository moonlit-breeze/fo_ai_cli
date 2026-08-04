
# 佛学问答CLI工具

一个基于DeepSeek API的佛学问答命令行工具，支持多轮对话、流式输出、对话保存/加载。

## 安装

pip install -r requirements.txt
cp .env.example .env
编辑.env，填入你的DEEPSEEK_API_KEY

## 使用

python fo_cli.py

## 命令

- `/help` - 显示帮助
- `/clear` - 清空对话历史
- `/save [文件名]` - 保存对话
- `/load [文件名]` - 加载对话
- `/list` - 列出已保存的对话
- `/model chat|reasoner` - 切换模型
- `/exit` - 退出
