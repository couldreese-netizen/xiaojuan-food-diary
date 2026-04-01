import streamlit as st
import json
import os
from PIL import Image
import datetime
import random

# ========== 有趣的文字库 ==========
GREETINGS = [
    "🐯 小卷发现新美食啦！",
    "🍜 今天吃什么？让小卷告诉你！",
    "🧀 小卷的美食雷达响了！",
    "🎉 和小卷一起开启美食冒险吧！",
    "🐯 嗷呜～小卷推荐的美食准没错！",
    "✨ 小卷的美食日记更新啦！",
    "🍜 跟着小卷，吃遍天下美食！",
]

EATING_WITH = [
    "和小卷一起分享",
    "和好朋友一起",
    "超开心的聚餐",
    "美食让友谊更美味",
]

def random_greeting():
    return random.choice(GREETINGS)

def random_eating_tag():
    return random.choice(EATING_WITH)

# ========== 数据操作函数 ==========
def load_data():
    """从JSON文件读取数据"""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    if not os.path.exists("data/restaurants.json"):
        default_data = {
            "users": [
                {
                    "id": 1,
                    "username": "xiaojuan",
                    "nickname": "🐯 小卷 🧀",
                    "invite_code": "XIAOJUAN2024",
                    "avatar": None,
                    "friends": [],
                    "bio": "🍜 美食探险家 | 小卷的觅食日记 | 一起吃遍全世界！"
                }
            ],
            "recommendations": []
        }
        with open("data/restaurants.json", "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data
    
    try:
        with open("data/restaurants.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        default_data = {
            "users": [
                {
                    "id": 1,
                    "username": "xiaojuan",
                    "nickname": "🐯 小卷 🧀",
                    "invite_code": "XIAOJUAN2024",
                    "avatar": None,
                    "friends": [],
                    "bio": "🍜 美食探险家 | 小卷的觅食日记 | 一起吃遍全世界！"
                }
            ],
            "recommendations": []
        }
        with open("data/restaurants.json", "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data

def save_data(data):
    """保存数据到JSON文件"""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    with open("data/restaurants.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_avatar(uploaded_file, user_id):
    """保存用户头像"""
    if not os.path.exists("avatars"):
        os.makedirs("avatars")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_{user_id}_{timestamp}.jpg"
    filepath = os.path.join("avatars", filename)
    
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return filepath

def save_image(uploaded_file, user_id, restaurant_name):
    """保存美食图片"""
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = "".join(c for c in restaurant_name if c.isalnum() or c in " _-")
    filename = f"{user_id}_{timestamp}_{clean_name}.jpg"
    filepath = os.path.join("uploads", filename)
    
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return filepath

def generate_invite_code():
    """生成有趣的邀请码"""
    import random
    import string
    prefixes = ["XIAO", "JUAN", "YUMMY", "FOOD", "NOM", "CHEESE", "EAT", "ROLL"]
    prefix = random.choice(prefixes)
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"

def get_all_users(data):
    """获取所有用户列表"""
    return [{"id": u["id"], "nickname": u.get("nickname", u["username"])} for u in data["users"]]

def add_friend(data, user_id, friend_id):
    """添加好友"""
    current_user = None
    for u in data["users"]:
        if u["id"] == user_id:
            current_user = u
            break
    
    if friend_id in current_user["friends"]:
        return False, "已经是好朋友啦！"
    
    current_user["friends"].append(friend_id)
    
    for u in data["users"]:
        if u["id"] == friend_id:
            if user_id not in u["friends"]:
                u["friends"].append(user_id)
            break
    
    save_data(data)
    return True, "🎉 成为好朋友啦！一起探索美食吧！"

def remove_friend(data, user_id, friend_id):
    """删除好友"""
    for u in data["users"]:
        if u["id"] == user_id:
            if friend_id in u["friends"]:
                u["friends"].remove(friend_id)
        if u["id"] == friend_id:
            if user_id in u["friends"]:
                u["friends"].remove(user_id)
    
    save_data(data)
    return True

def get_friends(data, user_id):
    """获取好友列表"""
    friends = []
    for u in data["users"]:
        if u["id"] == user_id:
            for friend_id in u["friends"]:
                for friend in data["users"]:
                    if friend["id"] == friend_id:
                        friends.append(friend)
            break
    return friends

def get_user_display_name(user):
    """获取用户显示名称"""
    return user.get("nickname", user["username"])

def check_username_exists(data, username):
    """检查用户名是否已存在"""
    for u in data["users"]:
        if u["username"] == username:
            return True
    return False

# ========== 页面设置 ==========
st.set_page_config(
    page_title="🐯 小卷的美食日记", 
    page_icon="🍜", 
    layout="wide"
)

# ========== 初始化登录状态 ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None

# ========== 未登录时显示登录页面 ==========
if not st.session_state.logged_in:
    # 可爱的欢迎动画效果
    st.markdown("""
    <style>
    .big-title {
        text-align: center;
        font-size: 3em;
        animation: bounce 1s ease;
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="big-title">🐯 🧀 🍜</p>', unsafe_allow_html=True)
        st.title("🍜 小卷的美食日记")
        st.markdown("### 好朋友才知道的宝藏小店")
        st.caption("🐯 和小卷一起，记录每一顿美好的饭！")
    
    # 创建两个标签页：登录 和 注册
    tab1, tab2 = st.tabs(["🔐 登录", "🎉 加入美食大家庭"])
    
    with tab1:
        invite_code = st.text_input(
            "请输入邀请码", 
            placeholder="例如：XIAOJUAN2024",
            help="问小卷要邀请码哦~",
            key="login_code"
        )
        
        if st.button("🐯 开启美食之旅", key="login_btn", use_container_width=True):
            data = load_data()
            user = None
            for u in data["users"]:
                if u["invite_code"] == invite_code:
                    user = u
                    break
            
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user["id"]
                st.session_state.user_name = user["username"]
                st.success(f"🎉 欢迎回来，{get_user_display_name(user)}！")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ 邀请码不对哦，问小卷要一个吧~")
    
    with tab2:
        st.markdown("### 🎉 加入小卷的美食大家庭")
        st.caption("需要朋友给你邀请码才能加入哦~")
        
        col1, col2 = st.columns(2)
        with col1:
            register_invite_code = st.text_input("✨ 邀请码", placeholder="朋友的邀请码", key="reg_code")
        with col2:
            new_username = st.text_input("🐯 用户名（登录用）", placeholder="英文或数字，例如：xiaoming", key="reg_username")
        
        new_nickname = st.text_input("🍜 昵称（显示用）", placeholder="例如：爱吃的小明", key="reg_nickname")
        new_bio = st.text_area("📝 一句话介绍自己", placeholder="介绍一下自己吧~", key="reg_bio")
        
        st.markdown("**📸 上传头像（让朋友们认识你！）**")
        new_avatar = st.file_uploader("点击上传头像", type=["jpg", "jpeg", "png"], key="reg_avatar")
        
        if new_avatar:
            avatar_preview = Image.open(new_avatar)
            st.image(avatar_preview, width=100)
            st.caption("🐯 好可爱的头像！")
        
        if st.button("🎉 注册加入", key="register_btn", use_container_width=True):
            if not register_invite_code:
                st.error("请输入邀请码")
            elif not new_username:
                st.error("请输入用户名")
            elif not new_nickname:
                st.error("请输入昵称")
            else:
                data = load_data()
                
                inviter = None
                for u in data["users"]:
                    if u["invite_code"] == register_invite_code:
                        inviter = u
                        break
                
                if not inviter:
                    st.error("邀请码无效，问小卷要一个正确的吧~")
                elif check_username_exists(data, new_username):
                    st.error("用户名已被使用，换一个吧~")
                else:
                    avatar_path = None
                    if new_avatar:
                        new_id = len(data["users"]) + 1
                        avatar_path = save_avatar(new_avatar, new_id)
                    
                    new_id = len(data["users"]) + 1
                    new_user = {
                        "id": new_id,
                        "username": new_username,
                        "nickname": new_nickname,
                        "invite_code": generate_invite_code(),
                        "avatar": avatar_path,
                        "friends": [inviter["id"]],
                        "bio": new_bio if new_bio else "🐯 新朋友，请多多关照~"
                    }
                    
                    for u in data["users"]:
                        if u["id"] == inviter["id"]:
                            u["friends"].append(new_id)
                            break
                    
                    data["users"].append(new_user)
                    save_data(data)
                    
                    st.success(f"🎉 注册成功！欢迎加入美食大家庭！")
                    st.info(f"✨ 你的邀请码是：**{new_user['invite_code']}**")
                    st.balloons()
                    st.caption("🐯 用这个邀请码登录，开始你的美食之旅吧！")

# ========== 已登录时显示主页面 ==========
else:
    data = load_data()
    current_user = None
    for u in data["users"]:
        if u["id"] == st.session_state.user_id:
            current_user = u
            break
    
    # 侧边栏显示用户信息
    with st.sidebar:
        st.markdown("---")
        
        # 显示头像
        if current_user and current_user.get("avatar") and os.path.exists(current_user["avatar"]):
            avatar_img = Image.open(current_user["avatar"])
            st.image(avatar_img, width=100)
        else:
            # 默认头像
            st.markdown("## 🐯")
        
        st.markdown(f"### {get_user_display_name(current_user)}")
        st.caption(f"@{current_user['username']}")
        
        if current_user.get("bio"):
            st.caption(current_user["bio"])
        
        st.markdown("---")
        
        # 导航菜单
        page = st.radio(
            "📖 美食日记",
            ["🏠 首页·美食广场", "📝 记录今日美食", "👥 我的饭搭子", "🐯 小卷的百宝箱"],
            help="和小卷一起探索美食吧！"
        )
        
        st.markdown("---")
        st.caption("🐯 每天都要好好吃饭哦~")
    
    # ========== 首页·美食广场 ==========
    if page == "🏠 首页·美食广场":
        st.header("🏠 美食广场")
        st.caption(random_greeting())
        
        data = load_data()
        friends = get_friends(data, st.session_state.user_id)
        
        # 筛选
        st.markdown("### 🔍 筛选美食")
        col1, col2, col3 = st.columns(3)
        with col1:
            show_filter = st.selectbox(
                "👀 显示", 
                ["🍜 全部推荐", "👥 只看饭搭子推荐", "🐯 只看我的推荐"]
            )
        with col2:
            all_cities = list(set([r.get("city", "未知") for r in data["recommendations"]]))
            if all_cities:
                filter_city = st.selectbox("📍 按城市筛选", ["🌍 全部"] + all_cities)
            else:
                filter_city = "🌍 全部"
                st.selectbox("📍 按城市筛选", ["🌍 全部"], disabled=True)
        
        recommendations = data["recommendations"]
        
        # 应用筛选
        filtered_recs = []
        for rec in recommendations:
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
            filtered_recs.append(rec)
        
        if len(filtered_recs) == 0:
            st.info("🐯 还没有美食推荐，快去记录你的美食吧！")
            if st.button("📝 我要记录美食！"):
                st.session_state.page = "📝 记录今日美食"
                st.rerun()
        else:
            st.markdown(f"🐯 找到 **{len(filtered_recs)}** 条美食推荐")
            st.markdown("---")
            
            for rec in filtered_recs:
                rec_user = None
                for u in data["users"]:
                    if u["id"] == rec["user_id"]:
                        rec_user = u
                        break
                
                user_name = get_user_display_name(rec_user) if rec_user else "匿名"
                is_my = (rec["user_id"] == st.session_state.user_id)
                is_friend = False
                for friend in friends:
                    if rec["user_id"] == friend["id"]:
                        is_friend = True
                        break
                
                if is_my:
                    user_label = "🐯 我"
                elif is_friend:
                    user_label = f"👥 {user_name}"
                else:
                    user_label = f"🍜 {user_name}"
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    **{user_label} 推荐**
                    
                    ## 🍽️ {rec['restaurant']}
                    **{rec['dish']}** · {'⭐' * rec['rating']} {rec['rating']}星 · {rec['price']}
                    
                    > 💬 {rec['reason']}
                    
                    📍 {rec['city']} {rec['district']} · 🏷️ {rec['tags']}
                    """)
                    
                    if "ate_with" in rec and rec["ate_with"]:
                        st.caption(f"👥 和 {rec['ate_with']} 一起吃")
                    else:
                        st.caption(f"🍜 {random_eating_tag()}")
                    
                    if "date" in rec:
                        st.caption(f"📅 {rec['date']}")
                
                with col2:
                    if "image_path" in rec and rec["image_path"] and os.path.exists(rec["image_path"]):
                        try:
                            image = Image.open(rec["image_path"])
                            st.image(image, use_container_width=True)
                        except:
                            st.caption("📷 图片加载失败")
                    else:
                        st.caption("🐯 想象一下~一定很好吃！")
                
                st.markdown("---")
    
    # ========== 记录今日美食 ==========
    elif page == "📝 记录今日美食":
        st.header("📝 记录今日美食")
        st.caption("🐯 快把你吃到的美味分享给朋友们吧！")
        
        data = load_data()
        friends = get_friends(data, st.session_state.user_id)
        
        with st.form("add_food", clear_on_submit=True):
            st.markdown("### 🍽️ 吃了什么？")
            
            col1, col2 = st.columns(2)
            with col1:
                city = st.text_input("📍 城市*", placeholder="例如：武汉、深圳、北京")
            with col2:
                district = st.text_input("🏘️ 区域", placeholder="例如：洪山区、南山区")
            
            col1, col2 = st.columns(2)
            with col1:
                restaurant = st.text_input("🏠 店名*", placeholder="例如：野妹火锅")
            with col2:
                dish = st.text_input("🍜 菜品名", placeholder="例如：虾滑")
            
            col1, col2 = st.columns(2)
            with col1:
                rating = st.slider("⭐ 评分", 1, 5, 4, help="1星不好吃，5星超好吃！")
            with col2:
                price = st.selectbox("💰 价格", ["¥ (平价)", "¥¥ (中等)", "¥¥¥ (稍贵)"])
            
            st.markdown("### 👥 和谁一起吃？")
            
            friend_names = [get_user_display_name(f) for f in friends]
            ate_with_options = ["🐯 独自一人"] + friend_names
            ate_with = st.multiselect(
                "选择和谁一起吃的",
                ate_with_options,
                help="记录和谁一起分享美食，让回忆更美好"
            )
            
            st.markdown("### 💬 美食评价")
            
            reason = st.text_area("推荐理由*", placeholder="为什么推荐？有什么必点菜？有什么小贴士？", height=100)
            tags = st.text_input("🏷️ 标签", placeholder="例如：火锅,必点,隐藏菜单,适合聚餐")
            
            st.markdown("### 📸 美食照片")
            
            uploaded_photo = st.file_uploader(
                "上传美食照片（让朋友流口水！）",
                type=["jpg", "jpeg", "png"]
            )
            
            if uploaded_photo:
                image = Image.open(uploaded_photo)
                st.image(image, width=200)
                st.caption("🐯 哇！看起来好好吃！")
            
            submitted = st.form_submit_button("🐯 发布美食日记", use_container_width=True, type="primary")
            
            if submitted:
                if not restaurant or not city or not reason:
                    st.error("请填写店名、城市和推荐理由")
                else:
                    data = load_data()
                    
                    image_path = None
                    if uploaded_photo:
                        image_path = save_image(uploaded_photo, st.session_state.user_id, restaurant)
                    
                    ate_with_str = ", ".join([a for a in ate_with if a != "🐯 独自一人"]) if ate_with else ""
                    
                    new_rec = {
                        "id": len(data["recommendations"]) + 1,
                        "user_id": st.session_state.user_id,
                        "city": city,
                        "district": district or "未填写",
                        "restaurant": restaurant,
                        "dish": dish or "推荐菜品",
                        "rating": rating,
                        "price": price.split(" ")[0],
                        "reason": reason,
                        "tags": tags or "美食",
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "image_path": image_path,
                        "ate_with": ate_with_str
                    }
                    
                    data["recommendations"].append(new_rec)
                    save_data(data)
                    
                    st.success("🎉 美食日记发布成功！朋友们都看到啦！")
                    st.balloons()
    
    # ========== 我的饭搭子 ==========
    elif page == "👥 我的饭搭子":
        st.header("👥 我的饭搭子")
        st.caption("🐯 和好朋友一起吃饭更香！")
        
        data = load_data()
        friends = get_friends(data, st.session_state.user_id)
        
        st.markdown("### 🍜 我的饭搭子们")
        
        if len(friends) == 0:
            st.info("🐯 还没有饭搭子，快邀请朋友加入吧！")
        else:
            for friend in friends:
                col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
                with col1:
                    if friend.get("avatar") and os.path.exists(friend["avatar"]):
                        avatar_img = Image.open(friend["avatar"])
                        st.image(avatar_img, width=60)
                    else:
                        st.markdown("## 🍜")
                with col2:
                    st.markdown(f"### {get_user_display_name(friend)}")
                    st.caption(f"@{friend['username']}")
                with col3:
                    if friend.get("bio"):
                        st.caption(friend["bio"])
                with col4:
                    if st.button("❌ 删除", key=f"del_{friend['id']}"):
                        remove_friend(data, st.session_state.user_id, friend['id'])
                        st.rerun()
                st.markdown("---")
        
        # 添加好友
        st.markdown("### 🎉 认识新朋友")
        
        all_users = [u for u in data["users"] if u["id"] != st.session_state.user_id]
        friend_ids = [f["id"] for f in friends]
        available_users = [u for u in all_users if u["id"] not in friend_ids]
        
        if available_users:
            friend_options = {get_user_display_name(u): u["id"] for u in available_users}
            selected_name = st.selectbox("选择想认识的朋友", list(friend_options.keys()))
            
            if st.button("🤝 成为饭搭子", use_container_width=True):
                success, msg = add_friend(data, st.session_state.user_id, friend_options[selected_name])
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("🐯 暂时没有其他朋友，邀请更多人加入吧！")
        
        st.markdown("---")
        st.markdown("### 📨 邀请朋友加入")
        st.info("🐯 把你的邀请码发给朋友，他们注册后就能成为你的饭搭子啦！")
        st.code(current_user["invite_code"])
        st.caption("✨ 朋友用这个邀请码注册，会自动成为你的好友哦！")
    
    # ========== 小卷的百宝箱 ==========
    elif page == "🐯 小卷的百宝箱":
        st.header("🐯 小卷的百宝箱")
        st.caption("这里藏着美食家的小秘密~")
        
        # 重新加载最新数据
        data = load_data()
        
        # 重新获取当前用户
        current_user = None
        for u in data["users"]:
            if u["id"] == st.session_state.user_id:
                current_user = u
                break
        
        my_recs = [r for r in data["recommendations"] if r["user_id"] == st.session_state.user_id]
        friends = get_friends(data, st.session_state.user_id)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 美食日记", len(my_recs), delta="篇")
        with col2:
            st.metric("👥 饭搭子", len(friends), delta="位")
        with col3:
            level = "🥉 美食新手" if len(my_recs) < 5 else "🥈 美食达人" if len(my_recs) < 20 else "🥇 美食家"
            st.metric("🍜 美食等级", level, delta=f"{len(my_recs)}篇")
        
        st.markdown("---")
        
        # 编辑个人信息
        st.markdown("### 🐯 编辑我的小档案")
        
        # 头像显示
        col1, col2 = st.columns([1, 2])
        with col1:
            if current_user.get("avatar") and os.path.exists(current_user["avatar"]):
                avatar_img = Image.open(current_user["avatar"])
                st.image(avatar_img, width=100)
            else:
                st.markdown("## 🐯")
                st.caption("点击下方按钮上传头像")
        
        with col2:
            st.markdown("**📸 上传新头像**")
            new_avatar = st.file_uploader(
                "点击选择图片", 
                type=["jpg", "jpeg", "png"], 
                key="edit_avatar",
                label_visibility="collapsed"
            )
            if new_avatar:
                avatar_preview = Image.open(new_avatar)
                st.image(avatar_preview, width=80)
                st.caption("新头像预览")
        
        # 昵称输入
        new_nickname = st.text_input(
            "🍜 昵称", 
            value=current_user.get("nickname", current_user["username"]),
            key="edit_nickname"
        )
        
        # 简介输入
        new_bio = st.text_area(
            "📝 一句话介绍自己", 
            value=current_user.get("bio", ""),
            key="edit_bio",
            height=80
        )
        
        # 保存按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            save_clicked = st.button("💾 保存小档案", use_container_width=True, type="primary")
        
        if save_clicked:
            # 重新加载最新数据
            data = load_data()
            
            # 找到当前用户
            current_user = None
            for u in data["users"]:
                if u["id"] == st.session_state.user_id:
                    current_user = u
                    break
            
            # 处理头像
            if new_avatar:
                # 删除旧头像文件（可选）
                if current_user.get("avatar") and os.path.exists(current_user["avatar"]):
                    try:
                        os.remove(current_user["avatar"])
                    except:
                        pass
                
                # 保存新头像
                avatar_path = save_avatar(new_avatar, st.session_state.user_id)
                current_user["avatar"] = avatar_path
            
            # 更新昵称
            if new_nickname:
                current_user["nickname"] = new_nickname
            
            # 更新简介
            current_user["bio"] = new_bio
            
            # 保存到文件
            save_data(data)
            
            # 显示成功消息
            st.success("🎉 小档案更新成功！")
            st.balloons()
            
            # 刷新页面
            st.rerun()
        
        st.markdown("---")
        
        # 我的邀请码
        st.markdown("### 📨 我的邀请码")
        st.code(current_user["invite_code"])
        st.caption("🐯 把邀请码发给朋友，一起探索美食！")
        
        st.markdown("---")
        
        # 我的推荐记录
        st.markdown("### 📝 我的美食日记")
        if len(my_recs) == 0:
            st.info("🐯 还没有美食日记，快去记录你的第一顿美食吧！")
            if st.button("🍜 记录今日美食"):
                st.session_state.page = "📝 记录今日美食"
                st.rerun()
        else:
            for rec in my_recs[-5:]:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"""
                        **{rec['restaurant']}** · {rec['city']} {rec['district']}
                        {'⭐' * rec['rating']} {rec['rating']}星
                        """)
                    with col2:
                        st.caption(f"📅 {rec.get('date', '未知')}")
                st.markdown("---")