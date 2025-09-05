from db import get_user, update_user

def add_referral(referrer_id, new_user_id):
    user = get_user(referrer_id)
    if new_user_id not in user["referrals"]:
        user["referrals"].append(new_user_id)
        update_user(referrer_id, {"balance": user["balance"] + 0.01})
        update_user(referrer_id, {"referrals": user["referrals"]})
