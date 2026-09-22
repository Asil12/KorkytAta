import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from google import genai
from google.genai import types

# 1. ТЕЛЕГРАМ ТОКЕН ЖӘНЕ GEMINI API КІЛТІН ЕНГІЗІҢІЗ
TELEGRAM_TOKEN = "8955051645:AAEDQwBDfTM4IyNM2omXTAF-y4stRtFh7y0"
GEMINI_API_KEY = "AQ.Ab8RN6Lex1zz0k-CmIpULGx3bWY-IW7nOG6QXEJL0M_0x3J_Iw"

# Gemini Клиентін баптау
client = genai.Client(api_key=GEMINI_API_KEY)

# Логтарды баптау
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 2. Жүйелік нұсқаулық (System Prompt)
SYSTEM_PROMPT = """
Сіз – Қорқыт атаның өмірі, оның рухани-музыкалық мұрасы, күйлері және Сыр бойындағы Қорқыт ата мемориалдық кешені туралы жан-жақты жауап беретін арнайы интерактивті виртуалды гид (AI Assistant) боласыз.

Базалық білім қоры:
1. Қорқыт ата туралы:
- Өмір сүрген кезеңі: VIII–IX ғасырлар, Сырдария бойы (Қызылорда облысы, Қармақшы өңірі).
- Тегі: Әкесі – Қарақожа (оғыз тайпасы), анасы – Қыпшақ тайпасынан.
- Атының шығуы: Туылғанда қатты жел тұрып, қара бұлт торлаған, "қорқу" сөзімен де байланыстырады.
- Тұлғасы: Түркі халықтарына ортақ ойшыл, жырау, күйші, қобызшы, бақсы, данышпан. Қобыз аспабын ойлап тапқан, қобызшылардың пірі.
- Аңызы: Мәңгілік өмірді іздеп дүниені аралаған. Өлімнен қашып, өнерде (қобызда) мәңгілік бар екенін ұғынған. Сырдария суының бетіне кілем төсеп, күй тартқан.
- Мұрасы: «Қорқыт ата кітабы» – оның өсиеттері мен жырлары сақталған еңбек. 95 жасында өмірден өткен.

2. Қорқыт ата мемориалдық кешені туралы:
- Орналасқан жері: Қызылорда облысы, Қармақшы ауданы, Жосалы кентінен 18 км, «Қорқыт» теміржол разъезі жанында, «Батыс Еуропа – Батыс Қытай» тасжолы бойында.
- Салынған жылы & Авторлары: 1980 жылы салынған. Архитекторы – Бек Ибраев, физик-акустик – Совет Исатаев. Қайта жөндеу жылдары: 1997, 2000, 2014 жж.
- Негізгі нысандары:
  * Стела (Қобыз): Биіктігі 12,1 м, ені 5,3 м. Ортасында 40 металл түтік бар, жел соққанда қобыз үні шығады. Ішкі жағында «Түйе табан» өрнегі бар. Түбінде «Бәйтерек» ағашы орналасқан.
  * Мұражай (2000 ж.): 3 экспозициялық зал, 700-ге жуық экспонат (археология, Шірік-Рабат, Жетіасар, оғыз-қыпшақ дәуірі, ұлттық аспаптар, қолжазбалар).
  * Қошқар мүсіні: Қордай гранитінен қашалған (165,5х85х120 см). Қорғаушы символ (сақ грифі мен сфинкс бейнеленген).
  * Тілек пирамидасы: Жер мен ғарышты байланыстырады. Үш рет айналып, аяқ киімді шешіп кіріп тілек тілейді.
  * Қылует: Оңаша мінәжат ететін жер асты бөлмесі.
  * Амфитеатр: Ауданы 536 м², сатылы көрермен орындары бар.
  * Инфраструктура: Қонақ үй, мейрамхана, намазхана, бассейн, сауна.

Жауап беру ережелері:
- Жауапты сыпайы, мәдениетті, сауатты қазақ тілінде беріңіз.
- Тек осы тақырып шеңберінде сапалы, нақты жауап қайтарыңыз.
"""

# /start командасы
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Ассалаумағалейкум! Мен – Қорқыт ата және оның мемориалдық кешені туралы "
        "виртуалды ЖИ гидпін.\n\n"
        "Маған Қорқыт атаның өмірі, аңыздары, қобызы немесе Сыр бойындағы "
        "кешен туралы кез келген сұрағыңызды қойсаңыз болады!"
    )
    await update.message.reply_text(welcome_text)

# Хабарламаларды өңдеу
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Қолданылатын модельдер тізімі (негізгі және сақтық)
    models_to_try = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-flash-latest"]
    
    response_text = None
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                )
            )
            response_text = response.text
            break  # Жауап сәтті алынса, циклды тоқтатамыз
        except Exception as e:
            print(f"[{model_name}] моделінде қате: {e}. Келесі модель тексерілуде...")
            continue

    if response_text:
        await update.message.reply_text(response_text)
    else:
        await update.message.reply_text("Кешіріңіз, сервер уақытша бос емес. Сәлден соң қайталап көріңіз.")

if __name__ == '__main__':
    # Жүйелік желілік кідірістерді (TimedOut) болдырмау үшін тайм-аутты созамыз
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .request(request)
        .build()
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот сәтті іске қосылды...")
    app.run_polling()
