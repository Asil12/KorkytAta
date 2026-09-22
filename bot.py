import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# 1. ЛОГИРОВАНИЕ ЖӘНЕ БАПТАУЛАР
# ---------------------------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токендер
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8955051645:AAEDQwBDfTM4IyNM2omXTAF-y4stRtFh7y0")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6Lex1zz0k-CmIpULGx3bWY-IW7nOG6QXEJL0M_0x3J_Iw")

# Gemini клиентін баптау
client = genai.Client(api_key=GEMINI_API_KEY)

# Резервтік модельдер тізімі
FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

# Боттың жүйелік нұсқаулығы (System Prompt)
SYSTEM_PROMPT = """
Сіз — Қорқыт Ата және оның мемориалды кешені туралы толық мәлімет беретін виртуалды гидсіз.
Сұрақтарға қазақ тілінде, сыпайы, нақты әрі тарихи деректерге сүйене отырып жауап беріңіз.
Қорқыт Атаның өмірі, қобызда ойнау өнері, оның жырлары және Қызылорда облысындағы мемориалды кешен туралы ақпаратты анық түсіндіріңіз.
"""

# ---------------------------------------------------------------------------
# 2. RENDER ПОРТ СКАНИРОВАНИЕСІН ШЕШУ (HEALTH CHECK SERVER)
# ---------------------------------------------------------------------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is live and running!")

    def log_message(self, format, *args):
        return  # Консольді артық веб-логтармен толтырмау үшін

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logging.info(f"Health Check сервері {port} портында іске қосылды.")
    server.serve_forever()

# ---------------------------------------------------------------------------
# 3. GEMINI АРҚЫЛЫ ЖАУАП ГЕНЕРАЦИЯЛАУ (FALLBACK МЕХАНИЗМІ)
# ---------------------------------------------------------------------------
def get_ai_response(user_text: str) -> str:
    for model_name in FALLBACK_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.3
                )
            )
            if response and response.text:
                return response.text
        except Exception as e:
            logging.warning(f"[{model_name}] моделінде қате шықты: {e}. Келесі модель тексерілуде...")
            continue

    return "Кешіріңіз, қазіргі уақытта AI серверлері бос емес немесе авторизация қатесі бар. Сәлден соң қайталап көріңіз."

# ---------------------------------------------------------------------------
# 4. TELEGRAM ХЭНДЛЕРЛЕРІ
# ---------------------------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Армысыздар! Мен Қорқыт Ата мен оның мемориалды кешені туралы ақпарат беретін ботпын.\n\n"
        "Маған Қорқыт Ата өмірі, ғылыми еңбектері, жырлары немесе кешен туралы кез келген сұрағыңызды қойсаңыз болады."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return

    # Пайдаланушыға жауап дайындалып жатқанын көрсету
    await update.message.chat.send_action(action="typing")
    
    # AI жауабын алу
    ai_answer = get_ai_response(user_text)
    
    await update.message.reply_text(ai_answer)

# ---------------------------------------------------------------------------
# 5. НЕГІЗГІ ІСКЕ ҚОСУ ПУНКТІ
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # 1. Фейк веб-серверді бөлек ағында (thread) іске қосу
    threading.Thread(target=run_health_check, daemon=True).start()

    # 2. Telegram ботты құру
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 3. Командалар мен хабарлама өңдеушілерді қосу
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 4. Ботты іске қосу (Polling)
    logging.info("Telegram боты сәтті іске қосылды...")
    app.run_polling()
