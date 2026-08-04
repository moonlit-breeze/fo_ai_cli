import os
import json
import time
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from config import DEEPSEEK_API_KEY, BASE_URL, DEFAULT_MODEL, SYSTEM_PROMPT
from datetime import datetime

console = Console()
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL, max_retries=3)

class FoConversation:
    def  __init__(self):
        self.system_prompt = """你是一位净土宗佛学助手，遵循以下规则：
        1. 回答必须依据正统佛法，不编造戒律与经文
        2.涉及戒律时，必须提示『仅供参考，以丛林规约为准』
        3.优先引用《印光大师文钞》等净土宗论典
        4.回答简洁，不超过300字
        5.不评论其他法门高下，不涉政治
        """
        # messages列表：第一个永远是system，后面交替user/assistant
        self.message = [{"role": "system", "content": self.system_prompt}]
        # 初始化保存目录
        self.save_dir = "."
        self.model = "deepseek-chat"
     
    def add_user(self, text):
        """添加用户消息到对话历史"""
        self.message.append({"role": "user", "content": text})

    def add_assistant(self, text):
        """添加AI回复到对话历史"""
        self.message.append({"role": "assistant", "content": text})

    def get_messages(self):
        """获取完整的消息列表（包含system + 历史对话）"""
        return self.message

    def handle_command(self, cmd: str) -> bool:
        """处理特殊命令，返回True表示已处理（不再发给AI）"""
        parts = cmd.split()
        command = parts[0].lower()

        if command == "/clear":
          self.message = [{"role": "system", "content": self.system_prompt}]
          console.print("[green]对话历史已清空[green]")
          return True
        
        elif command == "/save":
            self.save_conversation(filename=None)
            return True
        
        elif command == "/load":
            if len(parts) > 1:
                filepath = os.path.join("conversations", parts[1])
                if os.path.exists(filepath):
                    self.load_conversation(filepath)
                else:
                    console.print(f"[red]文件不存在：{filepath}[/red]")
            else:
                console.print("[yellow]用法：/load 文件名.json[/yellow]")
            return True

        elif command == "/list":
            if os.path.exists("conversations"):
                files = os.listdir("conversations")
                if files:
                    console.print("[cyan]已保存的对话：[/cyan]")
                    for f in files:
                        console.print(f"  {f}")
                else:
                    console.print("[yellow]暂无保存的对话[/yellow]")
            else:
                console.print("[yellow]暂无保存的对话[/yellow]")
            return True

        elif command == "/help":
            console.print("""[cyan]可用命令：
            /clear: 清空对话历史
            /save [文件名]: 保存对话到文件
            /load [文件名]: 加载文件中的对话
            /list: 列出已保存的对话
            /model: 切换模型（chat/reasoner）
            /exit: 退出 （内容由AI生成，仅供参考）""")
            return True

        elif command == "/model":
            if len(parts) >1 and parts[1] in ["chat", "reasoner"]:
                self.model = f"deepseek-{parts[1]}"
                console.print(f"[green]已切换到 {self.model}[/green]")
            else:
                console.print(f"[yellow]用法：/model chat 或 /model reasoner[/yellow]")
            return True
        
        elif command == "/exit":
            console.print("[yellow]退出 （内容由AI生成，仅供参考）[/yellow]")
            exit()

        return False

    def save_conversation(self, filename=None):
        if not filename:
            filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs("conversations", exist_ok=True)
        filepath = os.path.join("conversations", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "model": self.model,
                "message": self.message
            }, f, ensure_ascii=False, indent=2)

        console.print(f"[green]对话已保存到{filepath}[/green]")
        return filepath


    def load_conversation(self, filepath):
        if not filepath:
            console.print(f"[red]请输入要加载的对话文件路径[/red]")
            return

        if not os.path.exists(filepath):
            console.print(f"[red]文件不存在：{filepath}[/red]")
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.model = data["model"]
            self.message = data["message"]
            console.print(f"[green]已从 {filepath} 加载对话[/green]")
        except json.JSONDecodeError:
            console.print(f"[red]文件格式错误或为空：{filepath}[/red]")
        except KeyError as e:
            console.print(f"[red]文件缺少必要字段：{e}[/red]")

    def ask(self, question: str, max_retries=3):
        if question.startswith("/"):
            if self.handle_command(question):
                return
            
        # 1. 把用户问题加入历史
        self.add_user(question)

        for attempt in range(max_retries):
            try:
                # 用Rich显示"正在思考"提示
                console.print("[yellow]◇ 正在思考...[/yellow]")

                # 2. 向AI提问，流式输出在Panel内逐字显示
                response = client.chat.completions.create(
                    model=self.model,
                    messages=self.get_messages(),
                    stream=True,
                    timeout=30.0
                )

                full_reply = []
                with Live(Panel.fit("", title="[cyan]AI回答[/cyan]", border_style="cyan"),
                          console=console, refresh_per_second=20) as live:
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_reply.append(content)
                            live.update(Panel.fit(''.join(full_reply),
                                                  title="[cyan]AI回答[/cyan]",
                                                  border_style="cyan"))

                reply_text = ''.join(full_reply)

                # 3. 添加AI回复到历史，下次对话AI就能"记得"
                self.add_assistant(reply_text)
                return

            except Exception as e:
                console.print(f"[yellow]第{attempt+1}次尝试失败：{e}[/yellow]")
                if attempt < max_retries - 1:
                    console.print("[dim]2秒后重试...[/dim]")
                    time.sleep(2)
                else:
                    console.print(f"[red]调用失败：{e}[/red]")
                    # 失败时移除刚加的用户消息，允许重试
                    self.message.pop()
