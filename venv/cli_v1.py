from rich.console import Console
from conversation import FoConversation

console = Console()

if __name__ == "__main__":
    conv = FoConversation()
    console.print("[blod cyan]=== 佛学问答CLI ===[/blod cyan]")
    console.print("[dim]输入 /help 查看命令，输入exit退出[/dim]\n")
    
    while True:
        try:
            user_input = input("\n>> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]再见[/yellow]")
            break

        if user_input.lower() == "exit":
            console.print("[yellow]bye~[/yellow]")
            break

        if not user_input:
            continue

        # 输入长度检查，成本意识
        MAX_INPUT_LENGTH = 3000
        if len(user_input) > MAX_INPUT_LENGTH:
            console.print(f"[yellow]⚠️ 输入过长({len(user_input)}字符)，可能产生额外成本。是否继续？[/yellow]")
            confirm = input("按回车继续，或输入 n 取消: ").strip().lower()
            if confirm == "n":
                continue

        # 先检查是否是命令
        if user_input.startswith("/"):
            conv.handle_command(user_input)
            continue
            
        conv.ask(user_input)
        