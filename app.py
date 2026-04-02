import streamlit as st
import json
import os
from PIL import Image, ImageOps
import datetime
import random
import re
from zoneinfo import ZoneInfo
from supabase_client import (
    get_all_users, get_user_by_id, get_user_by_username,
    get_user_by_invite_code, add_user, update_user,
    get_all_recommendations, add_recommendation, toggle_like,
    get_friends as supabase_get_friends, add_friend as supabase_add_friend,
    delete_recommendation, update_recommendation
)

# ========== 小卷语录库（你最新自定义版）==========
XIAOJUAN_SAYINGS = [
    "🐯 哇塞！看起来好美味～小卷也想吃！",
    "🧀 小卷闻到香味啦，快分享给好朋友！",
    "🍜 今天也是被美食治愈的一天～",
    "✨ 小卷悄悄记下你的美食日记啦！",
    "🤓 tori说今天奢侈一把！",
    "👀 oo老师说: 很Q弹！",
    "🥺 尾椎骨说：我不争！",
    "🐯 嗷呜～这个推荐太棒了，小卷要偷偷收藏！",
    "🍊 桔桔说手里有个热乎的馍馍比什么都重要",
    "💛 和朋友一起吃饭最开心啦！",
    "🎉 你太会吃了！小卷为你鼓掌～",
    "🍱 下次带小卷一起去吃好不好？",
    "🌟 你的美食日记闪闪发光！",
    "🎲 命运的选择来啦～冲！",
    "🥳 第一条美食日记！小卷撒花～",
    "❤️ 收藏成功！小卷也记下来啦～"
]

def random_saying():
    return random.choice(XIAOJUAN_SAYINGS)

# ========== 辅助函数 ==========
def safe_open_image(filepath, default_size=(200,200)):
    try:
        if filepath and os.path.exists(filepath):
            img = Image.open(filepath)
            img = ImageOps.exif_transpose(img)
            return img
        return None
    except:
        return None

def save_avatar(uploaded_file, user_id):
    if not os.path.exists("avatars"):
        os.makedirs("avatars")
    
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    
    width, height = img.size
    if width != height:
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))
    
    img = img.resize((200, 200), Image.Resampling.LANCZOS)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_{user_id}_{timestamp}.jpg"
    filepath = os.path.join("avatars", filename)
    img.save(filepath, "JPEG", quality=85)
    return filepath

def save_image(uploaded_file, user_id, restaurant_name):
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = "".join(c for c in restaurant_name if c.isalnum() or c in " _-")
    filename = f"{user_id}_{timestamp}_{clean_name}.jpg"
    filepath = os.path.join("uploads", filename)
    img.save(filepath, "JPEG", quality=85)
    return filepath

def generate_invite_code(username):
    import random
    import string
    username_clean = re.sub(r'[^a-zA-Z]', '', username)
    prefix = username_clean[:6].upper() if username_clean else "USER"
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"

def check_username_exists(username):
    users = get_all_users()
    for u in users:
        if u["username"].lower() == username.lower():
            return True
    return False

def get_user_display_name(user):
    return user.get("nickname", user["username"])

def add_initial_user_if_needed():
    users = get_all_users()
    if len(users) == 0:
        new_user = {
            "username": "xiaojuan",
            "nickname": "🐯 小卷 🧀",
            "invite_code": "XIAOJUAN2024",
            "avatar": None,
            "friends": [],
            "bio": "🍜 美食探险家 | 小卷的觅食日记 | 一起吃遍全世界！",
            "remaining_invites": -1
        }
        add_user(new_user)
        return new_user
    return None

def search_users(keyword):
    keyword_lower = keyword.lower()
    results = []
    users = get_all_users()
    for u in users:
        if u["id"] == st.session_state.user_id:
            continue
        if (keyword_lower in u["username"].lower() or 
            keyword_lower in u.get("nickname", "").lower()):
            results.append(u)
    return results

def get_friends(user_id):
    return supabase_get_friends(user_id)

def add_friend(user_id, friend_id):
    return supabase_add_friend(user_id, friend_id)

def remove_friend(user_id, friend_id):
    user = get_user_by_id(user_id)
    friend = get_user_by_id(friend_id)
    if not user or not friend:
        return False
    friends_user = user.get("friends", [])
    if friend_id in friends_user:
        friends_user.remove(friend_id)
        update_user(user_id, {"friends": friends_user})
    friends_friend = friend.get("friends", [])
    if user_id in friends_friend:
        friends_friend.remove(user_id)
        update_user(friend_id, {"friends": friends_friend})
    return True

def get_lottery_pool(city, food_type):
    recommendations = get_all_recommendations()
    filtered = []
    for rec in recommendations:
        if city != "全部" and rec.get("city", "") != city:
            continue
        rec_type = rec.get("food_type", "外卖吃啥")
        if food_type != "全部" and rec_type != food_type:
            continue
        filtered.append(rec)
    
    sorted_by_likes = sorted(filtered, key=lambda x: len(x.get("likes", [])), reverse=True)
    top_likes = sorted_by_likes[:5]
    sorted_by_date = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)
    top_recent = sorted_by_date[:5]
    
    pool = {}
    for rec in top_likes + top_recent:
        pool[rec["id"]] = rec
    return list(pool.values())

# ========== 页面设置 ==========
st.set_page_config(
    page_title="🐯 HeyFoodie · 好友美食圈", 
    page_icon="🍜", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
img {border-radius: 50% !important;}
.stButton>button {border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# ========== 自动登录 ==========
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.markdown("""
    <script>
    const userId = localStorage.getItem('heyfoodie_user_id');
    const username = localStorage.getItem('heyfoodie_username');
    if (userId && username) {
        const url = new URL(window.location.href);
        if (!url.searchParams.has('user_id')) {
            url.searchParams.set('user_id', userId);
            url.searchParams.set('username', username);
            window.location.href = url.toString();
        }
    }
    </script>
    """, unsafe_allow_html=True)

# ========== 登录状态 ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None

if not st.session_state.logged_in:
    user_id_param = st.query_params.get("user_id")
    username_param = st.query_params.get("username")
    
    if user_id_param and username_param:
        try:
            user_id = int(user_id_param)
            user = get_user_by_id(user_id)
            if user and user["username"] == username_param:
                st.session_state.logged_in = True
                st.session_state.user_id = user["id"]
                st.session_state.user_name = user["username"]
                st.rerun()
        except:
            pass

add_initial_user_if_needed()

# ========== 登录页面 ==========
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .big-title {
        text-align: center;
        font-size: 3em;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="big-title">🐯 🧀 🍜</p>', unsafe_allow_html=True)
        st.title("🐯 HeyFoodie")
        st.markdown("### 好友专属美食圈 · 小卷的觅食日记")
        st.caption("🐯 和小卷一起，记录每一顿美好的饭！")
    
    tab1, tab2 = st.tabs(["🔐 登录", "🎉 注册新账号"])
    
    with tab1:
        st.markdown("### 登录")
        login_username = st.text_input("用户名", placeholder="你的用户名", key="login_username")
        login_invite_code = st.text_input("邀请码", placeholder="你的邀请码", key="login_code")
        
        if st.button("🐯 登录", key="login_btn", use_container_width=True):
            if not login_username or not login_invite_code:
                st.error("请填写用户名和邀请码")
            else:
                user = get_user_by_username(login_username)
                if user and user["invite_code"] == login_invite_code:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["username"]
                    st.query_params["user_id"] = user["id"]
                    st.query_params["username"] = user["username"]
                    st.markdown(f"""
                    <script>
                    localStorage.setItem('heyfoodie_user_id', '{user["id"]}');
                    localStorage.setItem('heyfoodie_username', '{user["username"]}');
                    </script>
                    """, unsafe_allow_html=True)
                    st.success(f"🎉 欢迎回来，{get_user_display_name(user)}！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ 用户名或邀请码错误")
    
    with tab2:
        st.markdown("### 🎉 注册新账号")
        st.caption("需要朋友的邀请码才能加入哦~")
        friend_code = st.text_input("朋友的邀请码", placeholder="输入朋友的邀请码", key="friend_code")
        new_username = st.text_input("用户名（登录用）", placeholder="英文或数字，例如：xiaoming", key="reg_username")
        new_nickname = st.text_input("昵称（显示用）", placeholder="例如：爱吃的小明", key="reg_nickname")
        new_bio = st.text_area("一句话介绍自己", placeholder="介绍一下自己吧~", key="reg_bio", height=80)
        
        st.markdown("**📸 上传头像（1:1正方形，会自动裁剪）**")
        new_avatar = st.file_uploader("点击上传头像", type=["jpg", "jpeg", "png"], key="reg_avatar")
        if new_avatar:
            preview_img = Image.open(new_avatar)
            preview_img = ImageOps.exif_transpose(preview_img)
            st.image(preview_img, width=100)
            st.caption("上传后会自动裁剪为正方形")
        
        if st.button("🎉 注册", key="register_btn", use_container_width=True):
            if not friend_code:
                st.error("请输入朋友的邀请码")
            elif not new_username:
                st.error("请输入用户名")
            elif not new_nickname:
                st.error("请输入昵称")
            else:
                inviter = get_user_by_invite_code(friend_code)
                if not inviter:
                    st.error("邀请码无效，问朋友要一个正确的吧~")
                elif check_username_exists(new_username):
                    st.error("用户名已被使用，换一个吧~")
                else:
                    remaining = inviter.get("remaining_invites", 10)
                    if remaining == 0:
                        st.error("邀请人的邀请次数已用完，无法继续邀请新朋友")
                        st.stop()
                    if remaining > 0 and inviter["id"] != 1:
                        update_user(inviter["id"], {"remaining_invites": remaining - 1})
                    
                    all_users = get_all_users()
                    new_id = max([u["id"] for u in all_users], default=0) + 1
                    new_invite_code = generate_invite_code(new_username)
                    avatar_path = None
                    if new_avatar:
                        avatar_path = save_avatar(new_avatar, new_id)
                    
                    new_user = {
                        "id": new_id,
                        "username": new_username.lower(),
                        "nickname": new_nickname,
                        "invite_code": new_invite_code,
                        "avatar": avatar_path,
                        "friends": [inviter["id"]],
                        "bio": new_bio if new_bio else "🐯 新朋友，请多多关照~",
                        "remaining_invites": 10
                    }
                    friends_inviter = inviter.get("friends", [])
                    friends_inviter.append(new_id)
                    update_user(inviter["id"], {"friends": friends_inviter})
                    add_user(new_user)
                    
                    st.success(f"🎉 注册成功！欢迎加入HeyFoodie！")
                    st.info(f"✨ 你的邀请码是：**{new_invite_code}**")
                    st.caption("🐯 用这个邀请码登录，开始你的美食之旅吧！")
                    st.balloons()

# ========== 主页面 ==========
else:
    current_user = get_user_by_id(st.session_state.user_id)
    if not current_user:
        st.error("用户不存在，请重新登录")
        st.session_state.logged_in = False
        st.rerun()
    
    with st.sidebar:
        st.markdown("---")
        avatar_img = safe_open_image(current_user.get("avatar"))
        if avatar_img:
            st.image(avatar_img, width=100)
        else:
            st.markdown("## 🐯")
        st.markdown(f"### {get_user_display_name(current_user)}")
        st.caption(f"@{current_user['username']}")
        if current_user.get("bio"):
            st.caption(current_user["bio"])
        st.markdown("---")
        st.markdown("#### 🐯 小卷小语")
        st.caption(random_saying())
        st.markdown("---")
        page = st.radio(
            "📖 美食日记",
            ["🏆 美食大王榜", "🎲 今天吃啥捏", "🏠 首页·美食广场", "📝 记录今日美食", "👥 我的饭搭子", "🐯 个人中心"],
            help="和小卷一起探索美食吧！"
        )
        st.markdown("---")
        if st.button("🚪 退出登录", use_container_width=True):
            st.markdown("""
            <script>
            localStorage.removeItem('heyfoodie_user_id');
            localStorage.removeItem('heyfoodie_username');
            </script>
            """, unsafe_allow_html=True)
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.query_params.clear()
            st.rerun()
        st.markdown("---")
        st.caption("🐯 每天都要好好吃饭哦~")
    
    # ========== 美食大王榜 ==========
    if page == "🏆 美食大王榜":
        st.header("🏆 美食大王榜")
        st.caption("看看谁是真正的吃货王者！")
        
        all_users = get_all_users()
        all_recs = get_all_recommendations()
        
        user_stats = {}
        for user in all_users:
            user_id = user["id"]
            user_recs = [r for r in all_recs if r["user_id"] == user_id]
            total_notes = len(user_recs)
            luxury_count = len([r for r in user_recs if r.get("food_type") == "奢侈一把"])
            user_stats[user_id] = {
                "user": user,
                "total_notes": total_notes,
                "luxury_count": luxury_count
            }
        
        sorted_by_notes = sorted(user_stats.values(), key=lambda x: x["total_notes"], reverse=True)
        sorted_by_luxury = sorted(user_stats.values(), key=lambda x: x["luxury_count"], reverse=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 笔记大王榜")
            st.caption("按发布美食日记数量排名")
            if sorted_by_notes:
                medals = ["🥇", "🥈", "🥉"]
                for i, stat in enumerate(sorted_by_notes[:5]):
                    user = stat["user"]
                    medal = medals[i] if i < 3 else f"{i+1}."
                    st.markdown(f"{medal} **{get_user_display_name(user)}** — {stat['total_notes']} 篇")
                    if i == 0:
                        st.caption("👑 美食大王")
            else:
                st.info("暂无数据")
        
        with col2:
            st.markdown("### 🍽️ 奢侈大王榜")
            st.caption("按“奢侈一把”次数排名")
            if sorted_by_luxury:
                medals = ["🥇", "🥈", "🥉"]
                for i, stat in enumerate(sorted_by_luxury[:5]):
                    user = stat["user"]
                    medal = medals[i] if i < 3 else f"{i+1}."
                    st.markdown(f"{medal} **{get_user_display_name(user)}** — {stat['luxury_count']} 次")
                    if i == 0:
                        st.caption("💎 奢侈大王")
            else:
                st.info("暂无数据")
        
        st.markdown("---")
        st.markdown("### 👥 全部美食家")
        all_users_sorted = sorted(user_stats.values(), key=lambda x: x["total_notes"], reverse=True)
        for stat in all_users_sorted:
            user = stat["user"]
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                avatar = safe_open_image(user.get("avatar"))
                if avatar:
                    st.image(avatar, width=40)
                else:
                    st.markdown("🫂")
            with col2:
                st.markdown(f"**{get_user_display_name(user)}** @{user['username']}")
                st.caption(f"📝 {stat['total_notes']} 篇 ｜ 🍽️ 奢侈 {stat['luxury_count']} 次")
            with col3:
                if user["id"] != st.session_state.user_id:
                    friends = get_friends(st.session_state.user_id)
                    is_friend = any(f["id"] == user["id"] for f in friends)
                    if not is_friend:
                        if st.button("➕ 加好友", key=f"add_from_rank_{user['id']}"):
                            success, msg = add_friend(st.session_state.user_id, user["id"])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.caption("✅ 已是饭搭子")
            st.markdown("---")
    
    # ========== 今天吃啥捏 ==========
    elif page == "🎲 今天吃啥捏":
        st.header("🎲 今天吃啥捏")
        st.caption("让命运帮你决定吃什么～")
        
        col1, col2 = st.columns(2)
        with col1:
            recommendations = get_all_recommendations()
            all_cities = list(set([r.get("city", "未知") for r in recommendations]))
            city_options = ["全部"] + all_cities
            selected_city = st.selectbox("📍 选择城市", city_options)
        with col2:
            food_type_options = ["全部", "外卖吃啥", "奢侈一把"]
            selected_type = st.selectbox("🍱 美食类型", food_type_options)
        
        pool = get_lottery_pool(selected_city, selected_type)
        
        if len(pool) == 0:
            st.warning("🐯 没有找到符合条件的推荐，快去记录你的美食吧！")
            if st.button("📝 立即去记录", use_container_width=True, type="primary"):
                st.session_state.page = "📝 记录今日美食"
                st.rerun()
        else:
            st.markdown(f"✨ 当前池子里有 **{len(pool)}** 家美食")
            
            if "lottery_step" not in st.session_state:
                st.session_state.lottery_step = 0
            if "lottery_result" not in st.session_state:
                st.session_state.lottery_result = None
            
            if st.session_state.lottery_step == 0:
                button_text = "🎲 今天吃啥捏"
                if st.button(button_text, use_container_width=True, type="primary"):
                    st.session_state.lottery_result = random.choice(pool)
                    st.session_state.lottery_step = 1
                    st.rerun()
            elif st.session_state.lottery_step == 1:
                button_text = "🔄 不想吃？再抽一次"
                if st.button(button_text, use_container_width=True):
                    st.session_state.lottery_result = random.choice(pool)
                    st.session_state.lottery_step = 2
                    st.rerun()
            elif st.session_state.lottery_step == 2:
                button_text = "🤔 嘿你到底想吃啥"
                if st.button(button_text, use_container_width=True):
                    st.session_state.lottery_result = random.choice(pool)
                    st.session_state.lottery_step = 3
                    st.rerun()
            elif st.session_state.lottery_step == 3:
                button_text = "🔄 重置抽奖"
                if st.button(button_text, use_container_width=True, type="primary"):
                    st.session_state.lottery_result = None
                    st.session_state.lottery_step = 0
                    st.rerun()
            
            if st.session_state.lottery_result:
                rec = st.session_state.lottery_result
                st.markdown("---")
                st.markdown("### 🎉 命运的选择 🎉")
                
                col_img, col_info = st.columns([1, 2])
                with col_img:
                    img = safe_open_image(rec.get("image_path"))
                    if img:
                        st.image(img, use_container_width=True)
                    else:
                        type_icon = "🍱" if rec.get("food_type", "外卖吃啥") == "外卖吃啥" else "🍽️"
                        st.markdown(f"# {type_icon}")
                        st.caption("暂无图片")
                
                with col_info:
                    rec_user = get_user_by_id(rec["user_id"])
                    sweet_icon = rec.get("sweet_category", "")
                    spiciness = rec.get("spiciness", 0)
                    spice_icons = "🌶️" * spiciness if spiciness > 0 else ""
                    taste_icon = sweet_icon if sweet_icon else ""
                    
                    st.markdown(f"""
                    **{rec['restaurant']}**
                    
                    **{rec['dish']}** · {'⭐' * rec['rating']} {rec['rating']}星 · 人均 ¥{rec.get('price', 0)}
                    {spice_icons} {taste_icon}
                    
                    > {rec['reason']}
                    
                    📍 {rec['city']} {rec['district']} · 🏷️ {rec['tags']}
                    """)
                    if rec.get("ate_with"):
                        st.caption(f"👥 和 {rec['ate_with']} 一起吃")
                    if rec_user:
                        st.caption(f"推荐人：{get_user_display_name(rec_user)}")
                
                st.markdown("---")
            else:
                st.info("点击上面的按钮，让命运帮你决定！")
    
    # ========== 首页·美食广场 ==========
    elif page == "🏠 首页·美食广场":
        st.header("🏠 美食广场")
        st.caption(random_saying())
        friends = get_friends(st.session_state.user_id)
        sort_by = st.radio("排序方式", ["🕐 最新发布", "❤️ 点赞最多"], horizontal=True, index=0)
        
        search_key = st.text_input("🔍 搜索店名/菜品/标签", placeholder="例如：火锅、奶茶、华强北")
        st.markdown("### 🔍 筛选美食")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            show_filter = st.selectbox("👀 显示", ["🍜 全部推荐", "👥 只看饭搭子推荐", "🐯 只看我的推荐"])
        with col2:
            recommendations = get_all_recommendations()
            all_cities = list(set([r.get("city", "未知") for r in recommendations]))
            if all_cities:
                filter_city = st.selectbox("📍 按城市筛选", ["🌍 全部"] + all_cities)
            else:
                filter_city = "🌍 全部"
                st.selectbox("📍 按城市筛选", ["🌍 全部"], disabled=True)
        with col3:
            filter_type = st.selectbox("🍱 分类筛选", ["🍱 全部", "🍱 外卖吃啥", "🍽️ 奢侈一把"])
        
        recommendations = get_all_recommendations()
        if sort_by == "🕐 最新发布":
            recommendations_sorted = sorted(recommendations, key=lambda x: x.get("date", ""), reverse=True)
        else:
            recommendations_sorted = sorted(recommendations, key=lambda x: len(x.get("likes", [])), reverse=True)
        
        filtered_recs = []
        for rec in recommendations_sorted:
            if search_key:
                sk = search_key.lower()
                if sk not in rec["restaurant"].lower() and sk not in rec["dish"].lower() and sk not in rec["tags"].lower():
                    continue
            
            if show_filter == "🐯 只看我的推荐" and rec["user_id"] != st.session_state.user_id:
                continue
            if show_filter == "👥 只看饭搭子推荐":
                is_friend = False
                for friend in friends:
                    if rec["user_id"] == friend["id"]:
                        is_friend = True
                        break
                if not is_friend and rec["user_id"] != st.session_state.user_id:
                    continue
            if filter_city != "🌍 全部" and rec.get("city", "未知") != filter_city:
                continue
            if filter_type == "🍱 外卖吃啥" and rec.get("food_type", "外卖吃啥") != "外卖吃啥":
                continue
            if filter_type == "🍽️ 奢侈一把" and rec.get("food_type", "外卖吃啥") != "奢侈一把":
                continue
            filtered_recs.append(rec)
        
        if len(filtered_recs) == 0:
            st.info("🐯 还没有美食推荐，快去记录你的美食吧！")
        else:
            st.markdown(f"🐯 找到 **{len(filtered_recs)}** 条美食推荐")
            
            page_size = 10
            total_pages = (len(filtered_recs) + page_size -1) // page_size
            current_page = st.number_input("页码", min_value=1, max_value=total_pages, value=1)
            start = (current_page-1)*page_size
            end = start + page_size
            paginated = filtered_recs[start:end]
            
            st.markdown("---")
            for rec in paginated:
                rec_user = get_user_by_id(rec["user_id"])
                user_name = get_user_display_name(rec_user) if rec_user else "匿名"
                is_my = (rec["user_id"] == st.session_state.user_id)
                is_friend = any(f["id"] == rec["user_id"] for f in friends)
                
                col_avatar, col_name = st.columns([1, 5])
                with col_avatar:
                    avatar = None
                    if is_my:
                        avatar = safe_open_image(current_user.get("avatar"))
                    elif rec_user:
                        avatar = safe_open_image(rec_user.get("avatar"))
                    if avatar:
                        st.image(avatar, width=40)
                    else:
                        st.markdown("🫂")
                with col_name:
                    if is_my:
                        st.markdown("**🐯 我**")
                    elif is_friend:
                        st.markdown(f"**👥 {user_name}**")
                    else:
                        st.markdown(f"**🍜 {user_name}**")
                
                sweet_icon = rec.get("sweet_category", "")
                spiciness = rec.get("spiciness", 0)
                spice_icons = "🌶️" * spiciness if spiciness > 0 else ""
                taste_icon = sweet_icon
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    type_icon = "🍱" if rec.get("food_type") == "外卖吃啥" else "🍽️"
                    st.markdown(f"""
                    ## {rec['restaurant']} {type_icon}
                    
                    **{rec['dish']}** · {'⭐' * rec['rating']} {rec['rating']}星 · 人均 ¥{rec.get('price', 0)}
                    {spice_icons} {taste_icon}
                    
                    > 💬 {rec['reason']}
                    
                    📍 {rec['city']} {rec['district']} · 🏷️ {rec['tags']}
                    """)
                    if rec.get("ate_with"):
                        st.caption(f"👥 和 {rec['ate_with']} 一起吃")
                    if rec.get("date"):
                        st.caption(f"📅 {rec['date']}")
                
                with col2:
                    img = safe_open_image(rec.get("image_path"))
                    if img:
                        st.image(img, use_container_width=True)
                    else:
                        st.caption("🐯 暂无图片")
                
                like_count = len(rec.get("likes", []))
                liked = st.session_state.user_id in rec.get("likes", [])
                col_like, _ = st.columns([1, 5])
                with col_like:
                    btn_label = f"❤️ {like_count}" if liked else f"🤍 {like_count}"
                    if st.button(btn_label, key=f"like_{rec['id']}"):
                        toggle_like(rec["id"], st.session_state.user_id)
                        st.rerun()
                
                st.markdown("---")
                
                # 编辑和删除按钮（缩进已修复）
                if is_my:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("✏️ 编辑", key=f"edit_{rec['id']}"):
                            st.session_state.editing_rec = rec
                            st.rerun()
                    with col2:
                        # 简化版删除按钮
                        if st.button("🗑️ 删除", key=f"delete_{rec['id']}"):
                            try:
                                delete_recommendation(rec["id"])
                                st.success(f"✅ 已删除「{rec['restaurant']}」")
                                st.rerun()
                            except Exception as e:
                                st.error(f"删除失败: {e}")
        
        # 编辑弹窗
        if "editing_rec" in st.session_state:
            rec_to_edit = st.session_state.editing_rec
            with st.expander("✏️ 编辑美食日记", expanded=True):
                st.markdown(f"### 编辑：{rec_to_edit['restaurant']}")
                friends = get_friends(st.session_state.user_id)
                with st.form("edit_food_form"):
                    current_type = rec_to_edit.get("food_type", "外卖吃啥")
                    type_options = ["🍱 外卖吃啥", "🍽️ 奢侈一把"]
                    type_idx = 0 if current_type == "外卖吃啥" else 1
                    edit_food_type = st.radio("类型", type_options, horizontal=True, index=type_idx)
                    
                    friend_names = [get_user_display_name(f) for f in friends]
                    current_ate = rec_to_edit.get("ate_with", "")
                    current_list = [x.strip() for x in current_ate.split(",") if x.strip()]
                    ate_opts = ["🐯 独自一人"] + friend_names
                    ate_with = st.multiselect("和谁吃", ate_opts, default=current_list)
                    ate_other = st.text_input("其他朋友（逗号分隔）")
                    manual = [x.strip() for x in ate_other.split(",") if x.strip()]
                    ate_with += manual
                    
                    img = safe_open_image(rec_to_edit.get("image_path"))
                    if img:
                        st.image(img, width=150, caption="当前图片")
                        change = st.checkbox("更换图片")
                    else:
                        change = True
                    new_img = None
                    if change:
                        new_img = st.file_uploader("上传新图", type=["jpg","png"])
                    
                    new_reason = st.text_area("推荐理由", value=rec_to_edit.get("reason",""), height=100)
                    new_rating = st.slider("评分",1,5, value=rec_to_edit.get("rating",4))
                    new_tags = st.text_input("标签", value=rec_to_edit.get("tags",""))
                    
                    col1,col2 = st.columns(2)
                    with col1:
                        sub = st.form_submit_button("💾 保存", use_container_width=True, type="primary")
                    with col2:
                        cancel = st.form_submit_button("❌ 取消", use_container_width=True)
                    
                    if sub:
                        updates = {
                            "food_type": "外卖吃啥" if "外卖" in edit_food_type else "奢侈一把",
                            "ate_with": ", ".join([a for a in ate_with if a != "🐯 独自一人"]),
                            "reason": new_reason,
                            "rating": new_rating,
                            "tags": new_tags or "美食"
                        }
                        if new_img:
                            path = save_image(new_img, st.session_state.user_id, rec_to_edit["restaurant"])
                            updates["image_path"] = path
                        update_recommendation(rec_to_edit["id"], updates)
                        st.success("✅ 更新成功")
                        del st.session_state.editing_rec
                        st.rerun()
                    if cancel:
                        del st.session_state.editing_rec
                        st.rerun()
    
    # ========== 记录今日美食 ==========
    elif page == "📝 记录今日美食":
        st.header("📝 记录今日美食")
        st.caption("🐯 分享你吃到的美味！")
        
        friends = get_friends(st.session_state.user_id)
        my_recs = [r for r in get_all_recommendations() if r["user_id"] == st.session_state.user_id]
        
        with st.form("add_food", clear_on_submit=True):
            st.markdown("### 🍽️ 基本信息")
            col1, col2 = st.columns(2)
            with col1:
                city = st.text_input("📍 城市*", placeholder="例如：武汉、深圳")
            with col2:
                district = st.text_input("🏘️ 区域", placeholder="例如：洪山区")
            
            col1, col2 = st.columns(2)
            with col1:
                restaurant = st.text_input("🏠 店名*", placeholder="例如：野妹火锅")
            with col2:
                dish = st.text_input("🍜 菜品名", placeholder="例如：虾滑")
            
            col1, col2 = st.columns(2)
            with col1:
                rating = st.slider("⭐ 评分", 1, 5, 4)
            with col2:
                price = st.number_input("💰 人均价格（元）", min_value=0, max_value=9999, value=50, step=10)
            
            st.markdown("### 🍱 美食分类")
            food_type = st.radio("选择类型", ["🍱 外卖吃啥", "🍽️ 奢侈一把"], horizontal=True)

            # 口味偏好
            st.markdown("### 😋 口味偏好")
            taste_icons = ["🌶️ 辣", "🍰 甜点", "🍦 冰淇淋", "🧋 奶茶"]
            selected_taste = st.radio(
                "选择口味类型",
                options=taste_icons,
                horizontal=True,
                format_func=lambda x: x.split()[0]
            )
            
            selected_icon = selected_taste.split()[0]
            spiciness = 0
            if selected_icon == "🌶️":
                spice_level = st.radio(
                    "🌶️ 辣度",
                    options=["0 (不辣)", "1 (微辣)", "2 (中辣)", "3 (超辣)"],
                    horizontal=True,
                    index=0
                )
                spiciness = int(spice_level.split()[0])

            # 👥 和谁一起吃
            st.markdown("### 👥 和谁一起吃？")
            friend_names = [get_user_display_name(f) for f in friends]
            ate_with_options = ["🐯 独自一人"] + friend_names
            ate_with = st.multiselect("选择好友", ate_with_options)
            ate_with_others = st.text_input("其他朋友（逗号分隔）", placeholder="例如：张三, 李四")
            manual_friends = [x.strip() for x in ate_with_others.split(",") if x.strip()] if ate_with_others else []
            ate_with = ate_with + manual_friends
            
            st.markdown("### 💬 美食评价")
            reason = st.text_area("推荐理由*", placeholder="为什么推荐？有什么必点菜？", height=100)
            
            default_tags = ["火锅","奶茶","烤肉","家常菜","外卖推荐","小众宝藏","甜品","早餐","夜宵","性价比高"]
            selected_tags = st.multiselect("🏷️ 选择标签", default_tags)
            custom_tag = st.text_input("自定义标签（多个用逗号）")
            if custom_tag:
                selected_tags += [t.strip() for t in custom_tag.split(",") if t.strip()]
            tags = ",".join(selected_tags) if selected_tags else "美食"
            
            st.markdown("### 📸 美食照片")
            uploaded_photo = st.file_uploader("上传照片", type=["jpg","png"])
            if uploaded_photo:
                img = Image.open(uploaded_photo)
                img = ImageOps.exif_transpose(img)
                st.image(img, width=200)
            
            submitted = st.form_submit_button("🐯 发布美食日记", use_container_width=True, type="primary")
            
            if submitted:
                if not restaurant or not city or not reason:
                    st.error("请填写店名、城市、理由")
                else:
                    img_path = None
                    if uploaded_photo:
                        img_path = save_image(uploaded_photo, st.session_state.user_id, restaurant)
                    
                    ate_str = ", ".join([a for a in ate_with if a != "🐯 独自一人"])
                    type_val = "外卖吃啥" if "外卖" in food_type else "奢侈一把"
                    tz = ZoneInfo("Asia/Shanghai")
                    now = datetime.datetime.now(tz)
                    
                    icon_to_sweet = {
                        "🌶️": "",
                        "🍰": "🍰",
                        "🍦": "🍦",
                        "🧋": "🧋"
                    }
                    sweet_val = icon_to_sweet.get(selected_icon, "")
                    
                    new_rec = {
                        "id": len(get_all_recommendations()) + 1,
                        "user_id": st.session_state.user_id,
                        "city": city,
                        "district": district or "未填写",
                        "restaurant": restaurant,
                        "dish": dish or "推荐菜品",
                        "rating": rating,
                        "price": price,
                        "reason": reason,
                        "tags": tags,
                        "date": now.strftime("%Y-%m-%d %H:%M"),
                        "image_path": img_path,
                        "ate_with": ate_str,
                        "food_type": type_val,
                        "likes": [],
                        "spiciness": spiciness,
                        "sweet_category": sweet_val
                    }
                    add_recommendation(new_rec)
                    
                    if len(my_recs) == 0:
                        st.toast("🥳 第一条美食日记！小卷撒花～", icon="🎉")
                    else:
                        st.toast(random_saying(), icon="🐯")
                    st.balloons()
                    import time
                    time.sleep(1.5)
                    st.rerun()
    
    # ========== 我的饭搭子 ==========
    elif page == "👥 我的饭搭子":
        st.header("👥 我的饭搭子")
        friends = get_friends(st.session_state.user_id)
        
        st.markdown("### 🍜 我的饭搭子们")
        if len(friends) == 0:
            st.info("🐯 还没有饭搭子，快邀请朋友加入吧！")
        else:
            for friend in friends:
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    avatar = safe_open_image(friend.get("avatar"))
                    if avatar:
                        st.image(avatar, width=60)
                    else:
                        st.markdown("## 🍜")
                with col2:
                    st.markdown(f"### {get_user_display_name(friend)}")
                    st.caption(f"@{friend['username']}")
                with col3:
                    if st.button("❌ 删除", key=f"del_{friend['id']}"):
                        remove_friend(st.session_state.user_id, friend['id'])
                        st.rerun()
                st.markdown("---")
        
        st.markdown("### 🔍 寻找新朋友")
        search_keyword = st.text_input("输入用户名或昵称搜索", placeholder="例如：小明")
        if search_keyword:
            results = search_users(search_keyword)
            if results:
                for user in results:
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        avatar = safe_open_image(user.get("avatar"))
                        if avatar:
                            st.image(avatar, width=50)
                        else:
                            st.markdown("🫂")
                    with col2:
                        st.markdown(f"**{get_user_display_name(user)}**")
                        st.caption(f"@{user['username']}")
                    with col3:
                        if st.button("查看主页", key=f"view_{user['id']}"):
                            st.session_state.view_user_id = user["id"]
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("未找到相关用户")
        
        if "view_user_id" in st.session_state:
            target_id = st.session_state.view_user_id
            target_user = get_user_by_id(target_id)
            if target_user:
                st.markdown("---")
                st.markdown(f"### 👤 {get_user_display_name(target_user)} 的主页")
                col1, col2 = st.columns([1, 3])
                with col1:
                    avatar = safe_open_image(target_user.get("avatar"))
                    if avatar:
                        st.image(avatar, width=100)
                    else:
                        st.markdown("## 🐯")
                with col2:
                    st.markdown(f"**{get_user_display_name(target_user)}**")
                    st.caption(f"@{target_user['username']}")
                    if target_user.get("bio"):
                        st.caption(target_user["bio"])
                
                user_recs = [r for r in get_all_recommendations() if r["user_id"] == target_id]
                st.markdown(f"#### 📝 美食日记 ({len(user_recs)}篇)")
                for rec in user_recs[-5:]:
                    st.markdown(f"**{rec['restaurant']}** · {rec['city']} · {'⭐' * rec['rating']}")
                    img = safe_open_image(rec.get("image_path"))
                    if img:
                        st.image(img, width=150)
                    st.markdown("---")
                
                if target_id not in [f["id"] for f in friends] and target_id != st.session_state.user_id:
                    if st.button("➕ 添加为饭搭子"):
                        success, msg = add_friend(st.session_state.user_id, target_id)
                        if success:
                            st.success(msg)
                            del st.session_state.view_user_id
                            st.rerun()
                        else:
                            st.error(msg)
                
                if st.button("← 返回"):
                    del st.session_state.view_user_id
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 📨 邀请朋友加入")
        st.info("把你的邀请码发给朋友～")
        st.code(current_user["invite_code"])
        if current_user["id"] == 1:
            st.caption("✨ 小卷的邀请码无限制")
        else:
            remaining = current_user.get("remaining_invites", 10)
            st.caption(f"✨ 还可邀请 {remaining} 位朋友")
    
    # ========== 个人中心 ==========
    elif page == "🐯 个人中心":
        st.header("🐯 个人中心")
        
        my_recs = [r for r in get_all_recommendations() if r["user_id"] == st.session_state.user_id]
        friends = get_friends(st.session_state.user_id)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 美食日记", len(my_recs))
        with col2:
            st.metric("👥 饭搭子", len(friends))
        with col3:
            level = "🥉 新手" if len(my_recs) <5 else "🥈 达人" if len(my_recs)<20 else "🥇 美食家"
            st.metric("🍜 美食等级", level)
        
        st.markdown("---")
        
        st.markdown("### 📝 我的美食日记")
        if my_recs:
            for rec in my_recs[:5]:
                col_img, col_info = st.columns([1,4])
                with col_img:
                    img = safe_open_image(rec.get("image_path"))
                    if img:
                        st.image(img, width=80)
                    else:
                        st.markdown("🍽️")
                with col_info:
                    st.markdown(f"**{rec['restaurant']}** | ⭐{rec['rating']} | {rec['city']}")
                    st.caption(rec['reason'][:50] + "..." if len(rec['reason'])>50 else rec['reason'])
        else:
            st.info("还没有记录美食，快去发布第一条吧！")
        
        st.markdown("---")
        
        if st.session_state.user_id == 1:
            with st.expander("🔧 管理员面板"):
                users = get_all_users()
                for u in users:
                    st.write(f"{u['nickname']} (@{u['username']}) - 邀请码: `{u['invite_code']}`")
        
        st.markdown("### ❤️ 我的收藏夹")
        liked_recs = []
        for rec in get_all_recommendations():
            if st.session_state.user_id in rec.get("likes", []):
                liked_recs.append(rec)
        
        if not liked_recs:
            st.info("还没有收藏过美食～")
        else:
            for rec in liked_recs[:10]:
                rec_user = get_user_by_id(rec["user_id"])
                col_img, col_info = st.columns([1,2])
                with col_img:
                    img = safe_open_image(rec.get("image_path"))
                    if img:
                        st.image(img, use_container_width=True)
                    else:
                        st.markdown("🍽️")
                with col_info:
                    st.markdown(f"**{rec['restaurant']}** - {rec_user['nickname']}推荐")
                    st.caption(rec['reason'][:80])
                    if st.button("❤️ 取消收藏", key=f"unlike_{rec['id']}"):
                        toggle_like(rec["id"], st.session_state.user_id)
                        st.rerun()
                st.markdown("---")
        
        st.markdown("---")
        st.markdown("### 🐯 编辑我的小档案")
        col1, col2 = st.columns([1,2])
        with col1:
            avatar = safe_open_image(current_user.get("avatar"))
            if avatar:
                st.image(avatar, width=100)
            else:
                st.markdown("## 🐯")
        with col2:
            new_avatar = st.file_uploader("更换头像", type=["jpg","png"])
            if new_avatar:
                prev = Image.open(new_avatar)
                prev = ImageOps.exif_transpose(prev)
                st.image(prev, width=80)
        
        new_nickname = st.text_input("🍜 昵称", value=current_user.get("nickname", current_user["username"]))
        new_bio = st.text_area("📝 介绍", value=current_user.get("bio",""))
        
        if st.button("💾 保存修改", use_container_width=True):
            updates = {}
            if new_avatar:
                old_path = current_user.get("avatar")
                if old_path and os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except:
                        pass
                path = save_avatar(new_avatar, st.session_state.user_id)
                updates["avatar"] = path
            if new_nickname:
                updates["nickname"] = new_nickname
            updates["bio"] = new_bio
            update_user(st.session_state.user_id, updates)
            st.success("✅ 修改成功！")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📨 我的邀请码")
        st.code(current_user["invite_code"])
        if current_user["id"] == 1:
            st.caption("✨ 小卷的邀请码无限制")
        else:
            remaining = current_user.get("remaining_invites", 10)
            st.caption(f"✨ 还可邀请 {remaining} 位朋友")
