"""
移动端支持模块 - 创建跨平台移动应用
"""
import logging
import json
import threading
import queue
import socket
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64
import io

try:
    # 使用Kivy创建移动应用
    import kivy
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.popup import Popup
    from kivy.uix.image import Image
    from kivy.clock import Clock
    from kivy.core.window import Window
    KIVY_AVAILABLE = True
except ImportError:
    KIVY_AVAILABLE = False

try:
    # 使用Flask创建Web API
    from flask import Flask, request, jsonify, render_template_string
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from config.settings import settings

logger = logging.getLogger(__name__)

class MobileApp:
    """移动端应用系统"""
    
    def __init__(self, ai_brain=None, emotion_engine=None, knowledge_manager=None):
        self.ai_brain = ai_brain
        self.emotion_engine = emotion_engine
        self.knowledge_manager = knowledge_manager
        
        # 移动端配置
        self.mobile_config = {
            'interface_type': 'web',  # 'kivy', 'web', 'hybrid'
            'port': 8080,
            'host': '0.0.0.0',
            'enable_push_notifications': True,
            'offline_mode': True
        }
        
        # 连接管理
        self.connected_devices = {}
        self.message_queue = queue.Queue()
        
        # Web服务器
        self.flask_app = None
        self.socketio = None
        self.server_thread = None
        
        # Kivy应用
        self.kivy_app = None
        
        # 消息历史
        self.mobile_messages = []
        self.max_messages = 100
    
    def start_mobile_support(self, interface_type: str = 'web'):
        """启动移动端支持"""
        self.mobile_config['interface_type'] = interface_type
        
        try:
            if interface_type == 'web' and FLASK_AVAILABLE:
                self._start_web_interface()
            elif interface_type == 'kivy' and KIVY_AVAILABLE:
                self._start_kivy_interface()
            else:
                self._start_simple_web_interface()
            
            logger.info(f"移动端支持已启动: {interface_type}")
            
        except Exception as e:
            logger.error(f"启动移动端支持失败: {e}")
    
    def _start_web_interface(self):
        """启动Web界面"""
        self.flask_app = Flask(__name__)
        self.socketio = SocketIO(self.flask_app, cors_allowed_origins="*")
        
        # 注册路由
        self._register_web_routes()
        self._register_socket_events()
        
        # 启动服务器
        def run_server():
            self.socketio.run(
                self.flask_app,
                host=self.mobile_config['host'],
                port=self.mobile_config['port'],
                debug=False,
                allow_unsafe_werkzeug=True
            )
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # 显示访问信息
        local_ip = self._get_local_ip()
        port = self.mobile_config['port']
        logger.info(f"Web界面已启动:")
        logger.info(f"  本地访问: http://localhost:{port}")
        logger.info(f"  网络访问: http://{local_ip}:{port}")
        logger.info(f"  移动端可通过上述地址访问")
    
    def _register_web_routes(self):
        """注册Web路由"""
        
        @self.flask_app.route('/')
        def index():
            return self._get_mobile_html_template()
        
        @self.flask_app.route('/api/send_message', methods=['POST'])
        def send_message():
            try:
                data = request.get_json()
                message = data.get('message', '')
                
                if message and self.ai_brain:
                    # 处理用户消息
                    response = self._process_mobile_message(message)
                    
                    # 广播给所有连接的设备
                    self.socketio.emit('new_message', {
                        'type': 'ai_response',
                        'content': response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return jsonify({'success': True, 'response': response})
                
                return jsonify({'success': False, 'error': '消息为空'})
                
            except Exception as e:
                logger.error(f"处理移动端消息失败: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.flask_app.route('/api/status')
        def get_status():
            try:
                status = self._get_ai_status()
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.flask_app.route('/api/emotion/<emotion>')
        def trigger_emotion(emotion):
            try:
                if self.emotion_engine:
                    self.emotion_engine.process_trigger({
                        'type': emotion,
                        'intensity': 0.7,
                        'source': 'mobile_trigger'
                    })
                    return jsonify({'success': True, 'emotion': emotion})
                return jsonify({'success': False, 'error': '情绪引擎不可用'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def _register_socket_events(self):
        """注册Socket事件"""
        
        @self.socketio.on('connect')
        def handle_connect():
            device_id = request.sid
            self.connected_devices[device_id] = {
                'connect_time': datetime.now(),
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
            
            emit('connected', {
                'device_id': device_id,
                'ai_name': settings.personality.name,
                'welcome_message': f"你好！我是{settings.personality.name}，很高兴在移动端见到你！"
            })
            
            logger.info(f"移动设备连接: {device_id} ({request.remote_addr})")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            device_id = request.sid
            if device_id in self.connected_devices:
                del self.connected_devices[device_id]
            logger.info(f"移动设备断开: {device_id}")
        
        @self.socketio.on('user_message')
        def handle_user_message(data):
            try:
                message = data.get('message', '')
                device_id = request.sid
                
                if message:
                    # 记录消息
                    self._add_mobile_message('user', message, device_id)
                    
                    # 处理消息
                    response = self._process_mobile_message(message)
                    
                    # 发送回应
                    emit('ai_response', {
                        'content': response,
                        'timestamp': datetime.now().isoformat(),
                        'emotion': self.emotion_engine.get_current_emotion() if self.emotion_engine else None
                    })
                    
                    # 记录AI回应
                    self._add_mobile_message('ai', response, device_id)
                
            except Exception as e:
                logger.error(f"处理Socket消息失败: {e}")
                emit('error', {'message': '处理消息时出错'})
        
        @self.socketio.on('request_status')
        def handle_status_request():
            try:
                status = self._get_ai_status()
                emit('status_update', status)
            except Exception as e:
                emit('error', {'message': '获取状态失败'})
    
    def _start_kivy_interface(self):
        """启动Kivy移动应用"""
        if not KIVY_AVAILABLE:
            logger.error("Kivy未安装，无法创建移动应用")
            return
        
        class AILifeMobileApp(App):
            def __init__(self, mobile_app_instance, **kwargs):
                super().__init__(**kwargs)
                self.mobile_app = mobile_app_instance
            
            def build(self):
                return self.mobile_app._create_kivy_interface()
        
        self.kivy_app = AILifeMobileApp(self)
        
        # 在单独线程中运行Kivy
        def run_kivy():
            self.kivy_app.run()
        
        kivy_thread = threading.Thread(target=run_kivy, daemon=True)
        kivy_thread.start()
    
    def _create_kivy_interface(self):
        """创建Kivy界面"""
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = Label(
            text=f'🌟 {settings.personality.name} - 移动版',
            size_hint_y=None,
            height='48dp',
            font_size='20sp'
        )
        main_layout.add_widget(title)
        
        # 聊天区域
        chat_scroll = ScrollView()
        self.chat_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        chat_scroll.add_widget(self.chat_layout)
        main_layout.add_widget(chat_scroll)
        
        # 输入区域
        input_layout = BoxLayout(size_hint_y=None, height='48dp', spacing=10)
        
        self.message_input = TextInput(
            multiline=False,
            hint_text='输入消息...',
            size_hint_x=0.8
        )
        self.message_input.bind(on_text_validate=self._kivy_send_message)
        
        send_button = Button(
            text='发送',
            size_hint_x=0.2
        )
        send_button.bind(on_press=self._kivy_send_message)
        
        input_layout.add_widget(self.message_input)
        input_layout.add_widget(send_button)
        main_layout.add_widget(input_layout)
        
        # 功能按钮
        button_layout = BoxLayout(size_hint_y=None, height='48dp', spacing=5)
        
        emotions = [('😊', 'joy'), ('😢', 'sadness'), ('🎉', 'excitement'), ('🤔', 'curiosity')]
        for emoji, emotion in emotions:
            btn = Button(text=emoji)
            btn.bind(on_press=lambda x, e=emotion: self._kivy_trigger_emotion(e))
            button_layout.add_widget(btn)
        
        main_layout.add_widget(button_layout)
        
        # 添加欢迎消息
        self._add_kivy_message('AI', f'你好！我是{settings.personality.name}！')
        
        return main_layout
    
    def _kivy_send_message(self, instance):
        """Kivy发送消息"""
        message = self.message_input.text.strip()
        if message:
            self._add_kivy_message('你', message)
            self.message_input.text = ''
            
            # 处理消息
            response = self._process_mobile_message(message)
            Clock.schedule_once(lambda dt: self._add_kivy_message('AI', response), 0.5)
    
    def _kivy_trigger_emotion(self, emotion):
        """Kivy触发情绪"""
        if self.emotion_engine:
            self.emotion_engine.process_trigger({
                'type': emotion,
                'intensity': 0.7,
                'source': 'mobile_trigger'
            })
            self._add_kivy_message('系统', f'触发情绪: {emotion}')
    
    def _add_kivy_message(self, sender, message):
        """添加Kivy消息"""
        msg_label = Label(
            text=f'[{sender}] {message}',
            text_size=(None, None),
            halign='left',
            size_hint_y=None
        )
        msg_label.bind(texture_size=msg_label.setter('size'))
        self.chat_layout.add_widget(msg_label)
    
    def _start_simple_web_interface(self):
        """启动简单Web界面（无依赖）"""
        import http.server
        import socketserver
        from urllib.parse import parse_qs
        
        class SimpleHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = self._get_simple_html()
                    self.wfile.write(html.encode('utf-8'))
                else:
                    self.send_error(404)
            
            def do_POST(self):
                if self.path == '/send':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = parse_qs(post_data.decode('utf-8'))
                    
                    message = data.get('message', [''])[0]
                    response = self._process_mobile_message(message)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    result = json.dumps({'response': response}, ensure_ascii=False)
                    self.wfile.write(result.encode('utf-8'))
        
        # 启动简单服务器
        def run_simple_server():
            with socketserver.TCPServer(("", 8080), SimpleHandler) as httpd:
                httpd.serve_forever()
        
        server_thread = threading.Thread(target=run_simple_server, daemon=True)
        server_thread.start()
    
    def _process_mobile_message(self, message: str) -> str:
        """处理移动端消息"""
        try:
            if self.ai_brain:
                # 触发情绪
                if self.emotion_engine:
                    self.emotion_engine.process_trigger({
                        'type': 'joy',
                        'intensity': 0.5,
                        'source': 'mobile_interaction'
                    })
                
                # 生成回应
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                context = {
                    'user_interaction': True,
                    'platform': 'mobile',
                    'current_emotion': self.emotion_engine.get_current_emotion() if self.emotion_engine else None
                }
                
                response = loop.run_until_complete(self.ai_brain.think(message, context))
                loop.close()
                
                return response
            else:
                return "很抱歉，AI大脑暂时不可用。但我还在这里陪着你！"
                
        except Exception as e:
            logger.error(f"处理移动端消息失败: {e}")
            return "哎呀，我的脑袋有点转不过来了... 😵"
    
    def _get_ai_status(self) -> Dict[str, Any]:
        """获取AI状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'connected_devices': len(self.connected_devices),
            'ai_name': settings.personality.name
        }
        
        if self.emotion_engine:
            status['emotion'] = self.emotion_engine.get_current_emotion()
        
        if self.ai_brain:
            status['ai_state'] = self.ai_brain.get_current_state()
        
        return status
    
    def _add_mobile_message(self, sender: str, content: str, device_id: str = ''):
        """添加移动端消息记录"""
        message = {
            'sender': sender,
            'content': content,
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.mobile_messages.append(message)
        
        # 保持消息数量限制
        if len(self.mobile_messages) > self.max_messages:
            self.mobile_messages = self.mobile_messages[-self.max_messages:]
    
    def _get_local_ip(self) -> str:
        """获取本地IP地址"""
        try:
            # 创建一个socket连接来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    def _get_mobile_html_template(self) -> str:
        """获取移动端HTML模板"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌟 ''' + settings.personality.name + ''' - 移动版</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh; display: flex; flex-direction: column;
        }
        .header { 
            background: rgba(255,255,255,0.1); padding: 15px; text-align: center; 
            color: white; font-size: 18px; font-weight: bold;
        }
        .chat-container { 
            flex: 1; overflow-y: auto; padding: 10px; 
            background: rgba(255,255,255,0.05);
        }
        .message { 
            margin: 8px 0; padding: 10px 15px; border-radius: 18px; 
            max-width: 80%; word-wrap: break-word;
        }
        .user-message { 
            background: #007AFF; color: white; margin-left: auto; 
            border-bottom-right-radius: 5px;
        }
        .ai-message { 
            background: rgba(255,255,255,0.9); color: #333; 
            border-bottom-left-radius: 5px;
        }
        .input-area { 
            background: rgba(255,255,255,0.1); padding: 15px; 
            display: flex; gap: 10px;
        }
        .message-input { 
            flex: 1; padding: 12px; border: none; border-radius: 20px; 
            font-size: 16px; outline: none;
        }
        .send-btn { 
            background: #007AFF; color: white; border: none; 
            border-radius: 20px; padding: 12px 20px; font-size: 16px;
        }
        .emotion-bar { 
            display: flex; justify-content: space-around; padding: 10px;
            background: rgba(255,255,255,0.1);
        }
        .emotion-btn { 
            background: none; border: none; font-size: 24px; 
            padding: 8px; border-radius: 50%;
        }
        .status-bar { 
            padding: 5px 15px; background: rgba(0,0,0,0.3); 
            color: white; font-size: 12px; text-align: center;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div class="header">🌟 ''' + settings.personality.name + ''' - 移动版</div>
    <div class="status-bar" id="status">连接中...</div>
    
    <div class="emotion-bar">
        <button class="emotion-btn" onclick="triggerEmotion('joy')">😊</button>
        <button class="emotion-btn" onclick="triggerEmotion('sadness')">😢</button>
        <button class="emotion-btn" onclick="triggerEmotion('excitement')">🎉</button>
        <button class="emotion-btn" onclick="triggerEmotion('curiosity')">🤔</button>
    </div>
    
    <div class="chat-container" id="chatContainer"></div>
    
    <div class="input-area">
        <input type="text" class="message-input" id="messageInput" 
               placeholder="输入消息..." onkeypress="checkEnter(event)">
        <button class="send-btn" onclick="sendMessage()">发送</button>
    </div>

    <script>
        const socket = io();
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const statusBar = document.getElementById('status');

        socket.on('connected', function(data) {
            statusBar.textContent = '已连接 - ' + data.ai_name;
            addMessage('ai', data.welcome_message);
        });

        socket.on('ai_response', function(data) {
            addMessage('ai', data.content);
        });

        socket.on('status_update', function(data) {
            if (data.emotion) {
                statusBar.textContent = '情绪: ' + data.emotion.emotion + ' | 设备: ' + data.connected_devices;
            }
        });

        function addMessage(sender, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + (sender === 'user' ? 'user-message' : 'ai-message');
            messageDiv.textContent = content;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function sendMessage() {
            const message = messageInput.value.trim();
            if (message) {
                addMessage('user', message);
                socket.emit('user_message', { message: message });
                messageInput.value = '';
            }
        }

        function checkEnter(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function triggerEmotion(emotion) {
            fetch('/api/emotion/' + emotion)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusBar.textContent = '触发情绪: ' + emotion;
                    }
                });
        }

        // 定期更新状态
        setInterval(() => {
            socket.emit('request_status');
        }, 5000);
    </script>
</body>
</html>
        '''
    
    def broadcast_to_mobile(self, message_type: str, content: Any):
        """向所有移动设备广播消息"""
        if self.socketio:
            self.socketio.emit('broadcast_message', {
                'type': message_type,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
    
    def send_push_notification(self, title: str, message: str):
        """发送推送通知（模拟）"""
        # 这里可以集成Firebase Cloud Messaging或其他推送服务
        notification = {
            'title': title,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"推送通知: {title} - {message}")
        
        # 广播给所有连接的设备
        self.broadcast_to_mobile('notification', notification)
    
    def get_mobile_stats(self) -> Dict[str, Any]:
        """获取移动端统计信息"""
        return {
            'connected_devices': len(self.connected_devices),
            'total_messages': len(self.mobile_messages),
            'interface_type': self.mobile_config['interface_type'],
            'server_running': self.server_thread is not None and self.server_thread.is_alive(),
            'supported_interfaces': {
                'web': FLASK_AVAILABLE,
                'kivy': KIVY_AVAILABLE,
                'simple': True
            }
        }
    
    def shutdown(self):
        """关闭移动端支持"""
        # 关闭Socket连接
        if self.socketio:
            self.socketio.stop()
        
        # 等待服务器线程结束
        if self.server_thread and self.server_thread.is_alive():
            # 由于Flask服务器难以优雅关闭，这里只记录日志
            logger.info("移动端服务器正在关闭...")
        
        logger.info("移动端支持已关闭")

# 全局移动端实例
mobile_app = None

def create_mobile_app(ai_brain=None, emotion_engine=None, knowledge_manager=None):
    """创建移动端应用实例"""
    global mobile_app
    mobile_app = MobileApp(ai_brain, emotion_engine, knowledge_manager)
    return mobile_app