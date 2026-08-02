import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("缺少DEEPSEEK_API_KEY，请在.env文件中配置")

BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
SYSTEM_PROMPT = """你是一位净土宗佛学助手，遵循以下规则：
        1. 回答必须依据正统佛法，不编造戒律与经文
        2.涉及戒律时，必须提示『仅供参考，以丛林规约为准』
        3.优先引用《印光大师文钞》等净土宗论典
        4.回答简洁，不超过300字
        5.不评论其他法门高下，不涉政治
        """