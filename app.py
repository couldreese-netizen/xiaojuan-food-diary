import streamlit as st
import json
import os
from PIL import Image, ImageOps
import datetime
import random
import re
from zoneinfo import ZoneInfo

# ========== 小卷语录库 ==========
XIAOJUAN_SAYINGS = [
    "🐯 哇塞！看起来好美味～小卷也想吃！",
    "🧀 小卷闻到香味啦，快分享给好朋友！",
    "🍜 今天也是被美食治愈的一天～",
    "✨ 小卷悄悄记下你的美食日记啦！",
    "🐯 嗷呜～这个推荐太棒了，小卷要偷偷收藏！",
    "💛 和朋友一起吃饭最开心啦！",
    "📝 小卷的美食雷达又响啦！",
    "🎉 你太会吃了！小卷为你鼓掌～",
    "🍱 下次带小卷一起去吃好不好？",
    "🌟 你的美食日记闪闪发光！"
]

def random_saying():
    return random.choice(XIAOJUAN_SAYINGS)

# ========== 数据操作函数 ==========
def load_data():
    """从JSON文件读取数据"""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    if not os.path.exists("data/restaurants.json"):
        default_data = {
            "users": [],
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
            "users": [],
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
    """保存并裁剪用户头像为1:1正方形"""
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
    """保存美食图片，自动修正方向"""
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
    """根据用户名生成邀请码"""
    import random
    import string
    
    username_clean = re.sub(r'[^a-zA-Z]', '', username)
    prefix = username_clean[:6].upper() if username_clean else "USER"
    suffix = ''.join(random.choices(string.digits, k=4))
    
    return f"{prefix}{suffix}"

def check_username_exists(data, username):
    """检查用户名是否已存在"""
    for u in data["users"]:
        if u["username"].lower() == username.lower():
            return True
    return False

def check_invite_code_valid(data, invite_code):
    """检查邀请码是否有效，返回用户对象"""
    for u in data["users"]:
        if u["invite_code"] == invite_code:
            return u
    return None

def login_user(data, username, invite_code):
    """通过用户名和邀请码登录"""
    for u in data["users"]:
        if u["username"].lower() == username.lower() and u["invite_code"] == invite_code:
            return u
    return None

def get_user_by_id(data, user_id):
    """通过ID获取用户"""
    for u in data["users"]:
        if u["id"] == user_id:
            return u
    return None

def add_friend(data, user_id, friend_id):
    """添加好友（双向）"""
    current_user = get_user_by_id(data, user_id)
    if friend_id in current_user["friends"]:
        return False, "已经是好朋友啦！"
    
    current_user["friends"].append(friend_id)
    
    friend = get_user_by_id(data, friend_id)
    if user_id not in friend["friends"]:
        friend["friends"].append(user_id)
    
    save_data(data)
    return True, "🎉 成为好朋友啦！一起探索美食吧！"

def remove_friend(data, user_id, friend_id):
    """删除好友"""
    current_user = get_user_by_id(data, user_id)
    if friend_id in current_user["friends"]:
        current_user["friends"].remove(friend_id)
    
    friend = get_user_by_id(data, friend_id)
    if user_id in friend["friends"]:
        friend["friends"].remove(user_id)
    
    save_data(data)
    return True

def get_friends(data, user_id):
    """获取好友列表"""
    current_user = get_user_by_id(data, user_id)
    friends = []
    for friend_id in current_user.get("friends", []):
        friend = get_user_by_id(data, friend_id)
        if friend:
            friends.append(friend)
    return friends

def get_user_display_name(user):
    """获取用户显示名称"""
    return user.get("nickname", user["username"])

def add_initial_user_if_needed(data):
    """如果没有用户，创建小卷作为第一个用户（无限制邀请）"""
    if len(data["users"]) == 0:
        new_user = {
            "id": 1,
            "username": "xiaojuan",
            "nickname": "🐯 小卷 🧀",
            "invite_code": "XIAOJUAN2024",
            "avatar": None,
            "friends": [],
            "bio": "🍜 美食探险家 | 小卷的觅食日记 | 一起吃遍全世界！",
            "remaining_invites": -1   # -1 表示无限制
        }
        data["users"].append(new_user)
        save_data(data)
        return new_user
    return None

def search_users(data, keyword):
    """根据关键词搜索用户（排除自己）"""
    keyword_lower = keyword.lower()
    results = []
    for u in data["users"]:
        if u["id"] == st.session_state.user_id:
            continue
        if (keyword_lower in u["username"].lower() or 
            keyword_lower in u.get("nickname", "").lower()):
            results.append(u)
    return results

# ========== 抽奖轮盘函数 ==========
def get_lottery_pool(data, city, food_type):
    """根据筛选条件获取抽奖池（点赞前5 + 最新前5，去重）"""
    filtered = []
    for rec in data["recommendations"]:
        # 城市筛选
        if city != "全部" and rec.get("city", "") != city:
            continue
        # 类型筛选
        rec_type = rec.get("food_type", "外卖吃啥")
        if food_type != "全部" and rec_type != food_type:
            continue
        filtered.append(rec)
    
    # 按点赞数排序取前5
    sorted_by_likes = sorted(filtered, key=lambda x: len(x.get("likes", [])), reverse=True)
    top_likes = sorted_by_likes[:5]
    
    # 按日期排序取前5（最新）
    sorted_by_date = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)
    top_recent = sorted_by_date[:5]
    
    # 合并去重（用id作为唯一标识）
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

# ========== 记住登录状态（URL参数） ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None

if not st.session_state.logged_in:
    user_id_param = st.query_params.get("user_id")
    username_param = st.query_params.get("username")
    
    if user_id_param and username_param:
        data = load_data()
        try:
            user = get_user_by_id(data, int(user_id_param))
            if user and user["username"] == username_param:
                st.session_state.logged_in = True
                st.session_state.user_id = user["id"]
                st.session_state.user_name = user["username"]
                st.rerun()
        except:
            pass

data = load_data()
add_initial_user_if_needed(data)

# ========== 未登录时显示登录页面 ==========
if not st.session_state.logged_in:
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
                data = load_data()
                user = login_user(data, login_username, login_invite_code)
                
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["username"]
                    st.query_params["user_id"] = user["id"]
                    st.query_params["username"] = user["username"]
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
                data = load_data()
                
                inviter = check_invite_code_valid(data, friend_code)
                if not inviter:
                    st.error("邀请码无效，问朋友要一个正确的吧~")
                elif check_username_exists(data, new_username):
                    st.error("用户名已被使用，换一个吧~")
                else:
                    # 检查邀请人剩余邀请次数
                    remaining = inviter.get("remaining_invites", 10)
                    if remaining == 0:
                        st.error("邀请人的邀请次数已用完，无法继续邀请新朋友")
                        st.stop()
                    if remaining > 0:
                        # 普通用户减少邀请次数
                        inviter["remaining_invites"] = remaining - 1
                    
                    new_id = max([u["id"] for u in data["users"]], default=0) + 1
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
                        "remaining_invites": 10  # 新用户初始可邀请10人
                    }
                    
                    # 将新用户加为邀请人的好友
                    for u in data["users"]:
                        if u["id"] == inviter["id"]:
                            u["friends"].append(new_id)
                            break
                    
                    data["users"].append(new_user)
                    save_data(data)
                    
                    st.success(f"🎉 注册成功！欢迎加入HeyFoodie！")
                    st.info(f"✨ 你的邀请码是：**{new_invite_code}**")
                    st.caption("🐯 用这个邀请码登录，开始你的美食之旅吧！")
                    st.balloons()

# ========== 已登录时显示主页面 ==========
else:
    data = load_data()
    current_user = get_user_by_id(data, st.session_state.user_id)
    
    if not current_user:
        st.error("用户不存在，请重新登录")
        st.session_state.logged_in = False
        st.rerun()
    
    with st.sidebar:
        st.markdown("---")
        
        if current_user.get("avatar") and os.path.exists(current_user["avatar"]):
            avatar_img = Image.open(current_user["avatar"])
            st.image(avatar_img, width=100)
        else:
            st.markdown("## 🐯")
        
        st.markdown(f"### {get_user_display_name(current_user)}")
        st.caption(f"@{current_user['username']}")
        
        if current_user.get("bio"):
            st.caption(current_user["bio"])
        
        st.markdown("---")
        
        # 小卷助手随机语录
        st.markdown("#### 🐯 小卷小语")
        st.caption(random_saying())
        st.markdown("---")
        
        page = st.radio(
            "📖 美食日记",
            ["🎲 今天吃啥", "🏠 首页·美食广场", "📝 记录今日美食", "👥 我的饭搭子", "🐯 个人中心"],
            help="和小卷一起探索美食吧！"
        )
        
        st.markdown("---")
        st.caption("🐯 每天都要好好吃饭哦~")
    
    # ========== 今天吃啥（抽奖轮盘） ==========
    if page == "🎲 今天吃啥":
        st.header("🎲 今天吃啥")
        st.caption("让命运帮你决定吃什么～ 小卷也会帮你筛选好店！")
        
        # 筛选条件
        col1, col2 = st.columns(2)
        with col1:
            # 获取所有城市
            data = load_data()
            all_cities = list(set([r.get("city", "未知") for r in data["recommendations"]]))
            city_options = ["全部"] + all_cities
            selected_city = st.selectbox("📍 选择城市", city_options)
        with col2:
            food_type_options = ["全部", "外卖吃啥", "奢侈一把"]
            selected_type = st.selectbox("🍱 美食类型", food_type_options)
        
        # 获取抽奖池
        pool = get_lottery_pool(data, selected_city, selected_type)
        
        if len(pool) == 0:
            st.warning("🐯 没有找到符合条件的推荐，请先添加美食日记或调整筛选条件～")
        else:
            st.markdown(f"✨ 当前池子里有 **{len(pool)}** 家美食等你翻牌！")
            
            # 初始化抽奖状态
            if "lottery_result" not in st.session_state:
                st.session_state.lottery_result = None
            if "lottery_count" not in st.session_state:
                st.session_state.lottery_count = 0  # 0=未抽，1=第一次，2=第二次，3=第三次
            
            # 三个按钮
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("🎲 今天吃啥", use_container_width=True):
                    if len(pool) > 0:
                        st.session_state.lottery_result = random.choice(pool)
                        st.session_state.lottery_count = 1
                        st.rerun()
            with col_btn2:
                if st.button("🔄 不想吃？再抽一次", use_container_width=True):
                    if len(pool) > 0:
                        st.session_state.lottery_result = random.choice(pool)
                        if st.session_state.lottery_count < 2:
                            st.session_state.lottery_count = 2
                        else:
                            st.session_state.lottery_count = 3
                        st.rerun()
            with col_btn3:
                if st.button("🤔 嘿你到底想吃啥", use_container_width=True):
                    if len(pool) > 0:
                        st.session_state.lottery_result = random.choice(pool)
                        st.session_state.lottery_count = 3
                        st.rerun()
            
            # 显示抽奖结果
            if st.session_state.lottery_result:
                rec = st.session_state.lottery_result
                st.markdown("---")
                st.markdown("### 🎉 命运的选择 🎉")
                
                # 布局：左侧图片，右侧信息
                col_img, col_info = st.columns([1, 2])
                with col_img:
                    if rec.get("image_path") and os.path.exists(rec["image_path"]):
                        try:
                            img = Image.open(rec["image_path"])
                            st.image(img, use_container_width=True)
                        except:
                            st.markdown("📷 图片加载失败")
                    else:
                        type_icon = "🍱" if rec.get("food_type", "外卖吃啥") == "外卖吃啥" else "🍽️"
                        st.markdown(f"# {type_icon}")
                        st.caption("暂无图片")
                
                with col_info:
                    type_icon = "🍱" if rec.get("food_type", "外卖吃啥") == "外卖吃啥" else "🍽️"
                    st.markdown(f"""
                    **{rec['restaurant']}**  {type_icon}
                    
                    **{rec['dish']}** · {'⭐' * rec['rating']} {rec['rating']}星 · 人均 ¥{rec.get('price', 0)}
                    
                    > {rec['reason']}
                    
                    📍 {rec['city']} {rec['district']} · 🏷️ {rec['tags']}
                    """)
                    
                    if rec.get("ate_with"):
                        st.caption(f"👥 和 {rec['ate_with']} 一起吃")
                    
                    # 显示推荐人
                    rec_user = get_user_by_id(data, rec["user_id"])
                    if rec_user:
                        st.caption(f"推荐人：{get_user_display_name(rec_user)}")
                
                # 根据抽奖次数显示俏皮话
                if st.session_state.lottery_count == 1:
                    st.caption("🐯 今天的第一抽！就它啦～")
                elif st.session_state.lottery_count == 2:
                    st.caption("🐯 第二次机会，换个口味也不错！")
                elif st.session_state.lottery_count == 3:
                    st.caption("🐯 第三次了！再犹豫就没饭吃啦！就它！")
                
                st.markdown("---")
                
                # 重置按钮
                if st.button("🔄 重置抽奖", use_container_width=True):
                    st.session_state.lottery_result = None
                    st.session_state.lottery_count = 0
                    st.rerun()
            else:
                st.info("点击上面的按钮，让命运帮你决定今天吃什么！")
    
    # ========== 首页·美食广场 ==========
    elif page == "🏠 首页·美食广场":
        st.header("🏠 美食广场")
        st.caption(random_saying())
        
        data = load_data()
        friends = get_friends(data, st.session_state.user_id)
        
        # 排序选项
        sort_by = st.radio(
            "排序方式",
            ["🕐 最新发布", "❤️ 点赞最多"],
            horizontal=True,
            index=0
        )
        
        st.markdown("### 🔍 筛选美食")
        col1, col2, col3, col4 = st.columns(4)
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
        with col3:
            filter_type = st.selectbox(
                "🍱 分类筛选",
                ["🍱 全部", "🍱 外卖吃啥", "🍽️ 奢侈一把"]
            )
        
        recommendations = data["recommendations"]
        
        # 排序
        if sort_by == "🕐 最新发布":
            recommendations_sorted = sorted(recommendations, key=lambda x: x.get("date", ""), reverse=True)
        else:  # 点赞最多
            recommendations_sorted = sorted(recommendations, key=lambda x: len(x.get("likes", [])), reverse=True)
        
        filtered_recs = []
        for rec in recommendations_sorted:
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
            if st.button("📝 我要记录美食！"):
                st.session_state.page = "📝 记录今日美食"
                st.rerun()
        else:
            st.markdown(f"🐯 找到 **{len(filtered_recs)}** 条美食推荐")
            st.markdown("---")
            
            for rec in filtered_recs:
                rec_user = get_user_by_id(data, rec["user_id"])
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
                
                type_icon = "🍱" if rec.get("food_type", "外卖吃啥") == "外卖吃啥" else "🍽️"
                type_text = rec.get("food_type", "外卖吃啥")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    **{user_label} 推荐**  {type_icon} {type_text}
                    
                    ## {rec['restaurant']}
                    **{rec['dish']}** · {'⭐' * rec['rating']} {rec['rating']}星 · 人均 ¥{rec.get('price', 0)}
                    
                    > 💬 {rec['reason']}
                    
                    📍 {rec['city']} {rec['district']} · 🏷️ {rec['tags']}
                    """)
                    
                    if "ate_with" in rec and rec["ate_with"]:
                        st.caption(f"👥 和 {rec['ate_with']} 一起吃")
                    
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
                
                # 点赞按钮
                like_count = len(rec.get("likes", []))
                liked = st.session_state.user_id in rec.get("likes", [])
                
                col_like, col_empty = st.columns([1, 5])
                with col_like:
                    button_label = f"❤️ {like_count}" if liked else f"🤍 {like_count}"
                    if st.button(button_label, key=f"like_{rec['id']}"):
                        data = load_data()
                        for r in data["recommendations"]:
                            if r["id"] == rec["id"]:
                                if "likes" not in r:
                                    r["likes"] = []
                                if st.session_state.user_id in r["likes"]:
                                    r["likes"].remove(st.session_state.user_id)
                                else:
                                    r["likes"].append(st.session_state.user_id)
                                break
                        save_data(data)
                        st.rerun()
                
                st.markdown("---")
                
                # 编辑删除按钮
                if is_my:
                    col1, col2, col3 = st.columns([1, 1, 3])
                    with col1:
                        if st.button("✏️ 编辑", key=f"edit_{rec['id']}"):
                            st.session_state.editing_rec = rec
                            st.rerun()
                    with col2:
                        if st.button("🗑️ 删除", key=f"delete_{rec['id']}"):
                            data = load_data()
                            data["recommendations"] = [r for r in data["recommendations"] if r["id"] != rec["id"]]
                            save_data(data)
                            st.success("删除成功！")
                            st.rerun()
                
                st.markdown("---")
        
        # 编辑弹窗
        if "editing_rec" in st.session_state:
            rec_to_edit = st.session_state.editing_rec
            
            with st.expander("✏️ 编辑美食日记", expanded=True):
                st.markdown(f"### 编辑：{rec_to_edit['restaurant']}")
                
                data = load_data()
                friends = get_friends(data, st.session_state.user_id)
                
                with st.form("edit_food_form"):
                    st.markdown("### 🍱 美食分类")
                    current_type = rec_to_edit.get("food_type", "外卖吃啥")
                    type_options = ["🍱 外卖吃啥", "🍽️ 奢侈一把"]
                    type_index = 0 if current_type == "外卖吃啥" else 1
                    edit_food_type = st.radio(
                        "选择类型",
                        type_options,
                        horizontal=True,
                        index=type_index
                    )
                    
                    st.markdown("### 👥 和谁一起吃？")
                    friend_names = [get_user_display_name(f) for f in friends]
                    current_ate_with = rec_to_edit.get("ate_with", "")
                    current_friends = [name.strip() for name in current_ate_with.split(",") if name.strip()] if current_ate_with else []
                    ate_with_options = ["🐯 独自一人"] + friend_names
                    ate_with = st.multiselect(
                        "选择和谁一起吃的",
                        ate_with_options,
                        default=current_friends,
                        help="记录和谁一起分享美食"
                    )
                    
                    st.markdown("### 📸 美食照片")
                    if rec_to_edit.get("image_path") and os.path.exists(rec_to_edit["image_path"]):
                        st.image(rec_to_edit["image_path"], width=150, caption="当前照片")
                        change_photo = st.checkbox("更换照片")
                    else:
                        change_photo = True
                    
                    new_photo = None
                    if change_photo:
                        new_photo = st.file_uploader(
                            "上传新照片（可选）",
                            type=["jpg", "jpeg", "png"],
                            key=f"edit_photo_{rec_to_edit['id']}"
                        )
                        if new_photo:
                            preview_img = Image.open(new_photo)
                            preview_img = ImageOps.exif_transpose(preview_img)
                            st.image(preview_img, width=150, caption="新照片预览")
                    
                    st.markdown("### 💬 美食评价")
                    new_reason = st.text_area(
                        "推荐理由",
                        value=rec_to_edit.get("reason", ""),
                        height=100,
                        key=f"edit_reason_{rec_to_edit['id']}"
                    )
                    new_rating = st.slider(
                        "评分",
                        1, 5, 
                        value=rec_to_edit.get("rating", 4),
                        key=f"edit_rating_{rec_to_edit['id']}"
                    )
                    new_tags = st.text_input(
                        "标签",
                        value=rec_to_edit.get("tags", ""),
                        key=f"edit_tags_{rec_to_edit['id']}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("💾 保存修改", use_container_width=True, type="primary")
                    with col2:
                        cancel_edit = st.form_submit_button("❌ 取消", use_container_width=True)
                    
                    if submit_edit:
                        data = load_data()
                        for rec in data["recommendations"]:
                            if rec["id"] == rec_to_edit["id"]:
                                if new_photo:
                                    image_path = save_image(new_photo, st.session_state.user_id, rec["restaurant"])
                                    rec["image_path"] = image_path
                                ate_with_str = ", ".join([a for a in ate_with if a != "🐯 独自一人"]) if ate_with else ""
                                rec["ate_with"] = ate_with_str
                                rec["reason"] = new_reason
                                rec["rating"] = new_rating
                                rec["tags"] = new_tags if new_tags else "美食"
                                rec["food_type"] = "外卖吃啥" if "外卖" in edit_food_type else "奢侈一把"
                                break
                        save_data(data)
                        st.success("✅ 美食日记更新成功！")
                        del st.session_state.editing_rec
                        st.rerun()
                    
                    if cancel_edit:
                        del st.session_state.editing_rec
                        st.rerun()
    
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
                rating = st.slider("⭐ 评分", 1, 5, 4)
            with col2:
                price = st.number_input("💰 人均价格（元）", min_value=0, max_value=9999, value=50, step=10, help="单位：元/人")
            
            st.markdown("### 🍱 美食分类")
            food_type = st.radio(
                "选择类型",
                ["🍱 外卖吃啥", "🍽️ 奢侈一把"],
                horizontal=True,
                help="外卖吃啥：日常点餐参考；奢侈一把：餐厅/探店分享"
            )
            
            st.markdown("### 👥 和谁一起吃？")
            friend_names = [get_user_display_name(f) for f in friends]
            ate_with_options = ["🐯 独自一人"] + friend_names
            ate_with = st.multiselect(
                "选择和谁一起吃的",
                ate_with_options,
                help="记录和谁一起分享美食"
            )
            
            st.markdown("### 💬 美食评价")
            reason = st.text_area("推荐理由*", placeholder="为什么推荐？有什么必点菜？", height=100)
            tags = st.text_input("🏷️ 标签", placeholder="例如：火锅,必点,隐藏菜单")
            
            st.markdown("### 📸 美食照片")
            uploaded_photo = st.file_uploader(
                "上传美食照片",
                type=["jpg", "jpeg", "png"]
            )
            if uploaded_photo:
                image = Image.open(uploaded_photo)
                image = ImageOps.exif_transpose(image)
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
                    
                    type_value = "外卖吃啥" if "外卖" in food_type else "奢侈一把"
                    
                    beijing_tz = ZoneInfo("Asia/Shanghai")
                    now_beijing = datetime.datetime.now(beijing_tz)
                    
                    new_rec = {
                        "id": len(data["recommendations"]) + 1,
                        "user_id": st.session_state.user_id,
                        "city": city,
                        "district": district or "未填写",
                        "restaurant": restaurant,
                        "dish": dish or "推荐菜品",
                        "rating": rating,
                        "price": price,
                        "reason": reason,
                        "tags": tags or "美食",
                        "date": now_beijing.strftime("%Y-%m-%d %H:%M"),
                        "image_path": image_path,
                        "ate_with": ate_with_str,
                        "food_type": type_value,
                        "likes": []
                    }
                    
                    data["recommendations"].append(new_rec)
                    save_data(data)
                    
                    st.success(random_saying())
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
        
        st.markdown("### 🔍 寻找新朋友")
        search_keyword = st.text_input("输入用户名或昵称搜索", placeholder="例如：小明")
        
        if search_keyword:
            results = search_users(data, search_keyword)
            if results:
                st.markdown("#### 搜索结果")
                for user in results:
                    with st.container():
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col1:
                            if user.get("avatar") and os.path.exists(user["avatar"]):
                                avatar_img = Image.open(user["avatar"])
                                st.image(avatar_img, width=50)
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
            target_user = get_user_by_id(data, target_id)
            if target_user:
                st.markdown("---")
                st.markdown(f"### 👤 {get_user_display_name(target_user)} 的主页")
                col1, col2 = st.columns([1, 3])
                with col1:
                    if target_user.get("avatar") and os.path.exists(target_user["avatar"]):
                        avatar_img = Image.open(target_user["avatar"])
                        st.image(avatar_img, width=100)
                    else:
                        st.markdown("## 🐯")
                with col2:
                    st.markdown(f"**{get_user_display_name(target_user)}**")
                    st.caption(f"@{target_user['username']}")
                    if target_user.get("bio"):
                        st.caption(target_user["bio"])
                
                user_recs = [r for r in data["recommendations"] if r["user_id"] == target_id]
                st.markdown(f"#### 📝 美食日记 ({len(user_recs)}篇)")
                if user_recs:
                    for rec in user_recs[-5:]:
                        st.markdown(f"""
                        **{rec['restaurant']}** · {rec['city']} {rec['district']}  
                        {'⭐' * rec['rating']} {rec['rating']}星 · 人均 ¥{rec.get('price', 0)}  
                        > {rec['reason']}
                        """)
                        if rec.get("image_path") and os.path.exists(rec["image_path"]):
                            st.image(rec["image_path"], width=150)
                        st.markdown("---")
                else:
                    st.info("该用户还没有发布美食日记")
                
                if target_id not in [f["id"] for f in friends] and target_id != st.session_state.user_id:
                    if st.button("➕ 添加为饭搭子", key=f"add_from_home_{target_id}"):
                        success, msg = add_friend(data, st.session_state.user_id, target_id)
                        if success:
                            st.success(msg)
                            del st.session_state.view_user_id
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    if target_id != st.session_state.user_id:
                        st.info("你们已经是饭搭子了")
                
                if st.button("← 返回好友列表"):
                    del st.session_state.view_user_id
                    st.rerun()
            else:
                st.error("用户不存在")
                del st.session_state.view_user_id
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📨 邀请朋友加入")
        st.info("🐯 把你的邀请码发给朋友，他们注册后就能成为你的饭搭子啦！")
        st.code(current_user["invite_code"])
        remaining = current_user.get("remaining_invites", 10)
        if current_user["id"] == 1:
            st.caption("✨ 小卷的邀请码无限制，可以邀请任意多位朋友！")
        else:
            st.caption(f"✨ 你还可以邀请 {remaining} 位朋友（每个朋友可邀请10人）")
    
    # ========== 个人中心 ==========
    elif page == "🐯 个人中心":
        st.header("🐯 个人中心")
        st.caption("这里藏着美食家的小秘密~")
        
        data = load_data()
        current_user = get_user_by_id(data, st.session_state.user_id)
        
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
        
        # 我赞过的美食（收藏夹）
        st.markdown("### ❤️ 我的收藏夹")
        st.caption("你点赞过的美食，随时查看想吃的好店～")
        
        liked_recs = []
        for rec in data["recommendations"]:
            if st.session_state.user_id in rec.get("likes", []):
                liked_recs.append(rec)
        
        if len(liked_recs) == 0:
            st.info("🐯 还没有收藏过美食，去首页给你喜欢的食物点个赞吧！")
        else:
            liked_recs_sorted = sorted(liked_recs, key=lambda x: x.get("date", ""), reverse=True)
            for rec in liked_recs_sorted:
                col_img, col_info = st.columns([1, 2])
                with col_img:
                    if rec.get("image_path") and os.path.exists(rec["image_path"]):
                        try:
                            img = Image.open(rec["image_path"])
                            st.image(img, use_container_width=True)
                        except:
                            st.markdown("📷 图片加载失败")
                    else:
                        type_icon = "🍱" if rec.get("food_type", "外卖吃啥") == "外卖吃啥" else "🍽️"
                        st.markdown(f"# {type_icon}")
                        st.caption("暂无图片")
                
                with col_info:
                    type_icon = "🍱" if rec.get("food_type", "外卖吃啥") == "外卖吃啥" else "🍽️"
                    st.markdown(f"""
                    **{rec['restaurant']}**  {type_icon}
                    
                    **{rec['dish']}** · {'⭐' * rec['rating']} {rec['rating']}星 · 人均 ¥{rec.get('price', 0)}
                    
                    > {rec['reason'][:100]}{'...' if len(rec['reason']) > 100 else ''}
                    
                    📍 {rec['city']} {rec['district']} · 🏷️ {rec['tags']}
                    """)
                    
                    if st.button("❤️ 取消收藏", key=f"unlike_{rec['id']}"):
                        data = load_data()
                        for r in data["recommendations"]:
                            if r["id"] == rec["id"]:
                                if st.session_state.user_id in r.get("likes", []):
                                    r["likes"].remove(st.session_state.user_id)
                                break
                        save_data(data)
                        st.rerun()
                
                st.markdown("---")
        
        st.markdown("---")
        
        # 编辑个人资料
        st.markdown("### 🐯 编辑我的小档案")
        col1, col2 = st.columns([1, 2])
        with col1:
            if current_user.get("avatar") and os.path.exists(current_user["avatar"]):
                avatar_img = Image.open(current_user["avatar"])
                st.image(avatar_img, width=100)
            else:
                st.markdown("## 🐯")
                st.caption("点击下方上传头像")
        
        with col2:
            st.markdown("**📸 上传新头像（自动裁剪为1:1正方形）**")
            new_avatar = st.file_uploader(
                "点击选择图片", 
                type=["jpg", "jpeg", "png"], 
                key="edit_avatar",
                label_visibility="collapsed"
            )
            if new_avatar:
                preview_img = Image.open(new_avatar)
                preview_img = ImageOps.exif_transpose(preview_img)
                st.image(preview_img, width=80)
                st.caption("预览（上传后自动裁剪为正方形）")
        
        new_nickname = st.text_input(
            "🍜 昵称", 
            value=current_user.get("nickname", current_user["username"]),
            key="edit_nickname"
        )
        new_bio = st.text_area(
            "📝 一句话介绍自己", 
            value=current_user.get("bio", ""),
            key="edit_bio",
            height=80
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            save_clicked = st.button("💾 保存小档案", use_container_width=True, type="primary")
        
        if save_clicked:
            data = load_data()
            current_user = get_user_by_id(data, st.session_state.user_id)
            
            if new_avatar:
                if current_user.get("avatar") and os.path.exists(current_user["avatar"]):
                    try:
                        os.remove(current_user["avatar"])
                    except:
                        pass
                avatar_path = save_avatar(new_avatar, st.session_state.user_id)
                current_user["avatar"] = avatar_path
            
            if new_nickname:
                current_user["nickname"] = new_nickname
            current_user["bio"] = new_bio
            
            save_data(data)
            st.success("🎉 小档案更新成功！")
            st.balloons()
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 📨 我的邀请码")
        st.code(current_user["invite_code"])
        remaining = current_user.get("remaining_invites", 10)
        if current_user["id"] == 1:
            st.caption("✨ 小卷的邀请码无限制，可以邀请任意多位朋友！")
        else:
            st.caption(f"✨ 你还可以邀请 {remaining} 位朋友（每个朋友可邀请10人）")
        
        st.markdown("---")
        
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
                        type_icon = "🍱" if rec.get("food_type", "外卖吃啥") == "外卖吃啥" else "🍽️"
                        like_count = len(rec.get("likes", []))
                        st.markdown(f"""
                        {type_icon} **{rec['restaurant']}** · {rec['city']} {rec['district']}
                        {'⭐' * rec['rating']} {rec['rating']}星 · 人均 ¥{rec.get('price', 0)} · ❤️ {like_count}
                        """)
                    with col2:
                        st.caption(f"📅 {rec.get('date', '未知')}")
                st.markdown("---")
