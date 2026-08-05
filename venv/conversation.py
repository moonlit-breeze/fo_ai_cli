import os
import json
import time
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from config import DEEPSEEK_API_KEY, BASE_URL, DEFAULT_MODEL, SYSTEM_PROMPT, ENABLE_RAG, KNOWLEDGE_BASE_FILE, RAG_TOP_K
from datetime import datetime
from rag import get_rag

console = Console()
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL, max_retries=3)

class FoConversation:
    def  __init__(self):
        self.system_prompt = """你是一位净土宗佛学助手，遵循以下规则：
        1. 回答必须依据正统佛法，不编造戒律与经文
        2. 涉及戒律时，必须提示『仅供参考，以丛林规约为准』
        3. 优先引用《印光大师文钞》等净土宗论典
        4. 回答简洁，不超过300字
        5. 不评论其他法门高下，不涉政治
        6. 【重要】当有知识库检索结果时，优先参考检索结果中的内容回答
        
        【回答格式要求】必须严格按照以下格式：
        
        答：[正文内容，简明扼要]
        
        注：[如有戒律相关说明，在此注明，如"仅供参考，以丛林规约为准"]
        
        出处：[必须单独一行，列出引用的经论名称]
        
        示例1：
        问：什么是五戒？
        答：五戒是佛教在家弟子应持的根本戒律，包括不杀生、不偷盗、不邪淫、不妄语、不饮酒。
        
        出处：《长阿含经》《增一阿含经》
        
        示例2（含戒律说明）：
        问：不偷盗戒的范围？
        答：不偷盗戒禁止一切不与而取的行为，包括直接窃取、骗取、侵占，乃至借而不还。
        
        出处：《四分律》卷一
        
        重要：出处必须单独成行，不能与其他内容在同一行。
        """

        # messages列表：第一个永远是system，后面交替user/assistant
        self.message = [{"role": "system", "content": self.system_prompt}]
        # 初始化保存目录
        self.save_dir = "."
        self.model = "deepseek-chat"

        # 初始化RAG系统
        self.rag = None
        if ENABLE_RAG:
            try:
                self.rag = get_rag()
                # 如果知识库为空，自动初始化
                if self.rag.get_collection_count() == 0:
                    if os.path.exists(KNOWLEDGE_BASE_FILE):
                        console.print("[cyan]正在初始化知识库...[/cyan]")
                        self.rag.load_documents_from_file(KNOWLEDGE_BASE_FILE)
                        console.print(f"[green]知识库已加载，共{self.rag.get_collection_count()}篇文档[/green]")
                    else:
                        console.print(f"[yellow]知识库文件不存在：{KNOWLEDGE_BASE_FILE}[/yellow]")
                        console.print("[yellow]RAG功能已禁用[/yellow]")
                        self.rag = None
            except Exception as e:
                console.print(f"[yellow]RAG初始化失败：{e}[/yellow]")
                self.rag = None
     
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
            /rag: 查看知识库状态
            /rag-rebuild: 重建知识库
            /exit: 退出""")
            return True

        elif command == "/model":
            if len(parts) >1 and parts[1] in ["chat", "reasoner"]:
                self.model = f"deepseek-{parts[1]}"
                console.print(f"[green]已切换到 {self.model}[/green]")
            else:
                console.print(f"[yellow]用法：/model chat 或 /model reasoner[/yellow]")
            return True

        elif command == "/rag":
            if self.rag:
                console.print(f"[cyan]知识库状态：[/cyan]")
                console.print(f"  文档数：{self.rag.get_collection_count()}")
            else:
                console.print("[yellow]RAG未启用[/yellow]")
            return True

        elif command == "/rag-rebuild":
            if not self.rag:
                console.print("[yellow]RAG未启用[/yellow]")
                return True
            if os.path.exists(KNOWLEDGE_BASE_FILE):
                console.print("[cyan]正在重建知识库...[/cyan]")
                self.rag.load_documents_from_file(KNOWLEDGE_BASE_FILE)
                console.print(f"[green]知识库已重建，共{self.rag.get_collection_count()}篇文档[/green]")
            else:
                console.print(f"[red]知识库文件不存在：{KNOWLEDGE_BASE_FILE}[/red]")
            return True
        
        elif command == "/exit":
            console.print("[yellow]退出[/yellow]")
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

        # 1. RAG检索相关内容
        rag_context = ""
        if self.rag and not question.startswith("/"):
            console.print("[dim]🔍 正在检索知识库...[/dim]")
            rag_context = self.rag.build_context(question, top_k=RAG_TOP_K)
            if rag_context:
                console.print(f"[dim]✓ 检索到{self.rag.get_collection_count()}篇文档[/dim]")

        # 2. 构建增强后的用户消息
        enhanced_question = question
        if rag_context:
            enhanced_question = f"{rag_context}\n\n【用户问题】\n{question}"

        # 3. 把用户问题加入历史
        self.add_user(enhanced_question)

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
