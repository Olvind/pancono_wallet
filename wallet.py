import json
import os

DB_FILE = "users.json"
RESERVED_FILE = "reserved_wallets.json"


def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)


def load_reserved_wallets():
    if os.path.exists(RESERVED_FILE):
        with open(RESERVED_FILE, "r") as f:
            return json.load(f)["reserved_wallets"]
    return []


def import_private_key(private_key: str):
    wallets = load_reserved_wallets()
    for w in wallets:
        if w["private_key"] == private_key:
            return {
                "status": "success",
                "address": w["public_address"],
                "balance": w["balance"]
            }
    return {"status": "error", "message": "Invalid private key"}
