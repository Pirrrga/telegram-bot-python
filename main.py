import telebot
import json
import os
from datetime import datetime, timedelta

# ========== ТОКЕН ИЗ ПЕРЕМЕННЫХ ==========
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

def get_week_stats(transactions):
    week_ago = datetime.now() - timedelta(days=7)
    week_income = 0
    week_expense = 0
    for t in transactions:
        t_date = datetime.strptime(t['date'], "%d.%m.%Y %H:%M")
        if t_date >= week_ago:
            if t['type'] == 'income':
                week_income += t['amount']
            else:
                week_expense += t['amount']
    return week_income, week_expense

def get_category_stats(transactions):
    stats = {}
    for t in transactions:
        if t['type'] == 'expense':
            cat = t['category']
            stats[cat] = stats.get(cat, 0) + t['amount']
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

def get_daily_stats(transactions):
    today = datetime.now().strftime("%d.%m.%Y")
    today_income = 0
    today_expense = 0
    for t in transactions:
        if t['date'].startswith(today):
            if t['type'] == 'income':
                today_income += t['amount']
            else:
                today_expense += t['amount']
    return today_income, today_expense

def get_advice(balance, month_expense, budget):
    if balance < 0:
        return "⚠️ У тебя отрицательный баланс! Срочно сократи расходы!"
    elif balance < 5000:
        return "💡 Совет: начни откладывать хотя бы 10% от каждого дохода."
    elif balance < 20000:
        return "👍 Неплохо! Продолжай в том же духе."
    elif balance > 100000:
        return "🎉 Отлично! Ты финансово грамотен. Можешь подумать об инвестициях."
    else:
        return "✅ Хороший баланс! Так держать!"

def get_budget_advice(month_expense, budget):
    if not budget:
        return ""
    percent = (month_expense / budget * 100) if budget > 0 else 0
    if percent > 100:
        return f"⚠️ КРИТИЧНО! Ты превысил бюджет на {percent - 100:.0f}%!"
    elif percent > 90:
        return "⚠️ Внимание! Осталось меньше 10% бюджета!"
    elif percent > 70:
        return "⚡ Осталось 30% бюджета. Пора экономить!"
    elif percent > 50:
        return "📊 Ты на полпути. Укладываешься в бюджет."
    else:
        return "🎯 Отлично! Ты хорошо контролируешь расходы."

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    get_user_data(user_id)
    text = (
        "🌟 ФИНАНСОВЫЙ ПОМОЩНИК 🌟\n\n"
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я помогу тебе контролировать доходы и расходы, ставить цели и следить за бюджетом.\n\n"
        "📌 ОСНОВНЫЕ КОМАНДЫ:\n"
        "/balance - текущий баланс 💰\n"
        "/today - статистика за сегодня 📅\n"
        "/history - история операций 📜\n"
        "/stats - расходы по категориям 📊\n"
        "/week - статистика за неделю 📅\n"
        "/month - статистика за месяц 📆\n"
        "/set_budget - установить бюджет 🎯\n"
        "/check_budget - проверить бюджет ⚠️\n"
        "/goal - поставить финансовую цель 🏆\n"
        "/goals - мои цели 🎯\n"
        "/delete_last - удалить последнюю операцию 🗑️\n"
        "/reset - сбросить все данные 🔄\n"
        "/help - все команды 📖\n\n"
        "💡 КАК ЗАПИСЫВАТЬ:\n"
        "Доход: +1000 Зарплата\n"
        "Расход: -500 Продукты"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['help'])
def help_command(message):
    text = (
        "📖 ВСЕ КОМАНДЫ:\n\n"
        "💰 ОСНОВНЫЕ:\n"
        "/balance - показать текущий баланс\n"
        "/today - статистика за сегодня\n"
        "/history - последние 10 операций\n\n"
        "📊 СТАТИСТИКА:\n"
        "/stats - расходы по категориям\n"
        "/week - статистика за текущую неделю\n"
        "/month - статистика за текущий месяц\n\n"
        "🎯 БЮДЖЕТ И ЦЕЛИ:\n"
        "/set_budget - установить месячный бюджет\n"
        "/check_budget - проверить расходы по бюджету\n"
        "/goal - поставить финансовую цель\n"
        "/goals - список твоих целей\n\n"
        "🛠️ УПРАВЛЕНИЕ:\n"
        "/delete_last - удалить последнюю операцию\n"
        "/reset - сбросить все данные\n\n"
        "💡 БЫСТРАЯ ЗАПИСЬ:\n"
        "+1000 Зарплата\n"
        "-500 Продукты"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    bal = user_data['balance']
    month_income, month_expense = get_month_stats(user_data['transactions'])
    advice = get_advice(bal, month_expense, user_data.get('budget'))
    
    if bal >= 0:
        text = f"💰 БАЛАНС: +{bal} руб.\n\n📊 ЗА МЕСЯЦ:\n✅ Доходы: +{month_income} руб.\n❌ Расходы: -{month_expense} руб.\n📈 Итог: {month_income - month_expense} руб.\n\n{advice}"
    else:
        text = f"💰 БАЛАНС: {bal} руб.\n\n📊 ЗА МЕСЯЦ:\n✅ Доходы: +{month_income} руб.\n❌ Расходы: -{month_expense} руб.\n📈 Итог: {month_income - month_expense} руб.\n\n{advice}"
    
    bot.reply_to(message, text)

@bot.message_handler(commands=['today'])
def today_stats(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    today_income, today_expense = get_daily_stats(user_data['transactions'])
    
    text = (
        f"📅 СТАТИСТИКА ЗА СЕГОДНЯ ({datetime.now().strftime('%d.%m.%Y')})\n\n"
        f"✅ Доходы: +{today_income} руб.\n"
        f"❌ Расходы: -{today_expense} руб.\n"
        f"📈 Итог: {today_income - today_expense} руб."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['history'])
def history(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    transactions = user_data['transactions']
    
    if not transactions:
        bot.reply_to(message, "📭 История операций пуста. Добавь первую операцию: +1000 Зарплата")
        return
    
    text = "📋 ПОСЛЕДНИЕ 10 ОПЕРАЦИЙ:\n\n"
    for i, t in enumerate(transactions[-10:], 1):
        sign = "➕" if t['type'] == 'income' else "➖"
        amount_sign = "+" if t['type'] == 'income' else "-"
        text += f"{i}. {sign} {amount_sign}{t['amount']} | {t['category']}\n   📅 {t['date']}\n\n"
    
    bot.reply_to(message, text)

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    stats = get_category_stats(user_data['transactions'])
    
    if not stats:
        bot.reply_to(message, "📊 Нет данных для статистики. Добавь расходы: -500 Продукты")
        return
    
    text = "📊 РАСХОДЫ ПО КАТЕГОРИЯМ:\n\n"
    total = sum(stats.values())
    
    for cat, amount in list(stats.items())[:10]:
        percent = (amount / total * 100) if total > 0 else 0
        bar_length = int(percent / 5)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        text += f"📌 {cat}: {amount} руб. ({percent:.0f}%)\n   [{bar}]\n\n"
    
    text += f"💰 ВСЕГО РАСХОДОВ: {total} руб."
    bot.reply_to(message, text)

@bot.message_handler(commands=['week'])
def week_stats(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    week_income, week_expense = get_week_stats(user_data['transactions'])
    
    text = (
        f"📅 СТАТИСТИКА ЗА НЕДЕЛЮ\n\n"
        f"✅ Доходы: +{week_income} руб.\n"
        f"❌ Расходы: -{week_expense} руб.\n"
        f"📈 Итог: {week_income - week_expense} руб."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['month'])
def month_stats(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    month_income, month_expense = get_month_stats(user_data['transactions'])
    current_month = datetime.now().strftime("%B %Y")
    
    text = (
        f"📆 СТАТИСТИКА ЗА {current_month}\n\n"
        f"✅ Доходы: +{month_income} руб.\n"
        f"❌ Расходы: -{month_expense} руб.\n"
        f"📈 Итог: {month_income - month_expense} руб."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['set_budget'])
def set_budget(message):
    bot.reply_to(message, "🎯 УСТАНОВИ БЮДЖЕТ НА МЕСЯЦ\n\nОтправь сумму, например: 50000")
    bot.register_next_step_handler(message, save_budget)

def save_budget(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    
    try:
        budget = int(message.text.strip())
        user_data['budget'] = budget
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"✅ БЮДЖЕТ УСТАНОВЛЕН: {budget} руб.\n\nИспользуй /check_budget, чтобы следить за расходами.")
    except:
        bot.reply_to(message, "❌ ОШИБКА! Нужно отправить число.\nПопробуй /set_budget заново.")

@bot.message_handler(commands=['check_budget'])
def check_budget(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    budget = user_data.get('budget')
    
    if not budget:
        bot.reply_to(message, "⚠️ БЮДЖЕТ НЕ УСТАНОВЛЕН\nИспользуй /set_budget")
        return
    
    month_expense = get_month_stats(user_data['transactions'])[1]
    remaining = budget - month_expense
    percent = (month_expense / budget * 100) if budget > 0 else 0
    advice = get_budget_advice(month_expense, budget)
    
    text = (
        f"🎯 МЕСЯЧНЫЙ БЮДЖЕТ: {budget} руб.\n"
        f"💸 ПОТРАЧЕНО: {month_expense} руб. ({percent:.0f}%)\n"
        f"✅ ОСТАЛОСЬ: {remaining} руб.\n\n"
        f"{advice}"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['goal'])
def set_goal(message):
    bot.reply_to(message, "🏆 ПОСТАВЬ ФИНАНСОВУЮ ЦЕЛЬ\n\nФормат: Название|Сумма\n\nПример: Накопить на телефон|30000")
    bot.register_next_step_handler(message, save_goal)

def save_goal(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    
    try:
        parts = message.text.split('|')
        name = parts[0].strip()
        amount = int(parts[1].strip())
        
        user_data['goals'][name] = {
            'target': amount,
            'saved': 0,
            'created': datetime.now().strftime("%d.%m.%Y")
        }
        save_user_data(user_id, user_data)
        bot.reply_to(message, f"✅ ЦЕЛЬ ПОСТАВЛЕНА!\n\n🏆 {name}\n🎯 Нужно накопить: {amount} руб.\n\nСледи за прогрессом через /goals")
    except:
        bot.reply_to(message, "❌ ОШИБКА! Неправильный формат.\n\nИспользуй: Название|Сумма\nПример: Накопить на телефон|30000")

@bot.message_handler(commands=['goals'])
def show_goals(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    goals = user_data.get('goals', {})
    
    if not goals:
        bot.reply_to(message, "🏆 У ТЕБЯ НЕТ ЦЕЛЕЙ\nИспользуй /goal, чтобы поставить первую цель!")
        return
    
    text = "🏆 ТВОИ ФИНАНСОВЫЕ ЦЕЛИ:\n\n"
    balance = user_data['balance']
    
    for name, goal in goals.items():
        saved = min(goal['saved'], goal['target'])
        percent = (saved / goal['target'] * 100) if goal['target'] > 0 else 0
        bar_length = int(percent / 10)
        bar = "█" * bar_length + "░" * (10 - bar_length)
        remaining = goal['target'] - saved
        text += f"📌 {name}\n"
        text += f"   Цель: {goal['target']} руб.\n"
        text += f"   Накоплено: {saved} руб. ({percent:.0f}%)\n"
        text += f"   Осталось: {remaining} руб.\n"
        text += f"   [{bar}]\n\n"
    
    text += f"💰 Твой текущий баланс: {balance} руб."
    bot.reply_to(message, text)

@bot.message_handler(commands=['delete_last'])
def delete_last(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)
    transactions = user_data['transactions']
    
    if not transactions:
        bot.reply_to(message, "📭 НЕТ ОПЕРАЦИЙ ДЛЯ УДАЛЕНИЯ")
        return
    
    last = transactions.pop()
    if last['type'] == 'income':
        user_data['balance'] -= last['amount']
        type_text = "ДОХОД"
    else:
        user_data['balance'] += last['amount']
        type_text = "РАСХОД"
    
    save_user_data(user_id, user_data)
    
    text = (
        f"🗑️ УДАЛЕНО:\n"
        f"Тип: {type_text}\n"
        f"Сумма: {last['amount']} руб.\n"
        f"Категория: {last['category']}\n"
        f"Дата: {last['date']}\n\n"
        f"💰 Новый баланс: {user_data['balance']} руб."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['reset'])
def reset(message):
    bot.reply_to(message, "⚠️ ВНИМАНИЕ!\n\nЭто удалит ВСЕ твои данные: баланс, историю, бюджет, цели.\n\nЕсли ты уверен, отправь: ДА")
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
        bot.reply_to(message, "✅ ВСЕ ДАННЫЕ СБРОШЕНЫ\n\nНачни с /start")
    else:
        bot.reply_to(message, "✅ СБРОС ОТМЕНЁН")

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
            type_emoji = "➕ ДОХОД"
        else:
            user_data['balance'] -= amount
            t_type = 'expense'
            type_emoji = "➖ РАСХОД"
        
        transaction = {
            'type': t_type,
            'amount': amount,
            'category': category,
            'date': datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        user_data['transactions'].append(transaction)
        save_user_data(user_id, user_data)
        
        # Проверка бюджета при расходе
        budget_warning = ""
        if t_type == 'expense' and user_data.get('budget'):
            month_expense = get_month_stats(user_data['transactions'])[1]
            budget = user_data['budget']
            if month_expense > budget:
                budget_warning = "\n\n⚠️ ВНИМАНИЕ! Ты превысил месячный бюджет!"
            elif month_expense > budget * 0.8:
                budget_warning = f"\n\n⚡ СОВЕТ: Осталось всего {budget - month_expense} руб. бюджета на этот месяц!"
        
        # Разные реакции в зависимости от суммы
        if amount >= 10000:
            reaction = "🎉 Ого, крупная сумма!"
        elif amount >= 5000:
            reaction = "👍 Отлично!"
        elif t_type == 'expense' and amount > 1000:
            reaction = "💸 Это была крупная трата..."
        else:
            reaction = "✅ Готово!"
        
        text = (
            f"{reaction}\n"
            f"{type_emoji} {amount} руб. | {category}\n"
            f"💰 Баланс: {user_data['balance']} руб."
            f"{budget_warning}"
        )
        bot.reply_to(message, text)
        
    else:
        text = (
            "❓ НЕ ПОНИМАЮ ФОРМАТ\n\n"
            "📝 ДЛЯ ЗАПИСИ ИСПОЛЬЗУЙ:\n"
            "Доход: +1000 Зарплата\n"
            "Расход: -500 Продукты\n\n"
            "📋 ВСЕ КОМАНДЫ: /help"
        )
        bot.reply_to(message, text)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 ФИНАНСОВЫЙ БОТ ЗАПУЩЕН!")
    print("✅ Все команды загружены")
    print("✅ Ожидание сообщений...")
    bot.polling(none_stop=True)
