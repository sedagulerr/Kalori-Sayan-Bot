import os
import re
import logging

from dotenv import load_dotenv

# .env dosyasi, claude_service gibi API key'e ihtiyac duyan modulleri
# import etmeden ONCE yuklenmeli, yoksa KeyError alinir.
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from calculations import compute_totals, divide_per_portion
from claude_service import parse_meal, get_meal_assessment
from db import init_db, log_meal, get_today_totals

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

MEAL_TYPES = {
    "kahvalti": "🍳 Kahvaltı",
    "ogle": "🍲 Öğle Yemeği",
    "aksam": "🍽️ Akşam Yemeği",
    "atistirmalik": "🥨 Atıştırmalık",
}

TODAY_BUTTON_TEXT = "📅 Bugünkü Toplam"
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup([[TODAY_BUTTON_TEXT]], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! Yediğin yemeğin malzemelerini yaz, kaloriyi hesaplayayım.\n\n"
        "Örnek: '200 gram tavuk göğsü, 1 su bardağı pirinç, 4 kişiye böl'\n\n"
        "Porsiyon sayısını yazmazsan sonradan sorarım. Sonuç geldikten sonra "
        "'değerlendir' yazarsan hangi öğün olduğunu sorup (kahvaltı/öğle/akşam/"
        "atıştırmalık) ona göre kısaca değerlendiririm.\n\n"
        "Aşağıdaki 'Bugünkü Toplam' butonuna basarak bugün kaydettiğin "
        "öğünlerin toplamını görebilirsin.",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


async def send_today_totals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    totals, count = get_today_totals(update.effective_user.id)
    if count == 0:
        await update.message.reply_text("Bugün henüz bir şey kaydetmedin.")
        return
    await update.message.reply_text(
        f"📅 Bugünkü toplam ({count} öğün):\n"
        f"🔥 {totals['calories']} kcal\n"
        f"🥩 {totals['protein_g']} g protein\n"
        f"🍞 {totals['carbs_g']} g karbonhidrat\n"
        f"🧈 {totals['fat_g']} g yağ"
    )


async def bugun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_today_totals(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    # 1) Sabit menu butonuna basildiysa
    if text == TODAY_BUTTON_TEXT:
        await send_today_totals(update, context)
        return

    # 2) Onceki mesajda porsiyon sayisi bekleniyorsa -> mesajin icindeki ilk sayiyi ara
    #    ("4", "4 kişi", "4'e böl" gibi farkli yazimlari da yakalar)
    if user_data.get("awaiting_portion"):
        match = re.search(r"\d+", text)
        if match:
            portion_count = int(match.group())
            if portion_count <= 0:
                await update.message.reply_text("Porsiyon sayısı 0'dan büyük bir sayı olmalı, tekrar yazar mısın?")
                return
            user_data["awaiting_portion"] = False
            await compute_and_reply(update, context, user_data["pending_ingredients"], portion_count)
            return

    # 3) "degerlendir" komutu -> once ogun turunu sor (buton olarak)
    if text.lower() in ("değerlendir", "degerlendir"):
        if "last_ingredients" not in user_data:
            await update.message.reply_text("Önce bir yemek gönder, sonra değerlendirmesini isteyebilirsin.")
            return
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(MEAL_TYPES["kahvalti"], callback_data="meal_type:kahvalti"),
             InlineKeyboardButton(MEAL_TYPES["ogle"], callback_data="meal_type:ogle")],
            [InlineKeyboardButton(MEAL_TYPES["aksam"], callback_data="meal_type:aksam"),
             InlineKeyboardButton(MEAL_TYPES["atistirmalik"], callback_data="meal_type:atistirmalik")],
        ])
        await update.message.reply_text("Hangi öğün için değerlendireyim?", reply_markup=keyboard)
        return

    # 4) Yeni yemek tarifi
    await update.message.reply_text("Hesaplıyorum...")
    try:
        parsed = parse_meal(text)
    except Exception:
        logger.exception("Claude parse hatasi")
        await update.message.reply_text("Malzemeleri analiz ederken bir hata oldu, tekrar dener misin?")
        return

    ingredients = parsed["ingredients"]
    portion_count = parsed.get("portion_count")
    if portion_count is not None and portion_count <= 0:
        portion_count = None  # gecersiz deger, porsiyon sonradan sorulacak

    if not ingredients:
        await update.message.reply_text(
            "Bunu bir yemek/malzeme tarifi olarak anlayamadım. "
            "Örneğin: '200 gram tavuk göğsü, 1 su bardağı pirinç, 4 kişiye böl' "
            "gibi yazabilir misin?"
        )
        return

    if portion_count:
        await compute_and_reply(update, context, ingredients, portion_count)
    else:
        totals = compute_totals(ingredients)
        user_data["awaiting_portion"] = True
        user_data["pending_ingredients"] = ingredients
        user_data["last_ingredients"] = ingredients
        user_data["last_totals"] = totals
        user_data["last_portion_totals"] = None
        await update.message.reply_text(
            format_totals(ingredients, totals) + "\n\nKaç kişiye bölmemi istersin? (sadece sayı yaz)"
        )


async def compute_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, ingredients: list, portion_count: int):
    totals = compute_totals(ingredients)
    per_portion = divide_per_portion(totals, portion_count)

    context.user_data["last_ingredients"] = ingredients
    context.user_data["last_totals"] = totals
    context.user_data["last_portion_totals"] = per_portion

    try:
        log_meal(update.effective_user.id, per_portion, portion_count)
    except Exception:
        logger.exception("Ogun veritabanina kaydedilirken hata olustu")
        # Kayit basarisiz olsa da kullaniciya sonucu gostermeye devam ediyoruz.

    msg = format_totals(ingredients, totals)
    msg += (
        f"\n\n👥 {portion_count} kişiye bölündü:\n"
        f"🔥 {per_portion['calories']} kcal/kişi\n"
        f"🥩 {per_portion['protein_g']} g protein\n"
        f"🍞 {per_portion['carbs_g']} g karbonhidrat\n"
        f"🧈 {per_portion['fat_g']} g yağ"
    )
    msg += "\n\n'değerlendir' yazarsan öğünü kısaca değerlendiririm."
    await update.message.reply_text(msg)


def format_totals(ingredients: list, totals: dict) -> str:
    lines = [
        f"• {i['name']} ({i['amount_description']}): {i['calories']} kcal"
        for i in ingredients
    ]
    return (
        "📋 Malzemeler:\n" + "\n".join(lines) +
        f"\n\nToplam: {totals['calories']} kcal | "
        f"{totals['protein_g']}g protein / {totals['carbs_g']}g karb / {totals['fat_g']}g yağ"
    )


async def handle_meal_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    meal_type_key = query.data.split(":", 1)[1]
    meal_type_label = MEAL_TYPES.get(meal_type_key, "")
    user_data = context.user_data

    if "last_ingredients" not in user_data:
        await query.edit_message_text("Önce bir yemek gönder, sonra değerlendirmesini isteyebilirsin.")
        return

    await query.edit_message_text(f"{meal_type_label} olarak değerlendiriyorum...")
    try:
        assessment = get_meal_assessment(
            user_data["last_ingredients"],
            user_data["last_totals"],
            user_data.get("last_portion_totals"),
            meal_type_label,
        )
    except Exception:
        logger.exception("Degerlendirme sirasinda hata")
        await context.bot.send_message(query.message.chat_id, "Değerlendirme alınırken bir hata oldu, tekrar dener misin?")
        return

    await context.bot.send_message(query.message.chat_id, assessment)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start", "Botu tanıt ve nasıl kullanılacağını göster"),
        BotCommand("bugun", "Bugün kaydettiğin öğünlerin toplamını gör"),
    ])


def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bugun", bugun))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_meal_type_selection, pattern=r"^meal_type:"))
    logger.info("Bot başlıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
