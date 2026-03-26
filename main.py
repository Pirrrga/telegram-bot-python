import telebot
import json
import os
from datetime import datetime

# ТОКЕН БЕРЁМ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (добавим позже)
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'finance_data.json'

def load_data():
    """Загружает данные из файла"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    """Сохраняет данные в файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
                 "Привет! Я твой финансовый помощник 🤖\n\n"
                 "📌 Команды:\n"
                 "/balance - показать баланс\n"
                 "/history - показать историю\n\n"
                 "💡 Как записывать:\n"
                 "Доход: +1000 Зарплата\n"
                 "Расход: -300 Такси")

@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data:
        data[user_id] = {'balance': 0, 'transactions': []}
        save_data(data)
    
    bot.reply_to(message, f"💰 Твой баланс: *{data[user_id]['balance']}* руб.", parse_mode='Markdown')

@bot.message_handler(commands=['history'])
def history(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data or not data[user_id]['transactions']:
        bot.reply_to(message, "📭 История операций пуста.")
        return
    
    text = "📋 *Последние операции:*\n"
    for t in data[user_id]['transactions'][-5:]:
        sign = "+" if t['type'] == 'income' else "-"
        text += f"{sign}{t['amount']} | {t['category']} ({t['date']})\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    data = load_data()
    
    if user_id not in data:
        data[user_id] = {'balance': 0, 'transactions': []}
    
    parts = text.split(maxsplit=1)
    
    if len(parts) == 2 and parts[0][0] in '+-' and parts[0][1:].isdigit():
        amount = int(parts[0][1:])
        category = parts[1]
        
        if parts[0][0] == '+':
            data[user_id]['balance'] += amount
            t_type = 'income'
        else:
            data[user_id]['balance'] -= amount
            t_type = 'expense'
        
        data[user_id]['transactions'].append({
            'type': t_type,
            'amount': amount,
            'category': category,
            'date': datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        save_data(data)
        
        bot.reply_to(message, f"✅ Записано: {parts[0]} {category}")
    else:
        bot.reply_to(message, "❓ Не понял формат.\nПиши например: +500 Еда или -200 Такси")

if __name__ == "__main__":
    print("🤖 Бот запущен и работает...")
    bot.polling(none_stop=True)
