import requests
import random
import string
import time
import json
import uuid
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# 更详细的CORS配置，支持开发环境
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8081", "http://localhost:3000", "http://localhost:19006"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SPUG_URL = os.getenv("SPUG_URL")

# 开发模式 - 如果没有配置真实的Supabase，使用模拟模式
DEVELOPMENT_MODE = not SUPABASE_URL or SUPABASE_URL == "your_supabase_project_url" or not SUPABASE_KEY or "example" in SUPABASE_URL.lower()

# 强制开发模式用于测试（可以通过环境变量覆盖）
if os.getenv("FORCE_DEV_MODE", "false").lower() == "true":
    DEVELOPMENT_MODE = True
    print("🔧 强制开发模式已启用")

if DEVELOPMENT_MODE:
    print("⚠️  开发模式：未配置真实的Supabase，将使用模拟数据")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

# 开发模式的内存存储
dev_verification_codes = {}
dev_users = {}
dev_invite_codes = {'1234': True, 'WELCOME': True, 'LANDE': True, 'OMNILAZE': True, 'ADVX2025': True}  # 有效的邀请码
# 开发模式订单存储
dev_orders = {}

def store_verification_code(phone_number, code):
    if DEVELOPMENT_MODE:
        # 开发模式：存储到内存
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        dev_verification_codes[phone_number] = {
            'code': code,
            'expires_at': expires_at,
            'used': False,
            'created_at': datetime.now(timezone.utc)
        }
        return {"success": True}
    else:
        # 生产模式：存储到Supabase
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        result = supabase.table('verification_codes').upsert({
            'phone_number': phone_number,
            'code': code,
            'expires_at': expires_at.isoformat(),
            'used': False
        }).execute()
        
        return result

def send_verification_code(phone_number):
    code = generate_verification_code()
    
    store_result = store_verification_code(phone_number, code)
    
    if DEVELOPMENT_MODE:
        # 开发模式：模拟发送成功，并在控制台显示验证码
        print(f"📱 开发模式 - 验证码已生成: {phone_number} -> {code}")
        return {"success": True, "message": "验证码发送成功（开发模式）", "dev_code": code}
    else:
        # 生产模式：真实发送短信
        body = {'name': '验证码', 'code': code, 'targets': phone_number}
        response = requests.post(SPUG_URL, json=body)
        
        if response.status_code == 200:
            return {"success": True, "message": "验证码发送成功"}
        else:
            return {"success": False, "message": "验证码发送失败"}

def verify_code(phone_number, input_code):
    if DEVELOPMENT_MODE:
        # 开发模式：从内存验证
        if phone_number not in dev_verification_codes:
            return {"success": False, "message": "验证码不存在或已使用"}
        
        code_record = dev_verification_codes[phone_number]
        
        if code_record['used']:
            return {"success": False, "message": "验证码不存在或已使用"}
        
        # 检查是否过期
        if datetime.now(timezone.utc) > code_record['expires_at']:
            return {"success": False, "message": "验证码已过期"}
        
        # 验证验证码
        if code_record['code'] != input_code:
            return {"success": False, "message": "验证码错误"}
        
        # 标记为已使用
        code_record['used'] = True
        return {"success": True, "message": "验证码验证成功"}
    else:
        # 生产模式：从Supabase验证
        result = supabase.table('verification_codes').select('*').eq('phone_number', phone_number).eq('used', False).order('created_at', desc=True).limit(1).execute()
        
        if not result.data:
            return {"success": False, "message": "验证码不存在或已使用"}
        
        code_record = result.data[0]
        expires_at_str = code_record['expires_at']
        if expires_at_str.endswith('+00:00'):
            expires_at_str = expires_at_str.replace('+00:00', 'Z')
        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
        
        if datetime.now(timezone.utc) > expires_at:
            return {"success": False, "message": "验证码已过期"}
        
        if code_record['code'] != input_code:
            return {"success": False, "message": "验证码错误"}
        
        # 标记验证码为已使用
        supabase.table('verification_codes').update({'used': True}).eq('id', code_record['id']).execute()
        
        return {"success": True, "message": "验证码验证成功"}

def login_with_phone(phone_number, verification_code):
    print(f"🔐 开始登录验证: {phone_number}")
    verify_result = verify_code(phone_number, verification_code)
    
    if not verify_result["success"]:
        print(f"❌ 验证码验证失败: {verify_result['message']}")
        return verify_result
    
    print(f"✅ 验证码验证成功: {phone_number}")
    is_new_user = False
    
    if DEVELOPMENT_MODE:
        # 开发模式：使用内存存储用户
        print(f"📝 当前用户列表: {list(dev_users.keys())}")
        if phone_number not in dev_users:
            # 新用户，但暂不创建，等待邀请码验证
            is_new_user = True
            user_id = f"dev_user_{len(dev_users) + 1}"
            print(f"🆕 检测到新用户: {phone_number}")
        else:
            user_id = dev_users[phone_number]['id']
            print(f"👤 老用户登录: {phone_number} (ID: {user_id})")
        
        print(f"✅ 开发模式 - 用户验证成功: {phone_number} (新用户: {is_new_user})")
    else:
        # 生产模式：使用Supabase
        user_result = supabase.table('users').select('*').eq('phone_number', phone_number).execute()
        
        if not user_result.data:
            # 新用户，但暂不创建，等待邀请码验证
            is_new_user = True
            user_id = f"temp_user_{phone_number}"  # 临时ID
            print(f"🆕 检测到新用户: {phone_number}")
        else:
            user_id = user_result.data[0]['id']
            print(f"👤 老用户登录: {phone_number} (ID: {user_id})")
    
    result = {
        "success": True,
        "message": "验证成功" if not is_new_user else "新用户验证成功，请输入邀请码",
        "user_id": user_id if not is_new_user else None,
        "phone_number": phone_number,
        "is_new_user": is_new_user
    }
    
    print(f"📤 返回结果: {result}")
    return result

# Flask API路由

@app.route('/send-verification-code', methods=['POST'])
def api_send_verification_code():
    """发送验证码API"""
    print(f"📱 收到发送验证码请求 - Origin: {request.headers.get('Origin', 'Unknown')}")
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        print(f"📱 手机号: {phone_number}")
        
        if not phone_number:
            return jsonify({"success": False, "message": "手机号不能为空"}), 400
        
        # 验证手机号格式
        if len(phone_number) != 11 or not phone_number.isdigit():
            return jsonify({"success": False, "message": "请输入正确的11位手机号码"}), 400
        
        result = send_verification_code(phone_number)
        
        if result["success"]:
            print(f"✅ 验证码发送成功: {phone_number}")
            return jsonify(result), 200
        else:
            print(f"❌ 验证码发送失败: {result['message']}")
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ 服务器错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

@app.route('/login-with-phone', methods=['POST'])
def api_login_with_phone():
    """验证码登录API"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        verification_code = data.get('verification_code')
        
        if not phone_number or not verification_code:
            return jsonify({"success": False, "message": "手机号和验证码不能为空"}), 400
        
        # 验证手机号格式
        if len(phone_number) != 11 or not phone_number.isdigit():
            return jsonify({"success": False, "message": "请输入正确的11位手机号码"}), 400
        
        # 验证验证码格式
        if len(verification_code) != 6 or not verification_code.isdigit():
            return jsonify({"success": False, "message": "请输入6位数字验证码"}), 400
        
        result = login_with_phone(phone_number, verification_code)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

def verify_invite_code_and_create_user(phone_number, invite_code):
    """验证邀请码并创建新用户"""
    print(f"🔑 验证邀请码: {phone_number} -> {invite_code}")
    
    if DEVELOPMENT_MODE:
        # 开发模式：检查内存中的邀请码
        print(f"📝 可用邀请码: {list(dev_invite_codes.keys())}")
        if invite_code not in dev_invite_codes:
            print(f"❌ 邀请码无效: {invite_code}")
            return {"success": False, "message": "邀请码无效"}
        
        # 创建新用户
        user_id = f"dev_user_{len(dev_users) + 1}"
        dev_users[phone_number] = {
            'id': user_id,
            'phone_number': phone_number,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'invite_code': invite_code
        }
        
        print(f"✅ 开发模式 - 新用户创建成功: {phone_number} (ID: {user_id})")
        return {
            "success": True,
            "message": "新用户注册成功",
            "user_id": user_id,
            "phone_number": phone_number
        }
    else:
        # 生产模式：从Supabase验证邀请码
        invite_result = supabase.table('invite_codes').select('*').eq('code', invite_code).eq('used', False).execute()
        
        if not invite_result.data:
            return {"success": False, "message": "邀请码无效或已使用"}
        
        try:
            # 创建新用户
            new_user = supabase.table('users').insert({
                'phone_number': phone_number,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'invite_code': invite_code
            }).execute()
            
            # 标记邀请码为已使用
            supabase.table('invite_codes').update({'used': True, 'used_by': phone_number}).eq('code', invite_code).execute()
            
            return {
                "success": True,
                "message": "新用户注册成功",
                "user_id": new_user.data[0]['id'],
                "phone_number": phone_number
            }
        except Exception as e:
            return {"success": False, "message": f"用户创建失败: {str(e)}"}

def generate_order_number():
    """生成订单号"""
    today = datetime.now().strftime('%Y%m%d')
    if DEVELOPMENT_MODE:
        # 开发模式：简单计数
        daily_count = len([o for o in dev_orders.values() if o['order_date'] == datetime.now().date().isoformat()]) + 1
    else:
        # 生产模式：使用数据库函数
        return None  # 让数据库触发器自动生成
    
    return f"ORD{today}{daily_count:03d}"

def create_order(user_id, phone_number, form_data):
    """创建订单"""
    print(f"📋 创建订单: 用户 {user_id}")
    
    order_number = generate_order_number()
    current_time = datetime.now(timezone.utc)
    
    order_data = {
        'order_number': order_number,
        'user_id': user_id,
        'phone_number': phone_number,
        'status': 'draft',
        'order_date': current_time.date().isoformat(),
        'created_at': current_time.isoformat(),
        'delivery_address': form_data.get('address', ''),
        'dietary_restrictions': json.dumps(form_data.get('allergies', []), ensure_ascii=False),
        'food_preferences': json.dumps(form_data.get('preferences', []), ensure_ascii=False),
        'budget_amount': float(form_data.get('budget', 0)),
        'budget_currency': 'CNY',
        'is_deleted': False
    }
    
    if DEVELOPMENT_MODE:
        # 开发模式：存储到内存
        order_id = str(uuid.uuid4())
        order_data['id'] = order_id
        dev_orders[order_id] = order_data
        
        print(f"✅ 开发模式 - 订单创建成功: {order_number}")
        return {
            "success": True,
            "message": "订单创建成功",
            "order_id": order_id,
            "order_number": order_number
        }
    else:
        # 生产模式：存储到Supabase
        try:
            result = supabase.table('orders').insert(order_data).execute()
            order_id = result.data[0]['id']
            actual_order_number = result.data[0]['order_number']
            
            print(f"✅ 生产模式 - 订单创建成功: {actual_order_number}")
            return {
                "success": True,
                "message": "订单创建成功",
                "order_id": order_id,
                "order_number": actual_order_number
            }
        except Exception as e:
            print(f"❌ 订单创建失败: {str(e)}")
            return {"success": False, "message": f"订单创建失败: {str(e)}"}

def submit_order(order_id):
    """提交订单"""
    print(f"📤 提交订单: {order_id}")
    
    if DEVELOPMENT_MODE:
        # 开发模式
        if order_id not in dev_orders:
            return {"success": False, "message": "订单不存在"}
        
        dev_orders[order_id]['status'] = 'submitted'
        dev_orders[order_id]['submitted_at'] = datetime.now(timezone.utc).isoformat()
        dev_orders[order_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        print(f"✅ 开发模式 - 订单提交成功: {dev_orders[order_id]['order_number']}")
        return {
            "success": True,
            "message": "订单提交成功",
            "order_number": dev_orders[order_id]['order_number']
        }
    else:
        # 生产模式
        try:
            result = supabase.table('orders').update({
                'status': 'submitted',
                'submitted_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', order_id).execute()
            
            if not result.data:
                return {"success": False, "message": "订单不存在"}
            
            print(f"✅ 生产模式 - 订单提交成功: {result.data[0]['order_number']}")
            return {
                "success": True,
                "message": "订单提交成功",
                "order_number": result.data[0]['order_number']
            }
        except Exception as e:
            print(f"❌ 订单提交失败: {str(e)}")
            return {"success": False, "message": f"订单提交失败: {str(e)}"}

def update_order_feedback(order_id, rating, feedback):
    """更新订单反馈"""
    print(f"⭐ 更新订单反馈: {order_id} - 评分: {rating}")
    
    if rating < 1 or rating > 5:
        return {"success": False, "message": "评分必须在1-5之间"}
    
    feedback_data = {
        'user_rating': rating,
        'user_feedback': feedback,
        'feedback_submitted_at': datetime.now(timezone.utc).isoformat()
    }
    
    if DEVELOPMENT_MODE:
        # 开发模式
        if order_id not in dev_orders:
            return {"success": False, "message": "订单不存在"}
        
        dev_orders[order_id].update(feedback_data)
        dev_orders[order_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        print(f"✅ 开发模式 - 反馈更新成功")
        return {"success": True, "message": "反馈提交成功"}
    else:
        # 生产模式
        try:
            result = supabase.table('orders').update(feedback_data).eq('id', order_id).execute()
            
            if not result.data:
                return {"success": False, "message": "订单不存在"}
            
            print(f"✅ 生产模式 - 反馈更新成功")
            return {"success": True, "message": "反馈提交成功"}
        except Exception as e:
            print(f"❌ 反馈更新失败: {str(e)}")
            return {"success": False, "message": f"反馈提交失败: {str(e)}"}

@app.route('/create-order', methods=['POST'])
def api_create_order():
    """创建订单API"""
    print(f"📋 收到创建订单请求")
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        phone_number = data.get('phone_number')
        form_data = data.get('form_data', {})
        
        print(f"📋 订单数据: 用户{user_id}, 地址{form_data.get('address', '')[:20]}...")
        
        if not user_id or not phone_number:
            return jsonify({"success": False, "message": "用户信息不能为空"}), 400
        
        if not form_data.get('address'):
            return jsonify({"success": False, "message": "配送地址不能为空"}), 400
        
        if not form_data.get('budget') or float(form_data.get('budget', 0)) <= 0:
            return jsonify({"success": False, "message": "预算金额无效"}), 400
        
        result = create_order(user_id, phone_number, form_data)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ 创建订单API错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

@app.route('/submit-order', methods=['POST'])
def api_submit_order():
    """提交订单API"""
    print(f"📤 收到提交订单请求")
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        print(f"📤 提交订单: {order_id}")
        
        if not order_id:
            return jsonify({"success": False, "message": "订单ID不能为空"}), 400
        
        result = submit_order(order_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ 提交订单API错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

@app.route('/order-feedback', methods=['POST'])
def api_order_feedback():
    """订单反馈API"""
    print(f"⭐ 收到订单反馈请求")
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        rating = data.get('rating')
        feedback = data.get('feedback', '')
        
        print(f"⭐ 订单反馈: {order_id} - 评分: {rating}")
        
        if not order_id:
            return jsonify({"success": False, "message": "订单ID不能为空"}), 400
        
        if not rating or not isinstance(rating, int):
            return jsonify({"success": False, "message": "评分不能为空且必须为整数"}), 400
        
        result = update_order_feedback(order_id, rating, feedback)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ 订单反馈API错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

@app.route('/orders/<user_id>', methods=['GET'])
def api_get_user_orders(user_id):
    """获取用户订单列表API"""
    print(f"📋 获取用户订单: {user_id}")
    try:
        if DEVELOPMENT_MODE:
            # 开发模式：从内存获取
            user_orders = [order for order in dev_orders.values() 
                          if order['user_id'] == user_id and not order.get('is_deleted', False)]
            user_orders.sort(key=lambda x: x['created_at'], reverse=True)
        else:
            # 生产模式：从Supabase获取
            result = supabase.table('orders').select('*').eq('user_id', user_id).eq('is_deleted', False).order('created_at', desc=True).execute()
            user_orders = result.data
        
        print(f"📋 找到 {len(user_orders)} 个订单")
        return jsonify({
            "success": True,
            "orders": user_orders,
            "count": len(user_orders)
        }), 200
        
    except Exception as e:
        print(f"❌ 获取订单API错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

@app.route('/verify-invite-code', methods=['POST'])
def api_verify_invite_code():
    """验证邀请码并创建新用户API"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        invite_code = data.get('invite_code')
        
        if not phone_number or not invite_code:
            return jsonify({"success": False, "message": "手机号和邀请码不能为空"}), 400
        
        # 验证手机号格式
        if len(phone_number) != 11 or not phone_number.isdigit():
            return jsonify({"success": False, "message": "请输入正确的11位手机号码"}), 400
        
        result = verify_invite_code_and_create_user(phone_number, invite_code)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查API"""
    return jsonify({
        "status": "healthy", 
        "message": "API服务正常运行",
        "cors_origins": ["http://localhost:8081", "http://localhost:3000", "http://localhost:19006"],
        "development_mode": DEVELOPMENT_MODE
    }), 200

if __name__ == '__main__':
    print("=== 手机验证码登录API服务 ===")
    print(f"🔧 开发模式: {DEVELOPMENT_MODE}")
    print("🌐 CORS已配置，支持以下源：")
    print("   - http://localhost:8081 (Expo开发服务器)")
    print("   - http://localhost:3000 (React开发服务器)")
    print("   - http://localhost:19006 (Expo Web)")
    print("📡 API服务启动中...")
    print("🔗 测试连接: http://localhost:5001/health")
    app.run(host='0.0.0.0', port=5001, debug=True)  # 改为5001端口