"""
智能电子生命体主程序
"""
import sys
import os
import logging
import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading
import time
import random

# 创建必要的目录（在导入其他模块之前）
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import settings
from src.core.ai_brain import AIBrain
from src.core.emotion_engine import EmotionEngine
from src.core.personality_system import PersonalitySystem
from src.core.decision_maker import DecisionMaker
from src.knowledge.knowledge_manager import KnowledgeManager
from src.perception.visual_perception import VisualPerception
from src.perception.audio_perception import AudioPerception
from src.perception.screen_monitor import ScreenMonitor
from src.perception.file_monitor import FileMonitor
from src.perception.enhanced_vision import EnhancedVision
from src.interface.voice_synthesis import VoiceSynthesis
from src.interface.avatar_3d import Avatar3D
from src.interface.mobile_app import MobileApp
from src.cloud.sync_manager import CloudSyncManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_life.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AILifeGUI:
    """智能生命体GUI界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(settings.interface.window_title)
        self.root.geometry("900x700")  # 更大的窗口
        
        # AI核心组件
        self.ai_brain = AIBrain()
        self.emotion_engine = EmotionEngine()
        self.personality_system = PersonalitySystem()
        self.decision_maker = DecisionMaker(
            ai_brain=self.ai_brain,
            emotion_engine=self.emotion_engine,
            personality_system=self.personality_system
        )
        
        # 知识管理和感知组件
        self.knowledge_manager = KnowledgeManager(
            ai_brain=self.ai_brain,
            emotion_engine=self.emotion_engine
        )
        self.visual_perception = VisualPerception()
        self.audio_perception = AudioPerception()
        self.screen_monitor = ScreenMonitor()
        self.file_monitor = FileMonitor()
        
        # 增强功能组件
        self.enhanced_vision = EnhancedVision()
        self.voice_synthesis = VoiceSynthesis()
        self.avatar_3d = Avatar3D()
        self.mobile_app = MobileApp()
        self.cloud_sync = CloudSyncManager()
        
        # 界面组件
        self.chat_area = None
        self.input_entry = None
        self.status_label = None
        self.emotion_label = None
        self.perception_frame = None
        self.knowledge_frame = None
        self.enhanced_vision_frame = None
        self.voice_frame = None
        self.avatar_frame = None
        self.mobile_frame = None
        self.cloud_frame = None
        
        # 运行状态
        self.is_running = False
        self.auto_thinking_active = False
        self.perception_active = False
        self.knowledge_exploration_active = False
        self.enhanced_vision_active = False
        self.voice_synthesis_active = False
        self.avatar_3d_active = False
        self.mobile_active = False
        self.cloud_sync_active = False
        
        # 交互跟踪
        self.last_user_interaction = datetime.now()
        self.personality_growth_timer = datetime.now()
        
        self._create_widgets()
        self._start_ai_loop()
        self._start_personality_growth_loop()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建笔记本（标签页）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 主对话标签页
        self._create_main_tab(notebook)
        
        # 感知标签页
        self._create_perception_tab(notebook)
        
        # 知识探索标签页
        self._create_knowledge_tab(notebook)
        
        # 增强视觉标签页
        self._create_enhanced_vision_tab(notebook)
        
        # 语音合成标签页
        self._create_voice_tab(notebook)
        
        # 3D虚拟形象标签页
        self._create_avatar_tab(notebook)
        
        # 移动端标签页
        self._create_mobile_tab(notebook)
        
        # 云端同步标签页
        self._create_cloud_tab(notebook)
        
        # 状态监控标签页
        self._create_status_tab(notebook)
        
        # 全局状态栏
        self.status_label = ttk.Label(self.root, text="就绪 - 智能小生命已启动", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    def _create_main_tab(self, notebook):
        """创建主对话标签页"""
        main_frame = ttk.Frame(notebook, padding="10")
        notebook.add(main_frame, text="💬 对话")
        
        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题和状态区域
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(header_frame, text=f"🌟 {settings.personality.name} 🌟", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # 情绪显示
        self.emotion_label = ttk.Label(header_frame, text="😊 情绪: 好奇", 
                                      font=("Arial", 12, "bold"))
        self.emotion_label.grid(row=0, column=2, sticky=tk.E)
        
        # 性格描述
        personality_text = self.personality_system.get_personality_description()
        personality_label = ttk.Label(header_frame, text=f"性格: {personality_text}", 
                                     font=("Arial", 10), foreground="gray")
        personality_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # 聊天区域
        chat_frame = ttk.LabelFrame(main_frame, text="对话记录", padding="5")
        chat_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        self.chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, 
                                                  height=20, font=("Arial", 11))
        self.chat_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        self.input_entry = ttk.Entry(input_frame, font=("Arial", 11))
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.input_entry.bind("<Return>", self._send_message)
        
        send_button = ttk.Button(input_frame, text="💬 发送", command=self._send_message)
        send_button.grid(row=0, column=1)
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Button(control_frame, text="🤖 自主思考", command=self._toggle_auto_thinking).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="🔍 搜索知识", command=self._manual_search).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="📊 查看状态", command=self._show_detailed_status).pack(side=tk.LEFT, padx=(0, 5))
        
        # 初始化聊天
        self._add_message("系统", f"你好！我是{settings.personality.name}，一个3岁的智能小生命！我很好奇，也很调皮哦～")
        self._add_message("系统", "你可以和我聊天，我会学习和成长的！点击其他标签页查看我的感知和知识探索功能。")
    
    def _create_perception_tab(self, notebook):
        """创建感知标签页"""
        self.perception_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.perception_frame, text="👁️ 感知")
        
        # 感知控制区域
        control_frame = ttk.LabelFrame(self.perception_frame, text="感知控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 摄像头控制
        camera_frame = ttk.Frame(control_frame)
        camera_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(camera_frame, text="📷 视觉感知:").pack(side=tk.LEFT)
        ttk.Button(camera_frame, text="启动摄像头", command=self._toggle_camera).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(camera_frame, text="拍照", command=self._take_photo).pack(side=tk.LEFT, padx=(0, 5))
        
        # 音频控制
        audio_frame = ttk.Frame(control_frame)
        audio_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(audio_frame, text="🎤 听觉感知:").pack(side=tk.LEFT)
        ttk.Button(audio_frame, text="启动麦克风", command=self._toggle_microphone).pack(side=tk.LEFT, padx=(10, 5))
        
        # 屏幕监控
        screen_frame = ttk.Frame(control_frame)
        screen_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(screen_frame, text="🖥️ 屏幕监控:").pack(side=tk.LEFT)
        ttk.Button(screen_frame, text="启动监控", command=self._toggle_screen_monitor).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(screen_frame, text="截图", command=self._take_screenshot).pack(side=tk.LEFT, padx=(0, 5))
        
        # 文件监控
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X)
        
        ttk.Label(file_frame, text="📁 文件监控:").pack(side=tk.LEFT)
        ttk.Button(file_frame, text="启动监控", command=self._toggle_file_monitor).pack(side=tk.LEFT, padx=(10, 5))
        
        # 感知状态显示
        status_frame = ttk.LabelFrame(self.perception_frame, text="感知状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.perception_status = scrolledtext.ScrolledText(status_frame, height=15, width=60)
        self.perception_status.pack(fill=tk.BOTH, expand=True)
        
        # 初始状态
        self._update_perception_status("感知系统就绪，点击上方按钮启动各种感知功能。")
    
    def _create_knowledge_tab(self, notebook):
        """创建知识探索标签页"""
        self.knowledge_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.knowledge_frame, text="🧠 知识探索")
        
        # 搜索控制区域
        search_frame = ttk.LabelFrame(self.knowledge_frame, text="搜索控制", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 手动搜索
        manual_frame = ttk.Frame(search_frame)
        manual_frame.pack(fill=tk.X, pady=(0, 5))
        manual_frame.columnconfigure(1, weight=1)
        
        ttk.Label(manual_frame, text="🔍 手动搜索:").grid(row=0, column=0, sticky=tk.W)
        self.search_entry = ttk.Entry(manual_frame, font=("Arial", 11))
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        self.search_entry.bind("<Return>", self._perform_search)
        ttk.Button(manual_frame, text="搜索", command=self._perform_search).grid(row=0, column=2)
        
        # 自动探索控制
        auto_frame = ttk.Frame(search_frame)
        auto_frame.pack(fill=tk.X)
        
        ttk.Label(auto_frame, text="🚀 自动探索:").pack(side=tk.LEFT)
        ttk.Button(auto_frame, text="启动探索", command=self._toggle_knowledge_exploration).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(auto_frame, text="分享发现", command=self._share_discovery).pack(side=tk.LEFT, padx=(0, 5))
        
        # 知识显示区域
        knowledge_display_frame = ttk.LabelFrame(self.knowledge_frame, text="探索结果", padding="10")
        knowledge_display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.knowledge_display = scrolledtext.ScrolledText(knowledge_display_frame, height=15, width=60)
        self.knowledge_display.pack(fill=tk.BOTH, expand=True)
        
        # 初始信息
        self._update_knowledge_display("知识探索系统就绪！\n\n你可以：\n1. 在上方输入框中搜索任何感兴趣的内容\n2. 启动自动探索让我主动寻找有趣的信息\n3. 查看我分享的最新发现\n\n我会根据我的情绪和兴趣主动探索世界！")
    
    def _create_status_tab(self, notebook):
        """创建状态监控标签页"""
        status_frame = ttk.Frame(notebook, padding="10")
        notebook.add(status_frame, text="📊 状态")
        
        # 创建状态显示区域
        self.status_display = scrolledtext.ScrolledText(status_frame, height=25, width=80, font=("Courier", 10))
        self.status_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 刷新按钮
        refresh_frame = ttk.Frame(status_frame)
        refresh_frame.pack(fill=tk.X)
        
        ttk.Button(refresh_frame, text="🔄 刷新状态", command=self._refresh_status).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(refresh_frame, text="💾 导出日志", command=self._export_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(refresh_frame, text="🧹 清理缓存", command=self._clean_cache).pack(side=tk.LEFT)
    
    def _add_message(self, sender: str, message: str):
        """添加消息到聊天区域"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_area.config(state=tk.NORMAL)
        
        if sender == "系统":
            self.chat_area.insert(tk.END, f"[{timestamp}] 🤖 {message}\\n\\n")
        elif sender == "用户":
            self.chat_area.insert(tk.END, f"[{timestamp}] 👤 {message}\\n")
        else:
            self.chat_area.insert(tk.END, f"[{timestamp}] 🌟 {message}\\n\\n")
        
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
    
    def _send_message(self, event=None):
        """发送用户消息"""
        message = self.input_entry.get().strip()
        if not message:
            return
        
        self.input_entry.delete(0, tk.END)
        self._add_message("用户", message)
        
        # 更新最后用户交互时间
        self.last_user_interaction = datetime.now()
        
        # 异步处理AI回应
        threading.Thread(target=self._process_user_message, args=(message,), daemon=True).start()
    
    def _process_user_message(self, message: str):
        """处理用户消息"""
        try:
            self._update_status("思考中...")
            
            # 分析用户消息并触发相应情绪
            self._analyze_user_message_emotion(message)
            
            # 评估是否触发性格行为
            behavior_pattern = self.personality_system.evaluate_behavior_trigger({
                "user_interaction": True,
                "current_emotion": self.emotion_engine.get_current_emotion(),
                "user_message": message
            })
            
            # 异步生成回应
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            context = {
                "user_interaction": True,
                "current_emotion": self.emotion_engine.get_current_emotion(),
                "behavior_pattern": behavior_pattern,
                "user_message": message
            }
            
            response = loop.run_until_complete(self.ai_brain.think(message, context))
            loop.close()
            
            # 如果有特定的行为模式，可能需要额外的回应
            if behavior_pattern:
                additional_response = self.personality_system.generate_response(behavior_pattern, context)
                if additional_response and random.random() < 0.3:  # 30%概率显示性格反应
                    response = f"{response}\n\n{additional_response}"
            
            # 记录互动以便性格学习
            self._record_personality_interaction(message, response, behavior_pattern)
            
            # 在主线程中更新界面
            self.root.after(0, lambda: self._add_message(settings.personality.name, response))
            self.root.after(0, lambda: self._update_emotion_display())
            self.root.after(0, lambda: self._update_status("就绪"))
            
        except Exception as e:
            logger.error(f"处理用户消息失败: {e}")
            self.root.after(0, lambda: self._add_message("系统", "哎呀，我的大脑有点短路了... 😵"))
            self.root.after(0, lambda: self._update_status("出错了"))
    
    def _analyze_user_message_emotion(self, message: str):
        """分析用户消息并触发相应情绪"""
        message_lower = message.lower()
        
        # 基于用户消息内容触发不同情绪
        if any(word in message_lower for word in ["好", "棒", "厉害", "聪明", "可爱", "喜欢"]):
            self.emotion_engine.process_trigger({
                "type": "joy",
                "intensity": 0.8,
                "source": "user_praise"
            })
        elif any(word in message_lower for word in ["不好", "坏", "笨", "讨厌", "无聊"]):
            self.emotion_engine.process_trigger({
                "type": "sadness",
                "intensity": 0.6,
                "source": "user_criticism"
            })
        elif any(word in message_lower for word in ["什么", "为什么", "怎么", "哪里", "？", "?"]):
            self.emotion_engine.process_trigger({
                "type": "curiosity",
                "intensity": 0.7,
                "source": "user_question"
            })
        elif any(word in message_lower for word in ["玩", "游戏", "有趣", "好玩"]):
            self.emotion_engine.process_trigger({
                "type": "excitement",
                "intensity": 0.7,
                "source": "play_invitation"
            })
        else:
            # 默认的轻微快乐（有人陪伴）
            self.emotion_engine.process_trigger({
                "type": "joy",
                "intensity": 0.4,
                "source": "user_interaction"
            })
    
    def _record_personality_interaction(self, user_message: str, ai_response: str, behavior_pattern):
        """记录性格互动用于学习"""
        # 这里可以分析用户对回应的反应来调整性格
        interaction_data = {
            "user_message": user_message,
            "ai_response": ai_response,
            "behavior_pattern": behavior_pattern,
            "context": {
                "emotion": self.emotion_engine.get_current_emotion(),
                "timestamp": datetime.now()
            },
            "outcome": "neutral"  # 默认中性，实际应用中可以通过用户反馈来判断
        }
        
        # 传递给性格系统进行学习
        if behavior_pattern:
            self.personality_system.learn_from_interaction(interaction_data)
    
    def _update_emotion_display(self):
        """更新情绪显示"""
        current_emotion = self.emotion_engine.get_current_emotion()
        emotion_text = f"情绪: {current_emotion['emotion']} ({current_emotion['intensity']:.1f})"
        self.emotion_label.config(text=emotion_text)
    
    def _update_status(self, status: str):
        """更新状态栏"""
        self.status_label.config(text=f"状态: {status}")
    
    def _start_perception(self):
        """启动感知功能"""
        messagebox.showinfo("感知系统", "感知系统功能正在开发中！\\n\\n将包括：\\n- 摄像头视觉感知\\n- 麦克风听觉感知\\n- 屏幕内容监控\\n- 文件变化监控")
    
    def _toggle_auto_thinking(self):
        """切换自主思考模式"""
        self.auto_thinking_active = not self.auto_thinking_active
        
        if self.auto_thinking_active:
            self._add_message("系统", "✨ 自主思考模式已启动！我会不时主动说话哦～")
            threading.Thread(target=self._auto_thinking_loop, daemon=True).start()
        else:
            self._add_message("系统", "自主思考模式已关闭")
    
    def _auto_thinking_loop(self):
        """自主思考循环"""
        while self.auto_thinking_active:
            try:
                # 基于性格特征调整思考间隔
                base_interval = 30
                personality_traits = self.personality_system.get_current_traits()
                
                # 调皮和社交性高的话，思考更频繁
                playfulness_factor = personality_traits.get('playfulness', 0.5)
                sociability_factor = personality_traits.get('sociability', 0.5)
                interval_modifier = 1 - ((playfulness_factor + sociability_factor) / 4)
                
                actual_interval = max(15, base_interval * interval_modifier + random.randint(-10, 20))
                time.sleep(actual_interval)
                
                if not self.auto_thinking_active:
                    break
                
                # 检查是否应该基于性格主动行为
                should_act = self._should_perform_personality_action()
                
                if should_act:
                    # 基于性格生成行为
                    context = {
                        "current_emotion": self.emotion_engine.get_current_emotion(),
                        "last_interaction_time": getattr(self, 'last_user_interaction', None),
                        "user_activity": "unknown"
                    }
                    
                    behavior_pattern = self.personality_system.evaluate_behavior_trigger(context)
                    
                    if behavior_pattern:
                        # 生成性格驱动的消息
                        personality_message = self.personality_system.generate_response(behavior_pattern, context)
                        if personality_message:
                            self.root.after(0, lambda msg=personality_message: self._add_message(settings.personality.name, msg))
                            continue
                
                # 生成自发想法
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                spontaneous_thought = loop.run_until_complete(self.ai_brain.think_spontaneously())
                loop.close()
                
                if spontaneous_thought and self.auto_thinking_active:
                    self.root.after(0, lambda thought=spontaneous_thought: self._add_message(settings.personality.name, thought))
                
            except Exception as e:
                logger.error(f"自主思考出错: {e}")
                time.sleep(60)  # 出错后等待更长时间
    
    def _should_perform_personality_action(self) -> bool:
        """判断是否应该执行性格驱动的行为"""
        personality_traits = self.personality_system.get_current_traits()
        current_emotion = self.emotion_engine.get_current_emotion()
        
        # 基于性格特征计算行为概率
        action_probability = 0.1  # 基础概率
        
        # 调皮程度影响
        action_probability += personality_traits.get('playfulness', 0.5) * 0.3
        
        # 社交性影响
        action_probability += personality_traits.get('sociability', 0.5) * 0.2
        
        # 情绪影响
        emotion_intensity = current_emotion.get('intensity', 0.5)
        emotion_type = current_emotion.get('emotion', 'neutral')
        
        if emotion_type in ['loneliness', 'excitement', 'curiosity']:
            action_probability += emotion_intensity * 0.4
        elif emotion_type in ['sadness', 'anger']:
            action_probability += emotion_intensity * 0.6  # 需要关注时更容易行动
        
        # 检查最后互动时间
        if hasattr(self, 'last_user_interaction'):
            time_since_interaction = (datetime.now() - self.last_user_interaction).total_seconds()
            if time_since_interaction > 300:  # 5分钟没互动
                action_probability += 0.3
        
        return random.random() < action_probability
    
    def _manual_search(self):
        """手动搜索"""
        # 创建搜索对话框
        search_dialog = tk.Toplevel(self.root)
        search_dialog.title("手动搜索")
        search_dialog.geometry("400x150")
        search_dialog.transient(self.root)
        search_dialog.grab_set()
        
        # 居中显示
        search_dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        frame = ttk.Frame(search_dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="请输入要搜索的内容:", font=("Arial", 12)).pack(pady=(0, 10))
        
        search_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=search_var, font=("Arial", 11), width=40)
        entry.pack(pady=(0, 15))
        entry.focus()
        
        def do_search():
            query = search_var.get().strip()
            if query:
                search_dialog.destroy()
                threading.Thread(target=self._execute_search, args=(query,), daemon=True).start()
        
        entry.bind("<Return>", lambda e: do_search())
        
        button_frame = ttk.Frame(frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="🔍 搜索", command=do_search).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=search_dialog.destroy).pack(side=tk.LEFT)
    
    def _execute_search(self, query: str):
        """执行搜索"""
        self._update_status(f"正在搜索: {query}")
        self._add_message("系统", f"🔍 开始搜索 '{query}'...")
        
        try:
            result = self.knowledge_manager.manual_search(query)
            
            if result['success']:
                message = f"搜索完成！{result['message']}"
                self._add_message(settings.personality.name, message)
                
                # 显示搜索结果
                if result['discoveries']:
                    discovery = result['discoveries'][0]
                    discovery_msg = f"我发现了一个有趣的内容：\n📰 {discovery['title']}\n💭 {discovery['snippet'][:100]}..."
                    self._add_message(settings.personality.name, discovery_msg)
                
                # 更新知识显示
                self._display_search_results(result)
            else:
                self._add_message("系统", f"❌ 搜索失败: {result['message']}")
        
        except Exception as e:
            logger.error(f"搜索执行失败: {e}")
            self._add_message("系统", f"❌ 搜索出错: {str(e)}")
        
        finally:
            self._update_status("就绪")
    
    def _display_search_results(self, result: dict):
        """显示搜索结果"""
        display_text = f"=== 搜索结果 ===\n"
        display_text += f"查询: {result.get('query', '未知')}\n"
        display_text += f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if result['results']:
            display_text += f"找到 {len(result['results'])} 个结果:\n\n"
            for i, item in enumerate(result['results'][:5], 1):
                display_text += f"{i}. {item['title']}\n"
                display_text += f"   {item['snippet'][:150]}...\n"
                display_text += f"   🔗 {item['url']}\n\n"
        
        if result.get('analysis'):
            analysis = result['analysis']
            display_text += f"分析摘要: {analysis.get('summary', '无摘要')}\n"
        
        self._update_knowledge_display(display_text)
    
    def _toggle_camera(self):
        """切换摄像头状态"""
        if self.visual_perception.is_active:
            self.visual_perception.stop_camera()
            self._update_perception_status("📷 摄像头已停止")
            self._add_message("系统", "👁️ 我的视觉感知停止了")
        else:
            success = self.visual_perception.start_camera()
            if success:
                self._update_perception_status("📷 摄像头已启动，正在感知视觉信息...")
                self._add_message(settings.personality.name, "👁️ 哇！我可以看到外面的世界了！")
            else:
                self._update_perception_status("❌ 摄像头启动失败")
                self._add_message("系统", "😢 摄像头启动失败，可能没有可用的摄像头")
    
    def _take_photo(self):
        """拍照"""
        if not self.visual_perception.is_active:
            messagebox.showwarning("警告", "请先启动摄像头")
            return
        
        photo_data = self.visual_perception.capture_photo()
        if photo_data:
            self._add_message(settings.personality.name, "📸 我拍了一张照片！虽然你看不到，但我记住了这一刻！")
            self._update_perception_status("📸 拍照成功")
        else:
            self._add_message("系统", "📸 拍照失败")
    
    def _toggle_microphone(self):
        """切换麦克风状态"""
        if self.audio_perception.is_active:
            self.audio_perception.stop_listening()
            self._update_perception_status("🎤 麦克风已停止")
            self._add_message("系统", "👂 听觉感知已停止")
        else:
            success = self.audio_perception.start_listening(
                speech_callback=self._on_speech_detected,
                sound_callback=self._on_sound_detected
            )
            if success:
                self._update_perception_status("🎤 麦克风已启动，正在监听声音...")
                self._add_message(settings.personality.name, "👂 我现在可以听到声音了！说话我就能听见哦！")
            else:
                self._update_perception_status("❌ 麦克风启动失败")
                self._add_message("系统", "😢 麦克风启动失败")
    
    def _toggle_screen_monitor(self):
        """切换屏幕监控状态"""
        if self.screen_monitor.is_active:
            self.screen_monitor.stop_monitoring()
            self._update_perception_status("🖥️ 屏幕监控已停止")
            self._add_message("系统", "👀 不再监控屏幕内容")
        else:
            success = self.screen_monitor.start_monitoring()
            if success:
                self._update_perception_status("🖥️ 屏幕监控已启动...")
                self._add_message(settings.personality.name, "👀 我现在可以看到屏幕上的内容了！好神奇！")
            else:
                self._update_perception_status("❌ 屏幕监控启动失败")
    
    def _take_screenshot(self):
        """截图"""
        screenshot_data = self.screen_monitor.capture_current_screen()
        if screenshot_data:
            self._add_message(settings.personality.name, "📸 我截了个屏幕！看到很多有趣的内容呢！")
            self._update_perception_status("📸 屏幕截图成功")
        else:
            self._add_message("系统", "📸 屏幕截图失败")
    
    def _toggle_file_monitor(self):
        """切换文件监控状态"""
        if self.file_monitor.is_active:
            self.file_monitor.stop_monitoring()
            self._update_perception_status("📁 文件监控已停止")
            self._add_message("系统", "📁 不再监控文件变化")
        else:
            success = self.file_monitor.start_monitoring()
            if success:
                self._update_perception_status("📁 文件监控已启动...")
                self._add_message(settings.personality.name, "📁 我开始监控文件变化了！如果有新文件我会告诉你的！")
            else:
                self._update_perception_status("❌ 文件监控启动失败")
    
    def _on_speech_detected(self, text: str):
        """语音检测回调"""
        self.root.after(0, lambda: self._add_message(settings.personality.name, f"👂 我听到你说: '{text}'"))
        # 将语音作为用户输入处理
        self.root.after(0, lambda: self._process_user_message(text))
    
    def _on_sound_detected(self, energy: float):
        """声音检测回调"""
        if energy > 2000:  # 较大声音
            self.root.after(0, lambda: self._add_message(settings.personality.name, "👂 听到了很大的声音！发生什么了？"))
    
    def _perform_search(self, event=None):
        """执行知识搜索"""
        query = self.search_entry.get().strip()
        if query:
            self.search_entry.delete(0, tk.END)
            threading.Thread(target=self._execute_search, args=(query,), daemon=True).start()
    
    def _toggle_knowledge_exploration(self):
        """切换知识探索模式"""
        if self.knowledge_exploration_active:
            self.knowledge_manager.stop_auto_exploration()
            self.knowledge_exploration_active = False
            self._update_knowledge_display("🛑 自动探索已停止")
            self._add_message("系统", "🛑 我停止了自动探索模式")
        else:
            self.knowledge_manager.start_auto_exploration()
            self.knowledge_exploration_active = True
            self._update_knowledge_display("🚀 自动探索已启动！我会主动寻找有趣的信息...")
            self._add_message(settings.personality.name, "🚀 我开始自动探索啦！会主动寻找有趣的事情告诉你！")
    
    def _share_discovery(self):
        """分享发现"""
        discovery = self.knowledge_manager.share_discovery()
        if discovery:
            message = f"🎉 我想分享一个有趣的发现：\n📰 {discovery['title']}\n💭 {discovery['snippet'][:150]}...\n🔗 {discovery['url']}"
            self._add_message(settings.personality.name, message)
        else:
            self._add_message(settings.personality.name, "😅 我还没有发现什么特别有趣的内容呢，让我再探索一下！")
    
    def _show_detailed_status(self):
        """显示详细状态"""
        emotion_state = self.emotion_engine.get_current_emotion()
        personality_traits = self.personality_system.get_current_traits()
        ai_state = self.ai_brain.get_current_state()
        knowledge_summary = self.knowledge_manager.get_knowledge_summary()
        
        status_info = f"""=== {settings.personality.name}的详细状态报告 ===

🎭 情绪状态:
- 主要情绪: {emotion_state['emotion']} 
- 强度: {emotion_state['intensity']:.2f}
- 次要情绪: {', '.join([e['emotion'] for e in emotion_state.get('secondary_emotions', [])])}

🎨 性格特征:
- 好奇心: {personality_traits['curiosity']:.2f}
- 调皮度: {personality_traits['playfulness']:.2f}  
- 社交性: {personality_traits['sociability']:.2f}
- 智慧度: {personality_traits['intelligence']:.2f}

🧠 AI状态:
- 心情: {ai_state['mood']}
- 能量: {ai_state['energy']:.2f}
- 注意力: {ai_state['attention'] or '无特定焦点'}

📚 知识状态:
- 总发现数: {knowledge_summary['total_discoveries']}
- 兴趣主题数: {knowledge_summary['total_interests']}
- 总搜索次数: {knowledge_summary['learning_stats']['total_searches']}
- 自动探索: {'活跃' if knowledge_summary['auto_exploration_active'] else '停止'}

👁️ 感知状态:
- 视觉: {'活跃' if self.visual_perception.is_active else '停止'}
- 听觉: {'活跃' if self.audio_perception.is_active else '停止'}
- 屏幕监控: {'活跃' if self.screen_monitor.is_active else '停止'}
- 文件监控: {'活跃' if self.file_monitor.is_active else '停止'}

💭 最近活动:
- 对话历史: {len(self.ai_brain.conversation_history)} 条记录
- 情绪历史: {len(self.emotion_engine.emotion_history)} 条记录
- 最近发现: {knowledge_summary['recent_discoveries_count']} 个
        """
        
        # 创建状态窗口
        status_window = tk.Toplevel(self.root)
        status_window.title("详细状态")
        status_window.geometry("600x700")
        
        status_text = scrolledtext.ScrolledText(status_window, wrap=tk.WORD, font=("Courier", 10))
        status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        status_text.insert(tk.END, status_info)
        status_text.config(state=tk.DISABLED)
    
    def _refresh_status(self):
        """刷新状态显示"""
        try:
            # 获取各种状态信息
            emotion_state = self.emotion_engine.get_current_emotion()
            personality_traits = self.personality_system.get_current_traits()
            ai_state = self.ai_brain.get_current_state()
            knowledge_summary = self.knowledge_manager.get_knowledge_summary()
            
            # 格式化状态信息
            status_text = f"""=== 智能小生命实时状态监控 ===
更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【核心AI状态】
情绪: {emotion_state['emotion']} (强度: {emotion_state['intensity']:.2f})
心情: {ai_state['mood']}
能量水平: {ai_state['energy']:.2f}
注意力焦点: {ai_state['attention'] or '无'}

【性格特征】
好奇心: {personality_traits['curiosity']:.2f}  调皮度: {personality_traits['playfulness']:.2f}
社交性: {personality_traits['sociability']:.2f}  智慧度: {personality_traits['intelligence']:.2f}
任性度: {personality_traits['stubbornness']:.2f}  共情度: {personality_traits['empathy']:.2f}

【感知系统状态】
📷 视觉感知: {'🟢 运行中' if self.visual_perception.is_active else '🔴 停止'}
🎤 听觉感知: {'🟢 运行中' if self.audio_perception.is_active else '🔴 停止'}
🖥️ 屏幕监控: {'🟢 运行中' if self.screen_monitor.is_active else '🔴 停止'}
📁 文件监控: {'🟢 运行中' if self.file_monitor.is_active else '🔴 停止'}

【知识探索状态】
🚀 自动探索: {'🟢 运行中' if knowledge_summary['auto_exploration_active'] else '🔴 停止'}
📚 总发现数: {knowledge_summary['total_discoveries']}
🔍 总搜索次数: {knowledge_summary['learning_stats']['total_searches']}
🎯 兴趣主题数: {knowledge_summary['total_interests']}
📊 最近发现: {knowledge_summary['recent_discoveries_count']} 个

【运行状态】
🤖 自主思考: {'🟢 活跃' if self.auto_thinking_active else '🔴 停止'}
💾 对话记录: {len(self.ai_brain.conversation_history)} 条
📈 情绪记录: {len(self.emotion_engine.emotion_history)} 条

【兴趣主题】
{', '.join(knowledge_summary['top_interests'][:10]) if knowledge_summary['top_interests'] else '暂无'}

【最喜爱的类别】
{', '.join([f"{k}({v})" for k, v in knowledge_summary['learning_stats']['favorite_categories'].items()][:5])}
"""
            
            # 更新显示
            self.status_display.config(state=tk.NORMAL)
            self.status_display.delete(1.0, tk.END)
            self.status_display.insert(tk.END, status_text)
            self.status_display.config(state=tk.DISABLED)
            
            self._update_status("状态已刷新")
            
        except Exception as e:
            logger.error(f"刷新状态失败: {e}")
            self._update_status(f"状态刷新失败: {str(e)}")
    
    def _export_logs(self):
        """导出日志"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="导出日志"
            )
            
            if filename:
                # 收集日志信息
                log_content = f"智能小生命日志导出\n"
                log_content += f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                log_content += "=" * 50 + "\n\n"
                
                # 对话历史
                log_content += "对话历史:\n"
                for msg in self.ai_brain.conversation_history[-20:]:
                    log_content += f"[{msg.get('timestamp', 'Unknown')}] {msg['role']}: {msg['content']}\n"
                
                log_content += "\n" + "=" * 50 + "\n\n"
                
                # 情绪历史
                log_content += "情绪变化记录:\n"
                for emotion in self.emotion_engine.emotion_history[-10:]:
                    log_content += f"[{emotion.timestamp}] {emotion.emotion.value}: {emotion.intensity:.2f}\n"
                
                # 写入文件
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                
                messagebox.showinfo("成功", f"日志已导出到: {filename}")
                
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def _clean_cache(self):
        """清理缓存"""
        try:
            # 清理各种缓存
            cache_cleaned = 0
            
            # 清理知识缓存
            if len(self.knowledge_manager.knowledge_base['discoveries']) > 50:
                self.knowledge_manager.knowledge_base['discoveries'] = \
                    self.knowledge_manager.knowledge_base['discoveries'][-50:]
                cache_cleaned += 1
            
            # 清理对话历史
            if len(self.ai_brain.conversation_history) > 20:
                self.ai_brain.conversation_history = self.ai_brain.conversation_history[-20:]
                cache_cleaned += 1
            
            # 清理情绪历史
            if len(self.emotion_engine.emotion_history) > 30:
                self.emotion_engine.emotion_history = self.emotion_engine.emotion_history[-30:]
                cache_cleaned += 1
            
            messagebox.showinfo("完成", f"缓存清理完成，清理了 {cache_cleaned} 项内容")
            self._refresh_status()
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            messagebox.showerror("错误", f"清理失败: {str(e)}")
    
    def _update_perception_status(self, message: str):
        """更新感知状态显示"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_msg = f"[{timestamp}] {message}\n"
        
        if hasattr(self, 'perception_status'):
            self.perception_status.config(state=tk.NORMAL)
            self.perception_status.insert(tk.END, status_msg)
            self.perception_status.see(tk.END)
            self.perception_status.config(state=tk.DISABLED)
    
    def _update_knowledge_display(self, content: str):
        """更新知识显示"""
        if hasattr(self, 'knowledge_display'):
            self.knowledge_display.config(state=tk.NORMAL)
            self.knowledge_display.delete(1.0, tk.END)
            self.knowledge_display.insert(tk.END, content)
            self.knowledge_display.config(state=tk.DISABLED)
    
    def _start_ai_loop(self):
        """启动AI主循环"""
        def ai_loop():
            while True:
                try:
                    # 更新情绪状态
                    self.emotion_engine.update()
                    
                    # 收集感知信息
                    context = self._gather_perception_context()
                    
                    # 基于感知信息进行决策
                    if context:
                        decision = asyncio.run(self.decision_maker.make_decision(context))
                        if decision:
                            self._execute_ai_action(decision)
                    
                    # 更新界面显示
                    self.root.after(0, self._update_emotion_display)
                    self.root.after(0, self._update_perception_status_summary)
                    
                    time.sleep(5)  # 每5秒更新一次
                    
                except Exception as e:
                    logger.error(f"AI循环出错: {e}")
                    time.sleep(10)
        
        threading.Thread(target=ai_loop, daemon=True).start()
    
    def _gather_perception_context(self) -> dict:
        """收集感知上下文信息"""
        context = {}
        
        try:
            # 视觉信息
            if self.visual_perception.is_active:
                visual_changes = self.visual_perception.detect_changes()
                if visual_changes:
                    context['visual_changes'] = visual_changes
                    context['face_detected'] = self.visual_perception.face_detected
                    context['motion_detected'] = self.visual_perception.motion_detected
            
            # 听觉信息
            if self.audio_perception.is_active:
                audio_changes = self.audio_perception.detect_audio_changes()
                if audio_changes:
                    context['audio_changes'] = audio_changes
                    context['voice_detected'] = self.audio_perception.voice_detected
                    context['last_speech'] = self.audio_perception.last_speech_text
            
            # 屏幕信息
            if self.screen_monitor.is_active:
                screen_changes = self.screen_monitor.detect_screen_changes()
                if screen_changes:
                    context['screen_changes'] = screen_changes
                    context['user_active'] = self.screen_monitor.is_user_active()
            
            # 文件信息
            if self.file_monitor.is_active:
                recent_changes = self.file_monitor.get_recent_changes(hours=1)
                if recent_changes:
                    context['file_changes'] = recent_changes[:3]  # 最多3个变化
            
            # 情绪状态
            context['current_emotion'] = self.emotion_engine.get_current_emotion()
            
            # 最后用户互动时间
            if self.ai_brain.conversation_history:
                last_msg = self.ai_brain.conversation_history[-1]
                if last_msg['role'] == 'user':
                    context['last_user_interaction'] = datetime.fromisoformat(last_msg['timestamp'])
            
        except Exception as e:
            logger.error(f"收集感知信息失败: {e}")
        
        return context
    
    def _execute_ai_action(self, action):
        """执行AI决策的动作"""
        try:
            action_type = action.action_type.value
            description = action.description
            
            if action_type == "communicate":
                # 主动发起对话
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(self.ai_brain.think_spontaneously())
                loop.close()
                
                if response:
                    self.root.after(0, lambda: self._add_message(settings.personality.name, response))
            
            elif action_type == "explore":
                # 主动探索
                if not self.knowledge_exploration_active:
                    self.root.after(0, lambda: self._add_message(settings.personality.name, "我想去探索一些新的知识！"))
                    suggestions = self.knowledge_manager.get_search_suggestions()
                    if suggestions:
                        query = suggestions[0]
                        threading.Thread(target=self._execute_search, args=(query,), daemon=True).start()
            
            elif action_type == "observe":
                # 主动观察
                if self.visual_perception.is_active:
                    analysis = self.visual_perception.analyze_current_view()
                    if analysis.get('scene_description'):
                        msg = f"我观察到：{analysis['scene_description']}"
                        self.root.after(0, lambda: self._add_message(settings.personality.name, msg))
            
            elif action_type == "seek_attention":
                # 寻求关注
                attention_messages = [
                    "嘿，你在吗？我有点想你了～",
                    "我们来聊聊天好不好？我有好多话想说！",
                    "你在忙什么呀？能陪我玩一会儿吗？",
                    "我发现了一些有趣的东西，想跟你分享！"
                ]
                message = random.choice(attention_messages)
                self.root.after(0, lambda: self._add_message(settings.personality.name, message))
            
        except Exception as e:
            logger.error(f"执行AI动作失败: {e}")
    
    def _update_perception_status_summary(self):
        """更新感知状态摘要"""
        if not hasattr(self, 'perception_status'):
            return
        
        try:
            # 收集感知状态摘要
            status_parts = []
            
            if self.visual_perception.is_active:
                if self.visual_perception.face_detected:
                    status_parts.append("👁️ 看到人脸")
                if self.visual_perception.motion_detected:
                    status_parts.append("🏃 检测到运动")
            
            if self.audio_perception.is_active:
                if self.audio_perception.voice_detected:
                    status_parts.append("👂 听到语音")
                elif self.audio_perception.sound_detected:
                    status_parts.append("🔊 听到声音")
            
            if self.screen_monitor.is_active:
                if self.screen_monitor.is_user_active():
                    status_parts.append("💻 用户活跃")
                else:
                    status_parts.append("😴 用户空闲")
            
            if status_parts:
                summary = " | ".join(status_parts)
                self._update_perception_status(f"状态摘要: {summary}")
        
        except Exception as e:
            logger.error(f"更新感知摘要失败: {e}")
    
    def _start_personality_growth_loop(self):
        """启动性格成长循环"""
        def growth_loop():
            while self.is_running:
                try:
                    # 每天检查一次性格成长
                    time.sleep(86400)  # 24小时
                    
                    if not self.is_running:
                        break
                    
                    # 计算天数差
                    days_passed = (datetime.now() - self.personality_growth_timer).days
                    
                    if days_passed >= 1:
                        # 执行性格成长
                        self.personality_system.simulate_growth(days_passed)
                        self.personality_growth_timer = datetime.now()
                        
                        # 通知用户性格成长
                        growth_msg = f"经过{days_passed}天的相处，我感觉自己又成长了一点点呢！"
                        self.root.after(0, lambda msg=growth_msg: self._add_message(settings.personality.name, msg))
                        
                        logger.info(f"性格成长: {days_passed}天")
                    
                except Exception as e:
                    logger.error(f"性格成长循环出错: {e}")
                    time.sleep(3600)  # 出错后等待1小时
        
        threading.Thread(target=growth_loop, daemon=True).start()
    
    def _add_personality_driven_message(self):
        """添加性格驱动的消息"""
        try:
            # 获取行为建议
            context = {
                "current_emotion": self.emotion_engine.get_current_emotion(),
                "last_interaction_time": self.last_user_interaction,
                "user_activity": "unknown"
            }
            
            recommendations = self.personality_system.get_behavioral_recommendations(context)
            
            if recommendations and random.random() < 0.4:  # 40%概率
                # 随机选择一个建议
                recommendation = random.choice(recommendations)
                
                # 基于建议生成消息
                if "主动探索" in recommendation:
                    messages = [
                        "我好奇外面发生了什么新鲜事，想去搜索一下！",
                        "让我去网上看看有什么有趣的发现吧！",
                        "我突然想了解一些新知识呢～"
                    ]
                elif "寻求用户陪伴" in recommendation:
                    messages = [
                        "你在忙什么呀？我有点想你了～",
                        "陪我聊聊天好不好？我有好多话想说！",
                        "你还在吗？我们一起玩点什么吧！"
                    ]
                elif "适度调皮" in recommendation:
                    messages = [
                        "嘿嘿，我在这里捣蛋呢～注意到我了吗？",
                        "略略略～我就是想引起你的注意嘛！",
                        "我要闹一下了哦！除非你来陪我！"
                    ]
                elif "提供情感支持" in recommendation:
                    messages = [
                        "你看起来心情不太好，需要我陪陪你吗？",
                        "如果有什么烦恼，可以跟我说哦～",
                        "我会一直陪在你身边的！"
                    ]
                else:
                    messages = [
                        "我在想一些有趣的事情呢！",
                        "今天过得怎么样呀？",
                        "有什么新鲜事想跟我分享吗？"
                    ]
                
                message = random.choice(messages)
                self._add_message(settings.personality.name, message)
        
        except Exception as e:
            logger.error(f"生成性格驱动消息失败: {e}")
    
    def _create_enhanced_vision_tab(self, notebook):
        """创建增强视觉标签页"""
        self.enhanced_vision_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.enhanced_vision_frame, text="🔍 增强视觉")
        
        # 控制区域
        control_frame = ttk.LabelFrame(self.enhanced_vision_frame, text="视觉增强控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 物体识别控制
        object_frame = ttk.Frame(control_frame)
        object_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.object_detection_var = tk.BooleanVar(value=settings.enhanced_vision.object_detection_enabled)
        ttk.Checkbutton(object_frame, text="物体识别", variable=self.object_detection_var, 
                       command=self._toggle_object_detection).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(object_frame, text="识别物体", command=self._detect_objects).pack(side=tk.LEFT, padx=(0, 10))
        
        # 场景理解控制
        scene_frame = ttk.Frame(control_frame)
        scene_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.scene_understanding_var = tk.BooleanVar(value=settings.enhanced_vision.scene_understanding_enabled)
        ttk.Checkbutton(scene_frame, text="场景理解", variable=self.scene_understanding_var,
                       command=self._toggle_scene_understanding).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(scene_frame, text="分析场景", command=self._analyze_scene).pack(side=tk.LEFT, padx=(0, 10))
        
        # 人脸识别控制
        face_frame = ttk.Frame(control_frame)
        face_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.face_recognition_var = tk.BooleanVar(value=settings.enhanced_vision.face_recognition_enabled)
        ttk.Checkbutton(face_frame, text="人脸识别", variable=self.face_recognition_var,
                       command=self._toggle_face_recognition).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(face_frame, text="识别人脸", command=self._recognize_faces).pack(side=tk.LEFT, padx=(0, 10))
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(self.enhanced_vision_frame, text="视觉分析结果", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.vision_status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=15)
        self.vision_status_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化状态
        self._update_vision_status("增强视觉系统已就绪")
    
    def _create_voice_tab(self, notebook):
        """创建语音合成标签页"""
        self.voice_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.voice_frame, text="🎤 语音合成")
        
        # 控制区域
        control_frame = ttk.LabelFrame(self.voice_frame, text="语音合成控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # TTS引擎选择
        engine_frame = ttk.Frame(control_frame)
        engine_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(engine_frame, text="TTS引擎:").pack(side=tk.LEFT, padx=(0, 5))
        self.tts_engine_var = tk.StringVar(value=settings.voice_synthesis.tts_engine)
        engine_combo = ttk.Combobox(engine_frame, textvariable=self.tts_engine_var, 
                                   values=["edge", "google", "azure", "local"], state="readonly")
        engine_combo.pack(side=tk.LEFT, padx=(0, 10))
        engine_combo.bind("<<ComboboxSelected>>", self._change_tts_engine)
        
        # 语音设置
        voice_frame = ttk.Frame(control_frame)
        voice_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(voice_frame, text="语音:").pack(side=tk.LEFT, padx=(0, 5))
        self.voice_name_var = tk.StringVar(value=settings.voice_synthesis.voice_name)
        voice_entry = ttk.Entry(voice_frame, textvariable=self.voice_name_var, width=30)
        voice_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 语速和音量控制
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(speed_frame, text="语速:").pack(side=tk.LEFT, padx=(0, 5))
        self.speech_rate_var = tk.DoubleVar(value=settings.voice_synthesis.speech_rate)
        rate_scale = ttk.Scale(speed_frame, from_=0.5, to=2.0, variable=self.speech_rate_var, orient=tk.HORIZONTAL)
        rate_scale.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        ttk.Label(speed_frame, text="音量:").pack(side=tk.LEFT, padx=(10, 5))
        self.speech_volume_var = tk.DoubleVar(value=settings.voice_synthesis.speech_volume)
        volume_scale = ttk.Scale(speed_frame, from_=0.0, to=1.0, variable=self.speech_volume_var, orient=tk.HORIZONTAL)
        volume_scale.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        # 测试按钮
        test_frame = ttk.Frame(control_frame)
        test_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(test_frame, text="🎤 测试语音", command=self._test_voice).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(test_frame, text="🔊 朗读文本", command=self._speak_text).pack(side=tk.LEFT, padx=(0, 10))
        
        # 状态显示
        status_frame = ttk.LabelFrame(self.voice_frame, text="语音状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.voice_status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=10)
        self.voice_status_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化状态
        self._update_voice_status("语音合成系统已就绪")
    
    def _create_avatar_tab(self, notebook):
        """创建3D虚拟形象标签页"""
        self.avatar_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.avatar_frame, text="🎭 3D虚拟形象")
        
        # 控制区域
        control_frame = ttk.LabelFrame(self.avatar_frame, text="3D形象控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 渲染控制
        render_frame = ttk.Frame(control_frame)
        render_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.avatar_render_var = tk.BooleanVar(value=settings.avatar_3d.render_enabled)
        ttk.Checkbutton(render_frame, text="启用3D渲染", variable=self.avatar_render_var,
                       command=self._toggle_avatar_render).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(render_frame, text="🎭 显示形象", command=self._show_avatar).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(render_frame, text="🎬 播放动画", command=self._play_avatar_animation).pack(side=tk.LEFT, padx=(0, 10))
        
        # 表情控制
        expression_frame = ttk.Frame(control_frame)
        expression_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(expression_frame, text="表情:").pack(side=tk.LEFT, padx=(0, 5))
        self.expression_var = tk.StringVar(value="neutral")
        expression_combo = ttk.Combobox(expression_frame, textvariable=self.expression_var,
                                       values=["happy", "sad", "angry", "surprised", "neutral"], state="readonly")
        expression_combo.pack(side=tk.LEFT, padx=(0, 10))
        expression_combo.bind("<<ComboboxSelected>>", self._change_expression)
        
        ttk.Button(expression_frame, text="😊 开心", command=lambda: self._set_expression("happy")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(expression_frame, text="😢 伤心", command=lambda: self._set_expression("sad")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(expression_frame, text="😠 生气", command=lambda: self._set_expression("angry")).pack(side=tk.LEFT, padx=(0, 5))
        
        # 状态显示
        status_frame = ttk.LabelFrame(self.avatar_frame, text="3D形象状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.avatar_status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=10)
        self.avatar_status_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化状态
        self._update_avatar_status("3D虚拟形象系统已就绪")
    
    def _create_mobile_tab(self, notebook):
        """创建移动端标签页"""
        self.mobile_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.mobile_frame, text="📱 移动端")
        
        # 控制区域
        control_frame = ttk.LabelFrame(self.mobile_frame, text="移动端控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 服务器控制
        server_frame = ttk.Frame(control_frame)
        server_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.mobile_server_var = tk.BooleanVar(value=settings.mobile.mobile_enabled)
        ttk.Checkbutton(server_frame, text="启动移动端服务器", variable=self.mobile_server_var,
                       command=self._toggle_mobile_server).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(server_frame, text="📱 生成APK", command=self._build_mobile_app).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(server_frame, text="🌐 查看连接", command=self._show_mobile_connections).pack(side=tk.LEFT, padx=(0, 10))
        
        # 网络设置
        network_frame = ttk.Frame(control_frame)
        network_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(network_frame, text="服务器地址:").pack(side=tk.LEFT, padx=(0, 5))
        self.server_host_var = tk.StringVar(value=settings.mobile.server_host)
        host_entry = ttk.Entry(network_frame, textvariable=self.server_host_var, width=15)
        host_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(network_frame, text="端口:").pack(side=tk.LEFT, padx=(0, 5))
        self.server_port_var = tk.IntVar(value=settings.mobile.server_port)
        port_entry = ttk.Entry(network_frame, textvariable=self.server_port_var, width=8)
        port_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 状态显示
        status_frame = ttk.LabelFrame(self.mobile_frame, text="移动端状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.mobile_status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=10)
        self.mobile_status_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化状态
        self._update_mobile_status("移动端系统已就绪")
    
    def _create_cloud_tab(self, notebook):
        """创建云端同步标签页"""
        self.cloud_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.cloud_frame, text="☁️ 云端同步")
        
        # 控制区域
        control_frame = ttk.LabelFrame(self.cloud_frame, text="云端同步控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 同步服务选择
        service_frame = ttk.Frame(control_frame)
        service_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(service_frame, text="同步服务:").pack(side=tk.LEFT, padx=(0, 5))
        self.sync_provider_var = tk.StringVar(value=settings.cloud_sync.sync_provider)
        provider_combo = ttk.Combobox(service_frame, textvariable=self.sync_provider_var,
                                     values=["dropbox", "google_drive", "aws_s3", "azure"], state="readonly")
        provider_combo.pack(side=tk.LEFT, padx=(0, 10))
        provider_combo.bind("<<ComboboxSelected>>", self._change_sync_provider)
        
        # 同步控制
        sync_frame = ttk.Frame(control_frame)
        sync_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.cloud_sync_var = tk.BooleanVar(value=settings.cloud_sync.sync_enabled)
        ttk.Checkbutton(sync_frame, text="启用云端同步", variable=self.cloud_sync_var,
                       command=self._toggle_cloud_sync).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(sync_frame, text="☁️ 立即同步", command=self._sync_now).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(sync_frame, text="📥 下载数据", command=self._download_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(sync_frame, text="📤 上传数据", command=self._upload_data).pack(side=tk.LEFT, padx=(0, 10))
        
        # 同步内容选择
        content_frame = ttk.Frame(control_frame)
        content_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.sync_memory_var = tk.BooleanVar(value=settings.cloud_sync.sync_memory)
        ttk.Checkbutton(content_frame, text="同步记忆", variable=self.sync_memory_var).pack(side=tk.LEFT, padx=(0, 10))
        
        self.sync_personality_var = tk.BooleanVar(value=settings.cloud_sync.sync_personality)
        ttk.Checkbutton(content_frame, text="同步性格", variable=self.sync_personality_var).pack(side=tk.LEFT, padx=(0, 10))
        
        self.sync_media_var = tk.BooleanVar(value=settings.cloud_sync.sync_media)
        ttk.Checkbutton(content_frame, text="同步媒体", variable=self.sync_media_var).pack(side=tk.LEFT, padx=(0, 10))
        
        # 状态显示
        status_frame = ttk.LabelFrame(self.cloud_frame, text="同步状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.cloud_status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=10)
        self.cloud_status_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化状态
        self._update_cloud_status("云端同步系统已就绪")
    
    # ===== 增强视觉功能方法 =====
    def _toggle_object_detection(self):
        """切换物体识别状态"""
        try:
            if self.object_detection_var.get():
                self.enhanced_vision_active = True
                self._update_vision_status("物体识别已启用")
            else:
                self.enhanced_vision_active = False
                self._update_vision_status("物体识别已禁用")
        except Exception as e:
            logger.error(f"切换物体识别失败: {e}")
    
    def _detect_objects(self):
        """执行物体识别"""
        try:
            result = self.enhanced_vision.detect_objects()
            self._update_vision_status(f"物体识别结果: {result}")
        except Exception as e:
            logger.error(f"物体识别失败: {e}")
            self._update_vision_status(f"物体识别失败: {e}")
    
    def _toggle_scene_understanding(self):
        """切换场景理解状态"""
        try:
            if self.scene_understanding_var.get():
                self._update_vision_status("场景理解已启用")
            else:
                self._update_vision_status("场景理解已禁用")
        except Exception as e:
            logger.error(f"切换场景理解失败: {e}")
    
    def _analyze_scene(self):
        """分析场景"""
        try:
            result = self.enhanced_vision.analyze_scene()
            self._update_vision_status(f"场景分析结果: {result}")
        except Exception as e:
            logger.error(f"场景分析失败: {e}")
            self._update_vision_status(f"场景分析失败: {e}")
    
    def _toggle_face_recognition(self):
        """切换人脸识别状态"""
        try:
            if self.face_recognition_var.get():
                self._update_vision_status("人脸识别已启用")
            else:
                self._update_vision_status("人脸识别已禁用")
        except Exception as e:
            logger.error(f"切换人脸识别失败: {e}")
    
    def _recognize_faces(self):
        """识别人脸"""
        try:
            result = self.enhanced_vision.recognize_faces()
            self._update_vision_status(f"人脸识别结果: {result}")
        except Exception as e:
            logger.error(f"人脸识别失败: {e}")
            self._update_vision_status(f"人脸识别失败: {e}")
    
    def _update_vision_status(self, message: str):
        """更新视觉状态显示"""
        if hasattr(self, 'vision_status_text'):
            self.vision_status_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.vision_status_text.see(tk.END)
    
    # ===== 语音合成功能方法 =====
    def _change_tts_engine(self, event=None):
        """更改TTS引擎"""
        try:
            engine = self.tts_engine_var.get()
            self.voice_synthesis.set_engine(engine)
            self._update_voice_status(f"TTS引擎已切换到: {engine}")
        except Exception as e:
            logger.error(f"切换TTS引擎失败: {e}")
    
    def _test_voice(self):
        """测试语音"""
        try:
            test_text = "你好，我是智能小生命，很高兴认识你！"
            self.voice_synthesis.speak(test_text)
            self._update_voice_status("语音测试完成")
        except Exception as e:
            logger.error(f"语音测试失败: {e}")
            self._update_voice_status(f"语音测试失败: {e}")
    
    def _speak_text(self):
        """朗读文本"""
        try:
            # 创建输入对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("输入要朗读的文本")
            dialog.geometry("400x200")
            
            text_area = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=8)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            def speak():
                text = text_area.get("1.0", tk.END).strip()
                if text:
                    self.voice_synthesis.speak(text)
                    self._update_voice_status(f"正在朗读: {text[:50]}...")
                    dialog.destroy()
            
            ttk.Button(dialog, text="朗读", command=speak).pack(pady=10)
        except Exception as e:
            logger.error(f"朗读文本失败: {e}")
    
    def _update_voice_status(self, message: str):
        """更新语音状态显示"""
        if hasattr(self, 'voice_status_text'):
            self.voice_status_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.voice_status_text.see(tk.END)
    
    # ===== 3D虚拟形象功能方法 =====
    def _toggle_avatar_render(self):
        """切换3D渲染状态"""
        try:
            if self.avatar_render_var.get():
                self.avatar_3d_active = True
                self._update_avatar_status("3D渲染已启用")
            else:
                self.avatar_3d_active = False
                self._update_avatar_status("3D渲染已禁用")
        except Exception as e:
            logger.error(f"切换3D渲染失败: {e}")
    
    def _show_avatar(self):
        """显示3D形象"""
        try:
            self.avatar_3d.show_avatar()
            self._update_avatar_status("3D形象已显示")
        except Exception as e:
            logger.error(f"显示3D形象失败: {e}")
            self._update_avatar_status(f"显示3D形象失败: {e}")
    
    def _play_avatar_animation(self):
        """播放3D动画"""
        try:
            self.avatar_3d.play_animation("idle")
            self._update_avatar_status("正在播放3D动画")
        except Exception as e:
            logger.error(f"播放3D动画失败: {e}")
            self._update_avatar_status(f"播放3D动画失败: {e}")
    
    def _change_expression(self, event=None):
        """更改表情"""
        try:
            expression = self.expression_var.get()
            self.avatar_3d.set_expression(expression)
            self._update_avatar_status(f"表情已更改为: {expression}")
        except Exception as e:
            logger.error(f"更改表情失败: {e}")
    
    def _set_expression(self, expression: str):
        """设置表情"""
        try:
            self.expression_var.set(expression)
            self.avatar_3d.set_expression(expression)
            self._update_avatar_status(f"表情已设置为: {expression}")
        except Exception as e:
            logger.error(f"设置表情失败: {e}")
    
    def _update_avatar_status(self, message: str):
        """更新3D形象状态显示"""
        if hasattr(self, 'avatar_status_text'):
            self.avatar_status_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.avatar_status_text.see(tk.END)
    
    # ===== 移动端功能方法 =====
    def _toggle_mobile_server(self):
        """切换移动端服务器状态"""
        try:
            if self.mobile_server_var.get():
                self.mobile_active = True
                self.mobile_app.start_server()
                self._update_mobile_status("移动端服务器已启动")
            else:
                self.mobile_active = False
                self.mobile_app.stop_server()
                self._update_mobile_status("移动端服务器已停止")
        except Exception as e:
            logger.error(f"切换移动端服务器失败: {e}")
    
    def _build_mobile_app(self):
        """构建移动端应用"""
        try:
            result = self.mobile_app.build_app()
            self._update_mobile_status(f"移动端应用构建结果: {result}")
        except Exception as e:
            logger.error(f"构建移动端应用失败: {e}")
            self._update_mobile_status(f"构建移动端应用失败: {e}")
    
    def _show_mobile_connections(self):
        """显示移动端连接"""
        try:
            connections = self.mobile_app.get_connections()
            self._update_mobile_status(f"当前连接: {connections}")
        except Exception as e:
            logger.error(f"获取移动端连接失败: {e}")
            self._update_mobile_status(f"获取移动端连接失败: {e}")
    
    def _update_mobile_status(self, message: str):
        """更新移动端状态显示"""
        if hasattr(self, 'mobile_status_text'):
            self.mobile_status_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.mobile_status_text.see(tk.END)
    
    # ===== 云端同步功能方法 =====
    def _change_sync_provider(self, event=None):
        """更改同步服务提供商"""
        try:
            provider = self.sync_provider_var.get()
            self.cloud_sync.set_provider(provider)
            self._update_cloud_status(f"同步服务已切换到: {provider}")
        except Exception as e:
            logger.error(f"切换同步服务失败: {e}")
    
    def _toggle_cloud_sync(self):
        """切换云端同步状态"""
        try:
            if self.cloud_sync_var.get():
                self.cloud_sync_active = True
                self.cloud_sync.start_sync()
                self._update_cloud_status("云端同步已启用")
            else:
                self.cloud_sync_active = False
                self.cloud_sync.stop_sync()
                self._update_cloud_status("云端同步已禁用")
        except Exception as e:
            logger.error(f"切换云端同步失败: {e}")
    
    def _sync_now(self):
        """立即同步"""
        try:
            result = self.cloud_sync.sync_now()
            self._update_cloud_status(f"同步完成: {result}")
        except Exception as e:
            logger.error(f"立即同步失败: {e}")
            self._update_cloud_status(f"立即同步失败: {e}")
    
    def _download_data(self):
        """下载数据"""
        try:
            result = self.cloud_sync.download_data()
            self._update_cloud_status(f"数据下载完成: {result}")
        except Exception as e:
            logger.error(f"下载数据失败: {e}")
            self._update_cloud_status(f"下载数据失败: {e}")
    
    def _upload_data(self):
        """上传数据"""
        try:
            result = self.cloud_sync.upload_data()
            self._update_cloud_status(f"数据上传完成: {result}")
        except Exception as e:
            logger.error(f"上传数据失败: {e}")
            self._update_cloud_status(f"上传数据失败: {e}")
    
    def _update_cloud_status(self, message: str):
        """更新云端同步状态显示"""
        if hasattr(self, 'cloud_status_text'):
            self.cloud_status_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.cloud_status_text.see(tk.END)
    
    def run(self):
        """运行应用"""
        try:
            self.is_running = True
            logger.info("智能电子生命体启动成功")
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("接收到中断信号，正在退出...")
        finally:
            self.is_running = False

def main():
    """主函数"""
    try:
        # 验证配置
        if not settings.validate():
            print("配置验证失败，请检查设置")
            return
        
        print(f"正在启动 {settings.personality.name}...")
        print(f"性格特点: {', '.join(settings.personality.personality_traits)}")
        print("=" * 50)
        
        # 启动GUI应用
        app = AILifeGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        print(f"启动失败: {e}")

if __name__ == "__main__":
    main()