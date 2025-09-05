import logging
import time
from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN
from db import get_user, update_user
from wallet import import_wallet, export_wallet
from airdrop import process_airdrop
from referral import add_referral
from config import ADMIN_ID
from db import load_db

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# /start command with referral support
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    args = message.get_args()
    user = get_user(message.from_user.id)

    if args.startswith("ref"):
        referrer_id = args.replace("ref", "")
        add_referral(referrer_id, str(message.from_user.id))

    text = "🌙 *Welcome to Pancono Wallet!*\n\nUse /wallet to view your balance."
    await message.answer(text, parse_mode="Markdown")

# Wallet dashboard
@dp.message_handler(commands=["wallet"])
async def wallet(message: types.Message):
    u = get_user(message.from_user.id)

    status = "🟢 Active" if u["airdrop_active"] else "🔴 Stopped"
    start_btn = ""
    if not u["airdrop_active"]:
        start_btn = "\n\n👉 /start_airdrop to begin a new 24h cycle."

    text = f"""
💼 *Pancono Wallet*

🆔 Wallet ID: `{u['wallet_id']}`
💰 Balance: {u['balance']:.6f} PANCA
🔗 TON Wallet: {u['ton_wallet'] or 'Not linked'}
👥 Referrals: {len(u['referrals'])}
🎁 Airdrop: {status}{start_btn}
    """
    await message.answer(text, parse_mode="Markdown")

# Start airdrop
@dp.message_handler(commands=["start_airdrop"])
async def start_airdrop(message: types.Message):
    u = get_user(message.from_user.id)
    if u["airdrop_active"]:
        await message.answer("⏳ Airdrop already running.")
        return

    update_user(message.from_user.id, {
        "airdrop_active": True,
        "airdrop_start": time.time()
    })
    await message.answer("✅ Airdrop started! You will earn 0.0005 PANCA/min for 24h.")

# Claim airdrop manually (updates balance)
@dp.message_handler(commands=["claim"])
async def claim(message: types.Message):
    earned = process_airdrop(message.from_user.id)
    if earned > 0:
        await message.answer(f"💎 You claimed {earned:.6f} PANCA!")
    else:
        await message.answer("⚠️ No rewards to claim. Maybe airdrop stopped?")

# Import wallet
@dp.message_handler(commands=["import"])
async def import_wallet_cmd(message: types.Message):
    await message.answer("🔑 Send your private key to import wallet:")

@dp.message_handler(lambda msg: msg.text.startswith("privkey"))
async def import_key(message: types.Message):
    addr, bal = import_wallet(message.from_user.id, message.text.strip())
    if addr:
        await message.answer(f"✅ Wallet imported!\n🆔 {addr}\n💰 Balance: {bal} PANCA")
    else:
        await message.answer("❌ Invalid private key.")

# Export private key
@dp.message_handler(commands=["export"])
async def export(message: types.Message):
    key = export_wallet(message.from_user.id)
    if key:
        await message.answer(f"🔑 Your private key:\n`{key}`", parse_mode="Markdown")
    else:
        await message.answer("⚠️ No wallet found to export.")
        

# Admin stats
@dp.message_handler(commands=["stats"])
async def stats(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        await message.answer("🚫 You are not authorized to view stats.")
        return

    db = load_db()
    users = db["users"]
    total_users = len(users)

    # Build referral summary
    leaderboard = []
    for uid, data in users.items():
        leaderboard.append((uid, len(data["referrals"])))
    leaderboard.sort(key=lambda x: x[1], reverse=True)

    text = f"📊 *Pancono Stats*\n\n👥 Total Users: {total_users}\n\n🏆 *Top Referrers:*\n"
    for uid, count in leaderboard[:10]:  # show top 10
        text += f"• User {uid}: {count} referrals\n"

    await message.answer(text, parse_mode="Markdown")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
