from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
import asyncio
import re
from pyrogram.errors import FloodWait, MessageNotModified

# Initialize Bot
bot = Client(
    "Countdown-Arabic",
    api_id=int(os.environ.get("API_ID", 0)),
    api_hash=os.environ.get("API_HASH", ""),
    bot_token=os.environ.get("BOT_TOKEN", "")
)

footer_message = os.environ.get("FOOTER_MESSAGE", "بواسطة بوت العداد")
stoptimer = False

# Arabic Time Parser Function
def parse_arabic_time(time_str):
    time_str = time_str.strip().lower()
    
    # Mapping common Arabic time terms to seconds
    time_map = {
        r'ثانية?': 1,
        r'ثواني': 1,
        r'دقيقة?': 60,
        r'دقائق': 60,
        r'دقايق': 60,
        r'ساعة?': 3600,
        r'ساعات': 3600,
        r'يوم': 86400,
        r'أيام': 86400,
        r'ايام': 86400,
    }
    
    # Special cases
    special_cases = {
        r'نص ساعة': 1800,
        r'نصف ساعة': 1800,
        r'ربع ساعة': 900,
        r'ثلث ساعة': 1200,
        r'ساعتين': 7200,
        r'دقيقتين': 120,
        r'يومين': 172800,
    }
    
    for pattern, seconds in special_cases.items():
        if re.search(pattern, time_str):
            return seconds
            
    # General pattern: (number) (unit)
    match = re.search(r'(\d+)\s*(.*)', time_str)
    if match:
        number = int(match.group(1))
        unit_part = match.group(2).strip()
        for pattern, seconds in time_map.items():
            if re.search(pattern, unit_part):
                return number * seconds
                
    # If only unit is mentioned (e.g., "ساعة")
    for pattern, seconds in time_map.items():
        if re.fullmatch(pattern, time_str):
            return seconds
            
    return None

@bot.on_message(filters.command(['start', 'help', 'مساعدة']))
async def start(client, message):
    help_text = (
        "👋 **أهلاً بك في بوت العداد العربي!**\n\n"
        "يمكنك استخدام الأمر التالي لضبط عداد:\n"
        "<code>عداد (النص) بعد (المدة)</code>\n\n"
        "**أمثلة:**\n"
        "• <code>عداد مكالمة بعد ساعة</code>\n"
        "• <code>عداد صلاة بعد نص ساعة</code>\n"
        "• <code>عداد تذكير بعد 10 دقايق</code>\n\n"
        "لإيقاف العداد: /stop أو /ايقاف"
    )
    await message.reply(help_text)

@bot.on_message(filters.regex(r'^عداد\s+\((.+)\)\s+بعد\s+(.+)$') | filters.regex(r'^عداد\s+(.+)\s+بعد\s+(.+)$'))
async def set_timer_arabic(client, message):
    global stoptimer
    try:
        # Extracting event and time from regex groups
        match = re.search(r'^عداد\s+\(?(.+?)\)?\s+بعد\s+(.+)$', message.text)
        if not match:
            return await message.reply("❌ صيغة غير صحيحة. استخدم: عداد (النص) بعد (المدة)")

        user_input_event = match.group(1).strip()
        time_str = match.group(2).strip()
        
        user_input_time = parse_arabic_time(time_str)
        
        if user_input_time is None:
            return await message.reply(f"❌ لم أفهم مدة الوقت: {time_str}")

        if message.chat.id > 0:
            # Private chat allowed in this version for convenience
            pass
        else:
            # Check admin in groups
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            if not member.privileges:
                return await message.reply('👮🏻‍♂️ عذراً، هذا الأمر للمشرفين فقط.')

        timer_msg = await message.reply(f"⏳ تم ضبط العداد لـ: **{user_input_event}**\nالمدة: {time_str}")
        try:
            await timer_msg.pin()
        except:
            pass # Might fail if not admin or in private

        if stoptimer: stoptimer = False
        
        current_time = user_input_time
        while current_time > 0 and not stoptimer:
            # Formatting time display
            d = current_time // 86400
            h = (current_time % 86400) // 3600
            m = (current_time % 3600) // 60
            s = current_time % 60
            
            display = ""
            if d > 0: display += f"{d} يوم "
            if h > 0: display += f"{h} ساعة "
            if m > 0: display += f"{m} دقيقة "
            if s > 0 or not display: display += f"{s} ثانية"
            
            text = f"🔔 **{user_input_event}**\n\n⏳ المتبقي: `{display.strip()}`\n\n_{footer_message}_"
            
            try:
                await timer_msg.edit(text)
            except MessageNotModified:
                pass
            except Exception:
                break
                
            # Dynamic sleep to avoid flood limits
            sleep_time = 1
            if current_time > 3600: sleep_time = 10
            elif current_time > 60: sleep_time = 5
            
            await asyncio.sleep(sleep_time)
            current_time -= sleep_time

        if not stoptimer:
            await timer_msg.edit(f"🚨 **انتهى الوقت!**\n\nالحدث: {user_input_event}")
            await message.reply(f"🔊 تذكير: انتهى وقت **{user_input_event}**!")
        else:
            await timer_msg.edit("🛑 تم إيقاف العداد.")
            stoptimer = False

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        await message.reply(f"حدث خطأ: {str(e)}")

@bot.on_message(filters.command(['stop', 'ايقاف', 'إيقاف']))
async def stop_timer(client, message):
    global stoptimer
    stoptimer = True
    await message.reply('🛑 تم إرسال أمر إيقاف العداد.')

if __name__ == "__main__":
    print("Arabic Countdown Bot is starting...")
    bot.run()
