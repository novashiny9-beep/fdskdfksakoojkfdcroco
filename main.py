import telebot
from flask import Flask, request
import requests
import json

# БОТ БАПТАУЛАРЫ
TOKEN = '8295067174:AAE5q4O4VkbKBbjVITVzAX-Tkb8Q9OMMzUk'
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Әр топтың ойын күйін бөлек сақтайтын сөздік
games = {}

def get_ai_word():
    """Тегін AI арқылы нақты уақытта Крокодил ойынына арналған қазақша сөз алу"""
    url = "https://duckduckgo.com/duckchat/v1/chat"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/event-stream",
        "x-vqd-4": "1"  # Бастапқы сессия белгісі
    }
    
    # 1. Алдымен AI сессиясын ашу үшін VQD токенін аламыз
    try:
        status_url = "https://duckduckgo.com/duckchat/v1/status"
        resp = requests.get(status_url, headers={"x-vqd-4": "1", "User-Agent": "Mozilla/5.0"})
        vqd = resp.headers.get("x-vqd-4")
        
        if not vqd:
            return "алма"  # Егер AI жауап бермесе, резервтік сөз
            
        headers["x-vqd-4"] = vqd
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{
                "role": "user", 
                "content": "Крокодил ойынына арналған бір ғана қазақша зат есім сөз жаз. Тек сөздің өзін ғана жаз, басқа ештеңе қоспа. Мысалы: машина"
            }]
        }
        
        # 2. Жауапты алу
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        
        # Текст ағынын тазалап, тек сөзді бөліп аламыз
        lines = response.text.split("\n")
        word = ""
        for line in lines:
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "message" in data:
                        word += data["message"]
                except:
                    continue
        
        cleaned_word = word.strip().replace(".", "").replace("!", "").lower()
        return cleaned_word if cleaned_word else "кітап"
        
    except Exception as e:
        return "телефон"  # Қате кеткен жағдайда ойын тоқтап қалмас үшін

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Сәлем! Мен Крокодил ойынын ойнатуға арналған ботпын.\n"
                          "Ойынды бастау үшін топта /game командасын жазыңыз.")

@bot.message_handler(commands=['game'])
def start_game(message):
    chat_id = message.chat.id
    
    # Егер бұл топта ойын жүріп жатса
    if chat_id in games and games[chat_id]['is_active']:
        leader_name = games[chat_id]['leader_name']
        bot.reply_to(message, f"❌ Ойын басталып кеткен! Қазіргі жүргізуші: {leader_name}. "
                              f"Ол жасырған сөзді табуға тырысыңыз!")
        return

    # Жаңа ойынды тіркеу
    leader_id = message.from_user.id
    leader_name = message.from_user.first_name
    
    # AI арқылы шынайы уақытта жаңа сөз генерациялау
    secret_word = get_ai_word()
    
    games[chat_id] = {
        'is_active': True,
        'leader_id': leader_id,
        'leader_name': leader_name,
        'secret_word': secret_word
    }
    
    # Жүргізушіге сөзді жеке чатына (личкасына) жіберу
    try:
        bot.send_message(leader_id, f"🎮 Сіз Крокодил ойынының жүргізушісі болдыңыз!\n"
                                    f"Жасанды интеллект сізге мына сөзді таңдады: **{secret_word}**\n\n"
                                    f"Топқа барып, бұл сөзді ишарамен, суретпен немесе түсіндірмемен сипаттаңыз. "
                                    f"Топта бұл сөзді тікелей жазбаңыз!")
        
        # Топқа хабарлама жіберу
        bot.send_message(chat_id, f"🎮 Ойын басталды! Жүргізуші: {leader_name}.\n"
                                  f"Бот жүргізушінің жеке чатына AI ойлап тапқан жасырын сөзді жіберді. "
                                  f"Кім бірінші тапса, сол келесі жүргізуші болады!")
    except Exception as e:
        games[chat_id]['is_active'] = False
        bot.reply_to(message, f"❌ {leader_name}, ойынды бастау үшін алдымен боттың жеке чатына кіріп, "
                              f"**Старт (/start)** батырмасын басыңыз. Сосын барып топта қайтадан /game жазыңыз.")

@bot.message_handler(commands=['stopgame'])
def stop_game(message):
    chat_id = message.chat.id
    
    if chat_id not in games or not games[chat_id]['is_active']:
        bot.reply_to(message, "❌ Қазір ешқандай белсенді ойын жүріп жатқан жоқ.")
        return
        
    # Ойынды тек жүргізуші тоқтата алады
    user_id = message.from_user.id
    if user_id == games[chat_id]['leader_id']:
        word = games[chat_id]['secret_word']
        games[chat_id]['is_active'] = False
        bot.reply_to(message, f"🛑 Ойын тоқтатылды. AI жасырған сөз мынау еді: {word}")
    else:
        bot.reply_to(message, "❌ Ойынды тек қазіргі жүргізуші ғана тоқтата алады!")

@bot.message_handler(func=lambda message: True)
def check_word(message):
    chat_id = message.chat.id
    
    # Егер бұл топта ойын белсенді болмаса, өткізіп жібереміз
    if chat_id not in games or not games[chat_id]['is_active']:
        return
        
    user_id = message.from_user.id
    user_text = message.text.strip().lower()
    
    # Жүргізушінің өзі жасырын сөзді топқа жазып қойса
    if user_id == games[chat_id]['leader_id']:
        if user_text == games[chat_id]['secret_word']:
            bot.reply_to(message, "🤫 Жүргізуші, жасырын сөзді өзіңіз чатқа жазбаңыз!")
        return

    # Егер басқа ойыншы сөзді тапса
    if user_text == games[chat_id]['secret_word']:
        winner_name = message.from_user.first_name
        correct_word = games[chat_id]['secret_word']
        
        bot.send_message(chat_id, f"🎉 Керемет! {winner_name} жасырын сөзді тапты!\n"
                                  f"AI жасырған жауап: **{correct_word}**.\n\n"
                                  f"Енді келесі ойынды бастау үшін топқа /game деп жазыңыз.")
        games[chat_id]['is_active'] = False

# ========================================================
# VERCEL WEBHOOK БАПТАУЛАРЫ
# ========================================================
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Forbidden', 403

if __name__ == "__main__":
    app.run()
