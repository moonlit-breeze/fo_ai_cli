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

        # 先检查是否是命令
        if user_input.startswith("/"):
            conv.handle_command(user_input)
            continue
            
        conv.ask(user_input)
        