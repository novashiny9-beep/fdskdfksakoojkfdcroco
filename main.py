import telebot
from flask import Flask, request
import random

# БОТ БАПТАУЛАРЫ
TOKEN = '8295067174:AAE5q4O4VkbKBbjVITVzAX-Tkb8Q9OMMzUk'  # Осы жерге өз токеніңізді жазыңыз
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ОЙЫН ДЕРЕКТЕРІ (Ойыншылар араласып кетпеуі үшін)
# Әр чаттың (группаның) ойын күйін бөлек сақтаймыз
games = {}

# КРОКОДИЛ ОЙЫНЫ ҮШІН СӨЗДЕР ТІЗІМІ
WORDS_POOL = [
    "алма", "кітап", "телефон", "машина", "ұшақ", "мектеп", "мұғалім", 
    "компьютер", "қалам", "доп", "ағаш", "сызығыш", "терезе", "мысық", 
    "ит", "аспан", "күн", "жаңбыр", "қар", "теңіз", "балық"
]

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
    secret_word = random.choice(WORDS_POOL)
    
    games[chat_id] = {
        'is_active': True,
        'leader_id': leader_id,
        'leader_name': leader_name,
        'secret_word': secret_word.lower()
    }
    
    # Жүргізушіге сөзді лс (личкасына) жіберу
    try:
        bot.send_message(leader_id, f"🎮 Сіз Крокодил ойынының жүргізушісі болдыңыз!\n"
                                    f"Сіздің жасырын сөзіңіз: **{secret_word}**\n\n"
                                    f"Топқа барып, бұл сөзді ишарамен, суретпен немесе түсіндірмемен сипаттаңыз. "
                                    f"Топта бұл сөзді тікелей жазбаңыз!")
        
        # Топқа хабарлама жіберу
        bot.send_message(chat_id, f"🎮 Ойын басталды! Жүргізуші: {leader_name}.\n"
                                  f"Бот жүргізушінің жеке чатына сөзді жіберді. "
                                  f"Кім бірінші тапса, сол келесі жүргізуші болады!")
    except Exception as e:
        # Егер жүргізуші ботқа личкада /start баспаған болса, хабарлама бармайды
        games[chat_id]['is_active'] = False
        bot.reply_to(message, f"❌ {leader_name}, ойынды бастау үшін алдымен боттың жеке чатына (@{bot.get_me().username}) кіріп, /start батырмасын басыңыз. Сосын барып топта /game жазыңыз.")

@bot.message_handler(commands=['stopgame'])
def stop_game(message):
    chat_id = message.chat.id
    
    if chat_id not in games or not games[chat_id]['is_active']:
        bot.reply_to(message, "❌ Қазір ешқандай белсенді ойын жүріп жатқан жоқ.")
        return
        
    # Ойынды тек жүргізуші немесе топ админі тоқтата алады
    user_id = message.from_user.id
    if user_id == games[chat_id]['leader_id']:
        word = games[chat_id]['secret_word']
        games[chat_id]['is_active'] = False
        bot.reply_to(message, f"🛑 Ойын тоқтатылды. Жасырын сөз мынау еді: {word}")
    else:
        bot.reply_to(message, "❌ Ойынды тек қазіргі жүргізуші ғана тоқтата алады!")

@bot.message_handler(func=lambda message: True)
def check_word(message):
    chat_id = message.chat.id
    
    # Егер бұл топта ойын белсенді болмаса, хабарламаларға мән бермейміз
    if chat_id not in games or not games[chat_id]['is_active']:
        return
        
    user_id = message.from_user.id
    user_text = message.text.strip().lower()
    
    # Жүргізушінің өзі жасырын сөзді топқа жазып қойса, қабылдамаймыз
    if user_id == games[chat_id]['leader_id']:
        if user_text == games[chat_id]['secret_word']:
            bot.reply_to(message, "🤫 Жүргізуші мырза, жасырын сөзді өзіңіз чатқа жазбаңыз!")
        return

    # Егер басқа ойыншы сөзді тапса
    if user_text == games[chat_id]['secret_word']:
        winner_name = message.from_user.first_name
        correct_word = games[chat_id]['secret_word']
        
        bot.send_message(chat_id, f"🎉 Керемет! {winner_name} жасырын сөзді тапты!\n"
                                  f"Жауап: **{correct_word}**.\n\n"
                                  f"Енді келесі ойынды бастау үшін топқа /game деп жазыңыз.")
        # Ойынды аяқтау
        games[chat_id]['is_active'] = False

# ========================================================
# VERCEL WEBHOOK БАПТАУЛАРЫ (Осы бөлім боттың өшпеуін қамтамасыз етеді)
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
