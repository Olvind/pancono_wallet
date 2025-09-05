from db import load_db, save_db, update_user, get_user

def import_wallet(user_id, private_key):
    db = load_db()
    for addr, w in db["reserved_wallets"].items():
        if w["private_key"] == private_key:
            update_user(user_id, {
                "wallet_id": addr,
                "private_key": private_key,
                "balance": w["balance"]
            })
            return addr, w["balance"]
    return None, None

def export_wallet(user_id):
    u = get_user(user_id)
    return u.get("private_key")
