import os
import telebot
import requests
import time
from telebot import types
from bs4 import BeautifulSoup as soup

# Render-এ এনভায়রনমেন্ট ভেরিয়েবল হিসেবে BOT_TOKEN সেট করবেন
TOKEN = os.getenv('8789592665:AAFX1Nlx6ArxpR3kgbTNWIerVN9V6GyeCMc')
bot = telebot.TeleBot(TOKEN)

# --- Headers Functions ---
def get_fb_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'authority': 'm.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://m.facebook.com',
        'referer': 'https://m.facebook.com/',
    }

def get_ig_headers():
    return {
        'host': 'www.instagram.com',
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.instagram.com',
        'referer': 'https://www.instagram.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'x-csrftoken': 'CW2Q00bvaKhSGobrrr0Q1U', # আপনার দেওয়া টোকেন 
        'x-ig-app-id': '936619743392459',
        'x-instagram-ajax': '1012029991',
        'x-requested-with': 'XMLHttpRequest',
    }

# --- Login Logic Functions ---

def fb_login_logic(email, password):
    session = requests.Session()
    try:
        res = session.get('https://m.facebook.com/login/', headers=get_fb_headers(), timeout=30)
        parser = soup(res.text, 'html.parser')
        form = parser.find('form', {'method': 'post'})
        
        if not form:
            return "❌ ফেইসবুক থেকে লগিন ফর্ম পাওয়া যায়নি। কিছুক্ষণ পর আবার চেষ্টা করুন।"

        data = {
            'lsd': form.find('input', {'name': 'lsd'})['value'],
            'jazoest': form.find('input', {'name': 'jazoest'})['value'],
            'm_ts': form.find('input', {'name': 'm_ts'})['value'],
            'li': form.find('input', {'name': 'li'})['value'],
            'try_number': '0',
            'unrecognized_tries': '0',
            'email': email,
            'pass': password,
            'login': 'Log In'
        }
        
        session.post('https://m.facebook.com/login/device-based/regular/login/', 
                     data=data, headers=get_fb_headers(), timeout=30)
        
        cookies = session.cookies.get_dict()
        if 'c_user' in cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            return f"✅ **Facebook লগিন সফল!**\n\n🆔 **User ID:** `{cookies['c_user']}`\n\n🍪 **Cookies:**\n`{cookie_str}`"
        elif 'checkpoint' in cookies:
            return "⚠️ **লগিন ফেইল!** আপনার একাউন্টটি Checkpoint-এ আটকে গেছে।"
        else:
            return "❌ **লগিন ফেইল!** ইউজারনেম বা পাসওয়ার্ড ভুল অথবা সার্ভার ব্লক করেছে।"
            
    except Exception as e:
        return f"❌ এরর: {str(e)}"

def ig_login_logic(email, password):
    session = requests.Session()
    try:
        data = {
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:&:{password}',
            'optIntoOneTap': 'false',
            'queryParams': '{}',
            'username': email,
        }
        
        response = session.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/', 
                                headers=get_ig_headers(), data=data, timeout=30)
        
        cookies = session.cookies.get_dict()
        
        if '"authenticated":true' in response.text and 'ds_user_id' in cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            return f"✅ **Instagram লগিন সফল!**\n\n🆔 **User ID:** `{cookies['ds_user_id']}`\n\n🍪 **Cookies:**\n`{cookie_str}`"
        elif '"authenticated":false' in response.text:
            return "❌ **লগিন ফেইল!** আপনার ইমেইল বা পাসওয়ার্ড ভুল।"
        else:
            return "⚠️ **লগিন ফেইল!** কুকিজ পাওয়া যায়নি। একাউন্ট ব্লক হতে পারে অথবা টু-ফ্যাক্টর অন করা আছে।"
            
    except Exception as e:
        return f"❌ এরর: {str(e)}"

# --- Bot Handlers ---

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📘 Facebook Cookies", callback_data='fb')
    btn2 = types.InlineKeyboardButton("📸 Instagram Cookies", callback_data='ig')
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, 
                     f"👋 **স্বাগতম!**\n\nএটি একটি সোশ্যাল লগিন কুকিজ এক্সট্রাক্টর বট। নিচের বাটন থেকে আপনার প্লাটফর্ম সিলেক্ট করুন।", 
                     reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'fb':
        msg = bot.send_message(call.message.chat.id, "📧 আপনার **Facebook** Email/Username এবং Password এভাবে পাঠান:\n\n`email:password`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: process_login(m, 'fb'))
        
    elif call.data == 'ig':
        msg = bot.send_message(call.message.chat.id, "📸 আপনার **Instagram** Username/Email এবং Password এভাবে পাঠান:\n\n`username:password`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: process_login(m, 'ig'))

def process_login(message, platform):
    try:
        if ':' not in message.text:
            bot.reply_to(message, "❌ ভুল ফরম্যাট! দয়া করে `email:password` এভাবে পাঠান।")
            return
            
        credentials = message.text.split(':')
        email = credentials[0].strip()
        password = credentials[1].strip()
        
        wait_msg = bot.reply_to(message, "⏳ প্রসেসিং হচ্ছে... দয়া করে অপেক্ষা করুন।")
        
        if platform == 'fb':
            result = fb_login_logic(email, password)
        elif platform == 'ig':
            result = ig_login_logic(email, password)
            
        bot.edit_message_text(result, message.chat.id, wait_msg.message_id, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ একটি সমস্যা হয়েছে: {str(e)}")

# Render-এ বট চালু রাখার জন্য
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
