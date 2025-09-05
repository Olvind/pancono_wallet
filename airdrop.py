import time
from db import get_user, update_user

AIRDROP_RATE = 0.0005  # PANCA per minute
AIRDROP_DURATION = 24 * 60  # minutes

def process_airdrop(user_id):
    user = get_user(user_id)

    if not user["airdrop_active"]:
        return 0

    start = user["airdrop_start"]
    elapsed = int((time.time() - start) / 60)  # minutes passed

    if elapsed >= AIRDROP_DURATION:
        update_user(user_id, {"airdrop_active": False})
        return 0

    earned = elapsed * AIRDROP_RATE
    update_user(user_id, {"balance": user["balance"] + earned})
    update_user(user_id, {"airdrop_start": time.time()})  # reset counter
    return earned
