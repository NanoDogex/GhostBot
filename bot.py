import os
import logging
import sqlite3
import asyncio
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import BadRequest
from dotenv import load_dotenv
load_dotenv()
# ================== ENV ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "dummy")
SERVICE_ENDPOINT = os.getenv(
    "SERVICE_ENDPOINT",
    "http://127.0.0.1:8000/v1/chat/completions",
)
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@GhostGptDev")
OWNER_ID = int(os.getenv("OWNER_ID", "8087130352"))
DB_PATH = os.getenv("DB_PATH", "bot.db")

# ================== CRYPTO WALLETS (SORTED) ==================
CRYPTO_WALLETS = {
    "trc": os.getenv("CRYPTO_WALLET_TRC"),
    "sol": os.getenv("CRYPTO_WALLET_SOL"),
    "btc": os.getenv("CRYPTO_WALLET_BTC"),
    "eth": os.getenv("CRYPTO_WALLET_ETH"),
    "bsc": os.getenv("CRYPTO_WALLET_BSC"),
}

# ================== LOGGING ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ghostgpt")

# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def add_user(user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
        (
            user.id,
            user.username,
            datetime.utcnow().isoformat(),
        ),
    )

    conn.commit()
    conn.close()


# ================== UI ==================

def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💎 Plans", callback_data="plans"),
                InlineKeyboardButton("🚀 Benefits", callback_data="benefits"),
            ],
            [
                InlineKeyboardButton("💰 Pay Crypto", callback_data="pay"),
                InlineKeyboardButton("📞 Support", callback_data="support"),
            ],
        ]
    )


def plans_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🥉 Basic — $9.99", callback_data="buy_basic"),
                InlineKeyboardButton("🥈 Pro — $19.99", callback_data="buy_pro"),
            ],
            [
                InlineKeyboardButton("👑 Elite — $39.99", callback_data="buy_elite"),
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="home"),
            ],
        ]
    )


def networks_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🟢 TRC20", callback_data="net_trc")],
            [InlineKeyboardButton("🟣 Solana", callback_data="net_sol")],
            [InlineKeyboardButton("🟠 Bitcoin", callback_data="net_btc")],
            [InlineKeyboardButton("🔵 Ethereum", callback_data="net_eth")],
            [InlineKeyboardButton("🟡 BSC", callback_data="net_bsc")],
            [InlineKeyboardButton("⬅️ Back", callback_data="home")],
        ]
    )


# ================== CAPTIONS ==================

HOME_CAPTION = f"""

 Unfiltered AI Intelligence  



Choose an option below 👇

"""

BENEFITS_TEXT = """

 No censorship  
 Blazing fast responses  
 Premium AI models  
 Privacy focused  
 Crypto friendly  
 Always online  



"""

PLANS_TEXT = """




 Instant activation after payment.
"""

# ================== SAFE EDIT ==================

async def safe_edit_caption(query, caption, keyboard):
    try:
        await query.edit_message_caption(
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


# ================== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user)

    if not os.path.exists("banner.jpg"):
        await update.message.reply_text(
            "⚠️ banner.jpg missing in bot folder."
        )
        return

    with open("banner.jpg", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=HOME_CAPTION,
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard(),
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # ===== HOME =====
    if data == "home":
        await safe_edit_caption(query, HOME_CAPTION, main_keyboard())

    # ===== BENEFITS =====
    elif data == "benefits":
        await safe_edit_caption(query, BENEFITS_TEXT, main_keyboard())

    # ===== PLANS =====
    elif data == "plans":
        await safe_edit_caption(query, PLANS_TEXT, plans_keyboard())

    # ===== PAY =====
    elif data == "pay":
        await safe_edit_caption(
            query,
            "💰 <b>Select payment network:</b>",
            networks_keyboard(),
        )

    # ===== NETWORKS =====
    elif data.startswith("net_"):
        net = data.split("_")[1]
        wallet = CRYPTO_WALLETS.get(net, "Not configured")

        text = f"""

<code>{wallet}</code>



"""

        await safe_edit_caption(query, text, networks_keyboard())

    # ===== SUPPORT =====
    elif data == "support":
        await safe_edit_caption(
            query,
            f"📞 Support: {OWNER_USERNAME}",
            main_keyboard(),
        )


# ================== MAIN ==================

def main():
    init_db()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("👻 GhostGPT Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
