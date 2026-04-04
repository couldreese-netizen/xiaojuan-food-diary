from supabase import create_client, Client
import streamlit as st
import os
import io
import re
from PIL import Image, ImageOps
import datetime

# ========== 从环境变量或 secrets 读取配置 ==========
try:
    # 优先使用 st.secrets（云端）
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    # 本地开发用 .env
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== 用户操作 ==========
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

# ========== 推荐操作 ==========
def get_all_recommendations():
    response = supabase.table("recommendations").select("*").execute()
    return response.data

def get_recommendations_by_user(user_id):
    response = supabase.table("recommendations").select("*").eq("user_id", user_id).execute()
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

# ========== 好友操作 ==========
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

# ========== Storage 存储操作 ==========
def upload_avatar(uploaded_file, user_id):
    """上传头像到 Supabase Storage，返回公开 URL"""
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    
    # 裁剪为正方形
    width, height = img.size
    if width != height:
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))
    
    # 调整大小
    img = img.resize((200, 200), Image.Resampling.LANCZOS)
    
    # 转换为字节
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes = img_bytes.getvalue()
    
    # 生成文件名（纯英文数字）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"user_{user_id}_{timestamp}.jpg"
    
    # 上传到 Supabase Storage
    supabase.storage.from_("avatars").upload(file_name, img_bytes, {"content-type": "image/jpeg"})
    
    # 返回公开 URL
    return supabase.storage.from_("avatars").get_public_url(file_name)

def upload_food_image(uploaded_file, user_id, restaurant_name):
    """上传美食图片到 Supabase Storage，返回公开 URL"""
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    
    # 压缩图片（限制最大边长 800px）
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    
    # 转换为字节
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=80)
    img_bytes = img_bytes.getvalue()
    
    # 生成文件名（移除中文字符，只保留英文数字下划线横线）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # 只保留英文、数字、下划线、横线，移除中文和特殊字符
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', restaurant_name)
    if not clean_name:
        clean_name = "food"
    file_name = f"{user_id}_{timestamp}_{clean_name}.jpg"
    
    # 上传到 Supabase Storage
    supabase.storage.from_("uploads").upload(file_name, img_bytes, {"content-type": "image/jpeg"})
    
    # 返回公开 URL
    return supabase.storage.from_("uploads").get_public_url(file_name)

def delete_storage_file(bucket_name, file_path):
    """删除存储桶中的文件（可选功能）"""
    try:
        supabase.storage.from_(bucket_name).remove([file_path])
        return True
    except:
        return False

# ========== 评论操作 ==========
def get_comments(recommendation_id):
    """获取某条推荐的所有评论"""
    response = supabase.table("comments").select("*").eq("recommendation_id", recommendation_id).order("created_at", desc=False).execute()
    return response.data

def add_comment(recommendation_id, user_id, content):
    """添加评论"""
    if not content or not content.strip():
        return None
    data = {
        "recommendation_id": recommendation_id,
        "user_id": user_id,
        "content": content.strip()
    }
    response = supabase.table("comments").insert(data).execute()
    return response.data[0]

def delete_comment(comment_id, user_id):
    """删除评论（只能删自己的）"""
    response = supabase.table("comments").delete().eq("id", comment_id).eq("user_id", user_id).execute()
    return response.data
