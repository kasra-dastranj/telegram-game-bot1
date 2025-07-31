import telebot
from telebot import types
import json
import sqlite3
from datetime import datetime
import os

# Bot token from BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual token
GAME_URL = "https://your-website.com/index.html"  # Replace with your game URL

bot = telebot.TeleBot(BOT_TOKEN)

# Database setup
def init_db():
    conn = sqlite3.connect('game_scores.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            score INTEGER,
            high_score INTEGER,
            date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_score(user_id, username, first_name, score, high_score):
    conn = sqlite3.connect('game_scores.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO scores (user_id, username, first_name, score, high_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, score, high_score))
    
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    conn = sqlite3.connect('game_scores.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT first_name, username, MAX(score) as best_score
        FROM scores 
        GROUP BY user_id 
        ORDER BY best_score DESC 
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return results

@bot.message_handler(commands=['start'])
def start_game(message):
    user = message.from_user
    
    welcome_text = f"""
🎯 سلام {user.first_name}!

به بازی **تیراندازی اداری** خوش اومدی!

🎮 در این بازی:
• روی چهره‌ها کلیک کن تا امتیاز بگیری
• مراقب پرهام باش! (🤡 قرمز - بدون امتیاز ولی سورپرایز داره!)
• 60 ثانیه وقت داری تا بیشترین امتیاز رو بگیری

دستورات:
/play - شروع بازی
/leaderboard - جدول امتیازها
/help - راهنما
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Game button
    game_button = types.InlineKeyboardButton(
        "🎯 شروع بازی", 
        web_app=types.WebAppInfo(url=GAME_URL)
    )
    
    # Leaderboard button
    leaderboard_button = types.InlineKeyboardButton(
        "🏆 جدول امتیازها",
        callback_data="leaderboard"
    )
    
    # Share button
    share_button = types.InlineKeyboardButton(
        "📤 دعوت دوستان",
        switch_inline_query="بیا تو این بازی من رو شکست بده! 🎯"
    )
    
    markup.add(game_button)
    markup.add(leaderboard_button, share_button)
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['play'])
def play_command(message):
    markup = types.InlineKeyboardMarkup()
    game_button = types.InlineKeyboardButton(
        "🎯 شروع بازی", 
        web_app=types.WebAppInfo(url=GAME_URL)
    )
    markup.add(game_button)
    
    bot.send_message(
        message.chat.id,
        "🎮 روی دکمه زیر کلیک کن تا بازی شروع بشه:",
        reply_markup=markup
    )

@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    leaderboard = get_leaderboard()
    
    if not leaderboard:
        bot.send_message(
            message.chat.id,
            "🏆 هنوز کسی بازی نکرده!\nاولین نفر باش و رکورد بزن! 🎯"
        )
        return
    
    leaderboard_text = "🏆 **جدول برترین بازیکنان:**\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (first_name, username, score) in enumerate(leaderboard):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = first_name or (f"@{username}" if username else "ناشناس")
        leaderboard_text += f"{medal} {name}: **{score}** امتیاز\n"
    
    markup = types.InlineKeyboardMarkup()
    play_button = types.InlineKeyboardButton(
        "🎯 من هم بازی کنم!",
        web_app=types.WebAppInfo(url=GAME_URL)
    )
    markup.add(play_button)
    
    bot.send_message(
        message.chat.id,
        leaderboard_text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🎯 **راهنمای بازی تیراندازی اداری**

🎮 **نحوه بازی:**
• روی چهره‌ها کلیک/تاچ کن
• هر هدف 10 امتیاز میده
• 60 ثانیه وقت داری

🤡 **مراقب پرهام باش!**
• شخصیت قرمز با نام PARHAM
• امتیاز نمیده ولی پیام خنده‌دار میده!
• صدای جیغ هم داره! 😂

🏆 **امتیازگیری:**
• هدف عادی = 10 امتیاز
• پرهام = 0 امتیاز (ولی سرگرمی!)

📱 **دستورات بات:**
/play - شروع بازی
/leaderboard - جدول امتیازها
/start - منوی اصلی
/help - این راهنما

موفق باشی! 🚀
"""
    
    markup = types.InlineKeyboardMarkup()
    play_button = types.InlineKeyboardButton(
        "🎯 شروع بازی",
        web_app=types.WebAppInfo(url=GAME_URL)
    )
    markup.add(play_button)
    
    bot.send_message(
        message.chat.id,
        help_text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard")
def callback_leaderboard(call):
    show_leaderboard(call.message)
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        # Parse game data sent from the web app
        data = json.loads(message.web_app_data.data)
        
        user = message.from_user
        score = data.get('score', 0)
        high_score = data.get('highScore', 0)
        action = data.get('action', '')
        
        if action == 'game_finished':
            # Save score to database
            save_score(
                user.id,
                user.username,
                user.first_name,
                score,
                high_score
            )
            
            # Send congratulations message
            if score > 0:
                congrats_text = f"""
🎉 **عالی {user.first_name}!**

🎯 امتیاز این بازی: **{score}**
🏆 بهترین امتیازت: **{high_score}**

{'🥇 رکورد جدید!' if score == high_score and score > 0 else ''}
"""
                
                markup = types.InlineKeyboardMarkup(row_width=2)
                
                play_again_button = types.InlineKeyboardButton(
                    "🔄 دوباره بازی",
                    web_app=types.WebAppInfo(url=GAME_URL)
                )
                
                leaderboard_button = types.InlineKeyboardButton(
                    "🏆 جدول امتیازها",
                    callback_data="leaderboard"
                )
                
                share_button = types.InlineKeyboardButton(
                    "📤 به اشتراک‌گذاری",
                    switch_inline_query=f"من تو بازی تیراندازی اداری {score} امتیاز گرفتم! بیا ببینم تو چقدر میگیری 🎯"
                )
                
                markup.add(play_again_button, leaderboard_button)
                markup.add(share_button)
                
                bot.send_message(
                    message.chat.id,
                    congrats_text,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            else:
                # No score
                bot.send_message(
                    message.chat.id,
                    "😅 این بار امتیازی نگرفتی!\nدوباره تلاش کن! 🎯"
                )
        
    except Exception as e:
        print(f"Error handling web app data: {e}")
        bot.send_message(
            message.chat.id,
            "❌ خطا در دریافت اطلاعات بازی!"
        )

@bot.inline_handler(func=lambda query: True)
def inline_query(query):
    try:
        results = []
        
        # Inline result for sharing the game
        game_result = types.InlineQueryResultArticle(
            id='1',
            title='🎯 بازی تیراندازی اداری',
            description='بازی سرگرم‌کننده تیراندازی - مراقب پرهام باش!',
            input_message_content=types.InputTextMessageContent(
                message_text=f"""
🎯 **بازی تیراندازی اداری**

🎮 بازی جذاب و سرگرم‌کننده!
🤡 مراقب پرهام باش - سورپرایز داره!
🏆 ببین کی بیشترین امتیاز رو میگیره!

برای شروع بازی روی دکمه زیر کلیک کن:
""",
                parse_mode='Markdown'
            ),
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "🎯 شروع بازی",
                    web_app=types.WebAppInfo(url=GAME_URL)
                )
            )
        )
        
        results.append(game_result)
        
        bot.answer_inline_query(query.id, results, cache_time=300)
        
    except Exception as e:
        print(f"Inline query error: {e}")

# Error handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    markup = types.InlineKeyboardMarkup()
    
    play_button = types.InlineKeyboardButton(
        "🎯 شروع بازی",
        web_app=types.WebAppInfo(url=GAME_URL)
    )
    
    help_button = types.InlineKeyboardButton(
        "❓ راهنما",
        callback_data="help"
    )
    
    markup.add(play_button)
    markup.add(help_button)
    
    bot.send_message(
        message.chat.id,
        "🎯 برای شروع بازی از دستور /start استفاده کن!",
        reply_markup=markup
    )

if __name__ == "__main__":
    print("🤖 Bot starting...")
    print(f"🌐 Game URL: {GAME_URL}")
    
    # Initialize database
    init_db()
    print("💾 Database initialized")
    
    # Start bot
    try:
        print("🚀 Bot is running...")
        bot.infinity_polling(timeout=60, long_polling_timeout=20)
    except Exception as e:
        print(f"❌ Bot error: {e}")

# Requirements to install:
# pip install pyTelegramBotAPI
