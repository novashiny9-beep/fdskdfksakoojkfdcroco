import telebot
import random
import time

# БОТ БАПТАУЛАРЫ
TOKEN = '8295067174:AAE5q4O4VkbKBbjVITVzAX-Tkb8Q9OMMzUk'
bot = telebot.TeleBot(TOKEN)

# Әр топтың ойын күйін бөлек сақтайтын сөздік
games = {}

# НАҚТЫ УАҚЫТТА КЕЗДЕЙСОҚ ТАҢДАЛАТЫН ҮЛКЕН ҚАЗАҚША СӨЗДЕР ҚОРЫ
WORDS_POOL = [
    "ғарышкер", "бағдаршам", "кітапхана", "компьютер", "суретші", "динозавр", "мұхит",
    "ұшақ", "тікұшақ", "велосипед", "кеме", "поезд", "телефон", "теледидар", "тоңазытқыш",
    "шаңсорғыш", "микрофон", "қолтырауын", "жолбарыс", "арыстан", "қасқыр", "түлкі", "аю",
    "піл", "керік", "маймыл", "дельфин", "акула", "бүркіт", "қарлығаш", "мұғалім", "дәрігер",
    "аспаз", "ғалым", "инженер", "полиция", "өртсөндіруші", "әнші", "биші", "спортшы",
    "футбол", "баскетбол", "теннис", "жүзу", "жүгіру", "шахмат", "домбыра", "гитара",
    "қобыз", "пиано", "барабан", "флейта", "алма", "банан", "құлпынай", "қарбыз",
    "қауын", "жүзім", "өрік", "шие", "қияр", "қызанақ", "сәбіз", "картоп",
    "пияз", "жаңбыр", "қар", "бұлт", "найзағай", "дауыл", "күн", "ай",
    "жұлдыз", "комета", "планета", "теңіз", "көл", "өзен", "сарқырама", "тау",
    "орман", "шөл", "үңгір", "арал", "қала", "ауыл", "мектеп", "университет",
    "мұражай", "театр", "дүкен", "базар", "саябақ", "стадион", "аурухана", "дәріхана",
    "қонақүй", "мейрамхана", "дәмхана", "кітап", "дәптер", "қалам", "қарындаш", "өшіргіш",
    "сызғыш", "желім", "қайшы", "сөмке", "парта", "тақта", "бор", "сағат",
    "көзілдірік", "кілт", "әмиян", "қолшатыр", "айна", "тарақ", "сабын", "сүлгі",
    "жастық", "көрпе", "төсек", "үстел", "орындық", "диван", "шкаф", "есік",
    "терезе", "қабырға", "шатыр", "еден", "кілем", "перде", "сурет", "гүлзар"
]

def generate_random_word():
    shuffled_list = WORDS_POOL.copy()
    random.shuffle(shuffled_list)
    return random.choice(shuffled_list)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Сәлем! Мен Крокодил ойынын ойнатуға арналған ботпын.\n"
                          "Ойынды бастау үшін топта /game командасын жазыңыз.")

@bot.message_handler(commands=['game'])
def start_game(message):
    chat_id = message.chat.id
    
    if chat_id in games and games[chat_id]['is_active']:
        leader_name = games[chat_id]['leader_name']
        bot.reply_to(message, f"❌ Ойын басталып кеткен! Қазіргі жүргізуші: {leader_name}. "
                              f"Ол жасырған сөзді табуға тырысыңыз!")
        return

    leader_id = message.from_user.id
    leader_name = message.from_user.first_name
    secret_word = generate_random_word()
    
    games[chat_id] = {
        'is_active': True,
        'leader_id': leader_id,
        'leader_name': leader_name,
        'secret_word': secret_word.lower()
    }
    
    try:
        bot.send_message(leader_id, f"🎮 Сіз Крокодил ойынының жүргізушісі болдыңыз!\n"
                                    f"Сіздің жасырын сөзіңіз: **{secret_word}**\n\n"
                                    f"Топқа барып, бұл сөзді ишарамен, суретпен немесе түсіндірмемен сипаттаңыз.")
        
        bot.send_message(chat_id, f"🎮 Ойын басталды! Жүргізуші: {leader_name}.\n"
                                  f"Бот жүргізушінің жеке чатына жасырын сөзді жіберді. "
                                  f"Кім бірінші тапса, сол келесі жүргізуші болады!")
    except Exception as e:
        games[chat_id]['is_active'] = False
        bot.reply_to(message, f"❌ {leader_name}, ойынды бастау үшін алдымен боттың жеке чатына кіріп, "
                              f"**Старт (/start)** батырмасын басыңыз.")

@bot.message_handler(commands=['stopgame'])
def stop_game(message):
    chat_id = message.chat.id
    if chat_id not in games or not games[chat_id]['is_active']:
        bot.reply_to(message, "❌ Қазір ешқандай белсенді ойын жүріп жатқан жоқ.")
        return
        
    user_id = message.from_user.id
    if user_id == games[chat_id]['leader_id']:
        word = games[chat_id]['secret_word']
        games[chat_id]['is_active'] = False
        bot.reply_to(message, f"🛑 Ойын тоқтатылды. Жасырған сөз мынау еді: {word}")
    else:
        bot.reply_to(message, "❌ Ойынды тек қазіргі жүргізуші ғана тоқтата алады!")

@bot.message_handler(func=lambda message: True)
def check_word(message):
    chat_id = message.chat.id
    if chat_id not in games or not games[chat_id]['is_active']:
        return
        
    user_id = message.from_user.id
    user_text = message.text.strip().lower()
    
    if user_id == games[chat_id]['leader_id']:
        if user_text == games[chat_id]['secret_word']:
            bot.reply_to(message, "🤫 Жүргізуші, жасырын сөзді өзіңіз чатқа жазбаңыз!")
        return

    if user_text == games[chat_id]['secret_word']:
        winner_name = message.from_user.first_name
        correct_word = games[chat_id]['secret_word']
        
        bot.send_message(chat_id, f"🎉 Керемет! {winner_name} жасырын сөзді тапты!\n"
                                  f"Жауап: **{correct_word}**.\n\n"
                                  f"Енді келесі ойынды бастау үшін топқа /game деп жазыңыз.")
        games[chat_id]['is_active'] = False

# ЕҢ СЕНІМДІ ІСКЕ ҚОСУ ӘДІСІ
if __name__ == "__main__":
    print("Бот сәтті қосылды...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
