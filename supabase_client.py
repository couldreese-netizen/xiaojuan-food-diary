from supabase import create_client, Client
import streamlit as st
import os

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_all_users():
    response = supabase.table("users").select("*").execute()
    return response.data

def get_user_by_id(user_id):
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    return response.data[0] if response.data else None

def get_user_by_username(username):
    response = supabase.table("users").select("*").eq("username", username).execute()
    return response.data[0] if response.data else None

def get_user_by_invite_code(invite_code):
    response = supabase.table("users").select("*").eq("invite_code", invite_code).execute()
    return response.data[0] if response.data else None

def add_user(user_data):
    response = supabase.table("users").insert(user_data).execute()
    return response.data[0]

def update_user(user_id, updates):
    response = supabase.table("users").update(updates).eq("id", user_id).execute()
    return response.data[0]

def get_all_recommendations():
    response = supabase.table("recommendations").select("*").execute()
    return response.data

def add_recommendation(rec_data):
    response = supabase.table("recommendations").insert(rec_data).execute()
    return response.data[0]

def update_recommendation(rec_id, updates):
    response = supabase.table("recommendations").update(updates).eq("id", rec_id).execute()
    return response.data[0]

def delete_recommendation(rec_id):
    response = supabase.table("recommendations").delete().eq("id", rec_id).execute()
    return response.data

def toggle_like(rec_id, user_id):
    rec = supabase.table("recommendations").select("likes").eq("id", rec_id).execute()
    if not rec.data:
        return
    likes = rec.data[0].get("likes", [])
    if user_id in likes:
        likes.remove(user_id)
    else:
        likes.append(user_id)
    supabase.table("recommendations").update({"likes": likes}).eq("id", rec_id).execute()

def add_friend(user_id, friend_id):
    user = get_user_by_id(user_id)
    friend = get_user_by_id(friend_id)
    if not user or not friend:
        return False, "用户不存在"
    friends_user = user.get("friends", [])
    if friend_id in friends_user:
        return False, "已经是好友"
    friends_user.append(friend_id)
    friends_friend = friend.get("friends", [])
    if user_id not in friends_friend:
        friends_friend.append(user_id)
    update_user(user_id, {"friends": friends_user})
    update_user(friend_id, {"friends": friends_friend})
    return True, "添加成功"

def get_friends(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return []
    friends = []
    for friend_id in user.get("friends", []):
        friend = get_user_by_id(friend_id)
        if friend:
            friends.append(friend)
    return friends
