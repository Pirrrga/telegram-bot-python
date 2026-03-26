import telebot
import json
import os
from datetime import datetime

# ТОКЕН БЕРЁМ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (добавим позже)
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'finance_data.json'

# ========== РАБОТА С ДАННЫМИ ==========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_data(user_id):
    data = load_data()
    if user_id not in data:
        data[user_id] = {
            'balance': 0,
            'transactions': [],
            'budget': None,
            'goals': {}
        }
        save_data(data)
    return data[user_id]

def save_user_data(user_id, user_data):
    data = load_data()
    data[user_id] = user_data
    save_data(data)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_week_range():
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start.strftime("%d.%m"), end.strftime("%d.%m")

def get_month_stats(transactions):
    current_month = datetime.now().strftime("%m")
    month_income = 0
    month_expense = 0
    for t in transactions:
        if t['date'][3:5] == current_month:
            if t['type'] == 'income':
                month_income += t['amount']
            else:
                month_expense += t['amount']
    return month_income, month_expense

def get_category_stats(transactions):
    stats = {}
    for t in transactions:
        if t['type'] == 'expense':
            cat = t['category']
            stats[cat] = stats.get(cat, 0) + t['amount']
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    get_user_data(user_id)
    
    welcome_text = (
        "🌟 *Добро пожаловать в Финансового Помощника!* 🌟\n\n"
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я помогу тебе контролировать доходы и расходы, "
        "ставить финансовые цели и не выходить за рамки бюджета.\n\n"
        "📌 *Основные команды:*\n"
        "/balance - текущий баланс 💰\n"
        "/history - история операций 📜\n"
        "/stats - статистика по категориям 📊\n"
        "/week - статистика за неделю 📅\n"
        "/month - статистика за месяц 📆\n"
        "/set_budget - установить бюджет 🎯\n"
        "/check_budget - проверить бюджет ⚠️\n"
        "/goal - поставить финансовую цель 🏆\n"
        "/goals - мои цели 🎯\n"
        "/delete_last - удалить последнюю операцию 🗑️\n"
        "/reset - сбросить все данные 🔄\n"
        "/help - все команды 📖\n\n"
        "💡 *Как записывать:* просто напиши сообщение\n"
        "`+1000 Зарплата` или `-500 Продукты`"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "📖 *Полный список команд:*\n\n"
        "💰 *Основные:*\n"
        "/balance - показать текущий баланс\n"
        "/history - последние 10 операций\n\n"
        "📊 *Статистика:*\n"
        "/stats - расходы по категориям\n"
        "/week - статистика за текущую неделю\n"
        "/month - статистика за текущий месяц\n\n"
        "🎯 *Бюджет и цели:*\n"
        "/set_budget - установить месячный бюджет\n"
        "/check_budget - проверить расходы по бюджету\n"
        "/goal - поставить финансовую цель\n"
        "/goals - список твоих целей\n\n"
        "🛠️ *Управление:*\n"
        "/delete_last - удалить последнюю операцию\n"
        "/reset - сбросить все данные\n\n"
        "💡 *Быстрая запись:* отправь сообщение\n"
        "`+1000 Зарплата` или `-500 Продукты`"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    balance = user_data['balance']
    
    if balance >= 0:
        balance_text = f"✅ *{balance}* руб."
    else:
        balance_text = f"❌ *{balance}* руб."
    
    advice = ""
    if balance < 0:
        advice = "\n\n⚠️ *Совет:* У тебя отрицательный баланс! Пора сократить расходы."
    elif balance < 5000:
        advice = "\n\n💡 *Совет:* Начни копить. Откладывай хотя бы 10% от доходов."
    elif balance < 20000:
        advice = "\n\n👍 *Совет:* Хорошо! Продолжай в том же духе."
    else:
        advice = "\n\n🎉 *Совет:* Отлично! Ты финансово грамотен!"
    
    bot.reply_to(message, f"💰 *Твой баланс:* {balance_text}{advice}", parse_mode='Markdown')

@bot.message_handler(commands=['history'])
def history(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    transactions = user_data['transactions']
    
    if not transactions:
        bot.reply_to(message, "📭 *История операций пуста.*\nДобавь первую операцию: +1000 Зарплата", parse_mode='Markdown')
        return
    
    text = "📋 *Последние 10 операций:*\n"
    text += "┌─────────────────────────┐\n"
    
    for t in transactions[-10:]:
        sign = "➕" if t['type'] == 'income' else "➖"
        amount_sign = "+" if t['type'] == 'income' else "-"
        text += f"│ {sign} {amount_sign}{t['amount']} | {t['category']}\n"
        text += f"│   📅 {t['date']}\n"
        text += "├─────────────────────────┤\n"
    
    text += "└─────────────────────────┘"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    transactions = user_data['transactions']
    stats = get_category_stats(transactions)
    
    if not stats:
        bot.reply_to(message, "📊 *Нет данных для статистики.*\nДобавь расходы: -500 Продукты", parse_mode='Markdown')
        return
    
    text = "📊 *Твои расходы по категориям:*\n\n"
    total = sum(stats.values())
    
    for cat, amount in list(stats.items())[:10]:
        percent = (amount / total * 100) if total > 0 else 0
        bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
        text += f"📌 *{cat}*: {amount} руб. ({percent:.0f}%)\n"
        text += f"   {bar}\n\n"
    
    text += f"💰 *Всего расходов:* {total} руб."
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['week'])
def week_stats(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    transactions = user_data['transactions']
    
    week_start, week_end = get_week_range()
    week_income = 0
    week_expense = 0
    
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    for t in transactions:
        t_date = datetime.strptime(t['date'], "%d.%m.%Y %H:%M")
        if t_date >= week_ago:
            if t['type'] == 'income':
                week_income += t['amount']
            else:
                week_expense += t['amount']
    
    text = (
        f"📅 *Статистика за неделю* ({week_start} - {week_end})\n\n"
        f"✅ Доходы: +{week_income} руб.\n"
        f"❌ Расходы: -{week_expense} руб.\n"
        f"📈 Итог: {week_income - week_expense} руб.\n\n"
    )
    
    if week_expense > week_income:
        text += "⚠️ *Внимание:* Расходы превышают доходы!"
    else:
        text += "👍 *Молодец!* Ты в плюсе за эту неделю."
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['month'])
def month_stats(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    transactions = user_data['transactions']
    
    month_income, month_expense = get_month_stats(transactions)
    current_month = datetime.now().strftime("%B %Y")
    
    text = (
        f"📆 *Статистика за {current_month}*\n\n"
        f"✅ Доходы: +{month_income} руб.\n"
        f"❌ Расходы: -{month_expense} руб.\n"
        f"📈 Итог: {month_income - month_expense} руб.\n\n"
    )
    
    if month_expense > month_income:
        text += "⚠️ *Внимание:* Расходы превышают доходы!"
    else:
        text += "👍 *Молодец!* Ты в плюсе за этот месяц."
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['set_budget'])
def set_budget(message):
    bot.reply_to(message, "🎯 *Установи бюджет на месяц*\n\nПросто отправь сообщение с суммой, например:\n`50000`", parse_mode='Markdown')
    bot.register_next_step_handler(message, save_budget)

def save_budget(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    
    try:
        budget = int(message.text.strip())
        user_data['budget'] = budget
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"✅ *Бюджет установлен:* {budget} руб. на месяц!\nИспользуй /check_budget, чтобы следить за расходами.", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ *Ошибка:* Нужно отправить число.\nПопробуй /set_budget заново.", parse_mode='Markdown')

@bot.message_handler(commands=['check_budget'])
def check_budget(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    budget = user_data.get('budget')
    
    if not budget:
        bot.reply_to(message, "⚠️ *Бюджет не установлен.*\nИспользуй /set_budget", parse_mode='Markdown')
        return
    
    month_expense = get_month_stats(user_data['transactions'])[1]
    remaining = budget - month_expense
    percent = (month_expense / budget * 100) if budget > 0 else 0
    
    text = f"🎯 *Месячный бюджет:* {budget} руб.\n"
    text += f"💸 *Потрачено:* {month_expense} руб. ({percent:.0f}%)\n"
    text += f"✅ *Осталось:* {remaining} руб.\n\n"
    
    if percent > 90:
        text += "⚠️ *Внимание!* Бюджет почти исчерпан!"
    elif percent > 70:
        text += "⚡ *Совет:* Пора сокращать расходы."
    elif percent > 50:
        text += "📊 *Норм:* Укладываешься в бюджет."
    else:
        text += "🎉 *Отлично!* Ты хорошо контролируешь расходы!"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['goal'])
def set_goal(message):
    bot.reply_to(message, "🏆 *Поставь финансовую цель*\n\nОтправь сообщение в формате:\n`Цель|Сумма`\n\nПример:\n`Накопить на телефон|30000`", parse_mode='Markdown')
    bot.register_next_step_handler(message, save_goal)

def save_goal(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    
    try:
        parts = message.text.split('|')
        goal_name = parts[0].strip()
        goal_amount = int(parts[1].strip())
        
        user_data['goals'][goal_name] = {
            'target': goal_amount,
            'saved': 0,
            'created': datetime.now().strftime("%d.%m.%Y")
        }
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"✅ *Цель поставлена:* {goal_name}\n🎯 Нужно накопить: {goal_amount} руб.\n\nСледи за прогрессом через /goals", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ *Ошибка:* Неправильный формат.\nИспользуй: `Название цели|Сумма`", parse_mode='Markdown')

@bot.message_handler(commands=['goals'])
def show_goals(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    goals = user_data.get('goals', {})
    
    if not goals:
        bot.reply_to(message, "🏆 *У тебя пока нет целей.*\nИспользуй /goal, чтобы поставить первую!", parse_mode='Markdown')
        return
    
    text = "🏆 *Твои финансовые цели:*\n\n"
    balance = user_data['balance']
    
    for name, goal in goals.items():
        saved = min(goal['saved'], goal['target'])
        percent = (saved / goal['target'] * 100) if goal['target'] > 0 else 0
        bar = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
        text += f"📌 *{name}*\n"
        text += f"   Цель: {goal['target']} руб.\n"
        text += f"   Накоплено: {saved} руб. ({percent:.0f}%)\n"
        text += f"   [{bar}]\n\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['delete_last'])
def delete_last(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    transactions = user_data['transactions']
    
    if not transactions:
        bot.reply_to(message, "📭 *Нет операций для удаления.*", parse_mode='Markdown')
        return
    
    last = transactions.pop()
    if last['type'] == 'income':
        user_data['balance'] -= last['amount']
    else:
        user_data['balance'] += last['amount']
    
    save_user_data(user_id, user_data)
    bot.reply_to(message, f"🗑️ *Удалено:* {last['amount']} руб. ({last['category']})\n📅 Дата: {last['date']}", parse_mode='Markdown')

@bot.message_handler(commands=['reset'])
def reset(message):
    bot.reply_to(message, "⚠️ *ВНИМАНИЕ!*\nЭто удалит ВСЕ твои данные: баланс, историю, бюджет, цели.\n\nЕсли ты уверен, отправь `ДА`", parse_mode='Markdown')
    bot.register_next_step_handler(message, confirm_reset)

def confirm_reset(message):
    if message.text.strip().upper() == 'ДА':
        user_id = str(message.from_user.id)
        save_user_data(user_id, {
            'balance': 0,
            'transactions': [],
            'budget': None,
            'goals': {}
        })
        bot.reply_to(message, "✅ *Все данные сброшены.*\nНачни с /start", parse_mode='Markdown')
    else:
        bot.reply_to(message, "✅ *Сброс отменён.*", parse_mode='Markdown')

# ========== ОБРАБОТКА СООБЩЕНИЙ (БЫСТРАЯ ЗАПИСЬ) ==========
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    user_data = get_user_data(user_id)
    
    parts = text.split(maxsplit=1)
    
    if len(parts) == 2 and parts[0][0] in '+-' and parts[0][1:].isdigit():
        amount = int(parts[0][1:])
        category = parts[1]
        
        if parts[0][0] == '+':
            user_data['balance'] += amount
            t_type = 'income'
        else:
            user_data['balance'] -= amount
            t_type = 'expense'
            
            # Обновляем прогресс целей (если есть)
            for goal_name, goal in user_data.get('goals', {}).items():
                if goal['saved'] < goal['target']:
                    # Можно настроить авто-накопление, но пока просто отображаем
                    pass
        
        transaction = {
            'type': t_type,
            'amount': amount,
            'category': category,
            'date': datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        user_data['transactions'].append(transaction)
        save_user_data(user_id, user_data)
        
        # Разные реакции в зависимости от суммы
        if amount >= 10000:
            reaction = "🎉 Ого, крупная сумма!"
        elif amount >= 5000:
            reaction = "👍 Отлично!"
        elif t_type == 'expense' and amount > 1000:
            reaction = "💸 Это была крупная трата..."
        else:
            reaction = "✅ Готово!"
        
        bot.reply_to(message, f"{reaction}\n📝 Записано: {parts[0]} {category}\n💰 Баланс: {user_data['balance']} руб.")
        
        # Проверка бюджета при расходе
        if t_type == 'expense' and user_data.get('budget'):
            month_expense = get_month_stats(user_data['transactions'])[1]
            budget = user_data['budget']
            if month_expense > budget:
                bot.reply_to(message, "⚠️ *Внимание!* Ты превысил месячный бюджет!", parse_mode='Markdown')
            elif month_expense > budget * 0.8:
                bot.reply_to(message, "⚡ *Совет:* Осталось всего 20% бюджета на этот месяц!", parse_mode='Markdown')
    else:
        # Если сообщение не распознано
        bot.reply_to(message, "❓ *Не понимаю формат.*\n\n📝 Для записи используй:\n`+1000 Зарплата` или `-500 Продукты`\n\n📋 Список команд: /help", parse_mode='Markdown')

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 МЕГА-БОТ ЗАПУЩЕН!")
    print("Доступные команды: /start, /help, /balance, /history, /stats, /week, /month, /set_budget, /check_budget, /goal, /goals, /delete_last, /reset")
    bot.polling(none_stop=True)
