import json
import time
from config import DB_FILE

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_user(user_id):
    db = load_db()
    if str(user_id) not in db["users"]:
        db["users"][str(user_id)] = {
            "wallet_id": None,
            "private_key": None,
            "balance": 0,
            "ton_wallet": None,
            "referrals": [],
            "airdrop_active": False,
            "airdrop_start": None
        }
        save_db(db)
    return db["users"][str(user_id)]

def update_user(user_id, data):
    db = load_db()
    db["users"][str(user_id)].update(data)
    save_db(db)
