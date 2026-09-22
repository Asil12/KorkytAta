import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ---------------------------------------------------------------------------
# 1. БАПТАУЛАР ЖӘНЕ АВТОРИЗАЦИЯ
# ---------------------------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8955051645:AAEDQwBDfTM4IyNM2omXTAF-y4stRtFh7y0")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6JuVHUSCA1O4kHnaUF6nmwTmjXpXt9mdPgD8b27leWenw")

# Gemini API баптау (AQ... кілтімен де жұмыс істейді)
genai.configure(api_key=GEMINI_API_KEY)

# Резервтік модельдер тізімі
FALLBACK_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro"
]

SYSTEM_PROMPT = """
Сіз — Қорқыт Ата және оның мемориалды кешені туралы толық мәлімет беретін виртуалды гидсіз.
Сұрақтарға қазақ тілінде, сыпайы, нақты әрі тарихи деректерге сүйене отырып жауап беріңіз.
Қорқыт Атаның өмірі, қобызда ойнау өнері, оның жырлары және Қызылорда облысындағы мемориалды кешен туралы ақпаратты анық түсіндіріңіз.
"""

# ---------------------------------------------------------------------------
# 2. HEALTH CHECK SERVER (PORT TIMEOUT ТҮЗЕТУ)
# ---------------------------------------------------------------------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

    def log_message(self, format, *args):
        return

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# ---------------------------------------------------------------------------
# 3. AI ЖАУАБЫН АЛУ
# ---------------------------------------------------------------------------
def get_ai_response(user_text: str) -> str:
    for model_name in FALLBACK_MODELS:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT
            )
            response = model.generate_content(user_text)
            if response and response.text:
                return response.text
        except Exception as e:
            logging.warning(f"[{model_name}] қате берді: {e}. Келесі модель тексерілуде...")
            continue

    return "Өкінішке орай, AI сервері жауап бере алмады. Бірнеше секундтан кейін қайта байқап көріңіз."

# ---------------------------------------------------------------------------
# 4. TELEGRAM ХЭНДЛЕРЛЕРІ
# ---------------------------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Армысыздар! Мен Қорқыт Ата мен оның мемориалды кешені туралы ақпарат беретін ботпын.\n\n"
        "Сұрағыңызды қоя беріңіз!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return

    await update.message.chat.send_action(action="typing")
    ai_answer = get_ai_response(update.message.text)
    await update.message.reply_text(ai_answer)

# ---------------------------------------------------------------------------
# 5. ІСКЕ ҚОСУ
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    threading.Thread(target=run_health_check, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Telegram боты іске қосылды...")
    app.run_polling()
