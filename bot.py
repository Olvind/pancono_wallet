import logging
import time
import datetime
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN, ADMIN_ID
from db import get_user, update_user, load_db
from wallet import import_wallet, export_wallet, import_private_key
from referral import add_referral

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

AIRDROP_AMOUNT = 0.0005
AIRDROP_DURATION_HOURS = 24
AIRDROP_INTERVAL_MINUTES = 1


# /start command with referral support
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    args = message.get_args()
    user = get_user(message.from_user.id)

    if args.startswith("ref"):
        referrer_id = args.replace("ref", "")
        add_referral(referrer_id, str(message.from_user.id))

    text = (
        "🌙 *Welcome to Pancono Wallet!*\n\n"
        "💰 Use /wallet to view your balance\n"
        "🎁 Airdrop: 0.0005 PANCA/min for 24h\n"
        f"👥 Invite friends: https://t.me/{(await bot.get_me()).username}?start=ref{message.from_user.id}\n\n"
        "🔑 Import reserved wallets with /import"
    )
    await message.answer(text, parse_mode="Markdown")


# Wallet dashboard
@dp.message_handler(commands=["wallet"])
async def wallet(message: types.Message):
    u = get_user(message.from_user.id)

    # Airdrop status
    status = "🔴 Stopped"
    if u.get("airdrop_active"):
        elapsed = time.time() - u["airdrop_start"]
        if elapsed < AIRDROP_DURATION_HOURS * 3600:
            status = "🟢 Active"
        else:
            status = "⏳ Expired (use /start_airdrop to restart)"
            update_user(message.from_user.id, {"airdrop_active": False})

    text = f"""
💼 *Pancono Wallet*

🆔 Wallet ID: `{u['wallet_id']}`
💰 Balance: {u['balance']:.6f} PANCA
🔗 TON Wallet: {u.get('ton_wallet') or 'Not linked'}
👥 Referrals: {len(u['referrals'])}
🎁 Airdrop: {status}
"""
    await message.answer(text, parse_mode="Markdown")


# Start airdrop
@dp.message_handler(commands=["start_airdrop"])
async def start_airdrop(message: types.Message):
    u = get_user(message.from_user.id)
    if u.get("airdrop_active"):
        elapsed = time.time() - u["airdrop_start"]
        if elapsed < AIRDROP_DURATION_HOURS * 3600:
            await message.answer("⏳ Airdrop already running.")
            return

    update_user(message.from_user.id, {
        "airdrop_active": True,
        "airdrop_start": time.time(),
        "last_claim": None
    })
    await message.answer("✅ Airdrop started! You will earn 0.0005 PANCA/min for 24h.")


# Background auto-airdrop processor
async def process_airdrops():
    while True:
        db = load_db()
        changed = False
        for uid, data in db["users"].items():
            if data.get("airdrop_active"):
                elapsed = time.time() - data["airdrop_start"]
                if elapsed < AIRDROP_DURATION_HOURS * 3600:
                    last_claim = data.get("last_claim") or 0
                    if time.time() - last_claim >= AIRDROP_INTERVAL_MINUTES * 60:
                        data["balance"] += AIRDROP_AMOUNT
                        data["last_claim"] = time.time()
                        changed = True
                else:
                    data["airdrop_active"] = False
                    changed = True
        if changed:
            update_user("bulk_save", db)  # extend db.update to allow saving whole db
        await asyncio.sleep(30)


# Manual claim (if you keep this option)
@dp.message_handler(commands=["claim"])
async def claim(message: types.Message):
    u = get_user(message.from_user.id)
    if not u.get("airdrop_active"):
        await message.answer("⚠️ No active airdrop. Start with /start_airdrop.")
        return

    last_claim = u.get("last_claim") or 0
    if time.time() - last_claim >= AIRDROP_INTERVAL_MINUTES * 60:
        u["balance"] += AIRDROP_AMOUNT
        u["last_claim"] = time.time()
        update_user(message.from_user.id, u)
        await message.answer(f"💎 You claimed {AIRDROP_AMOUNT:.6f} PANCA!")
    else:
        await message.answer("⚠️ Too early. Wait for next claim cycle.")


# Import reserved wallet
@dp.message_handler(commands=["import"])
async def import_key_cmd(message: types.Message):
    try:
        _, priv_key = message.text.split(" ", 1)
    except:
        await message.answer("❌ Usage: /import YOUR_PRIVATE_KEY")
        return

    result = import_private_key(priv_key.strip())
    if result["status"] == "success":
        await message.answer(
            f"✅ Wallet Imported!\n\n"
            f"🔑 Address: {result['address']}\n"
            f"💰 Balance: {result['balance']} PANCA"
        )
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

    leaderboard = []
    for uid, data in users.items():
        leaderboard.append((uid, len(data["referrals"])))
    leaderboard.sort(key=lambda x: x[1], reverse=True)

    text = f"📊 *Pancono Stats*\n\n👥 Total Users: {total_users}\n\n🏆 *Top Referrers:*\n"
    for uid, count in leaderboard[:10]:
        text += f"• User {uid}: {count} referrals\n"

    await message.answer(text, parse_mode="Markdown")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(process_airdrops())
    executor.start_polling(dp, skip_updates=True)
