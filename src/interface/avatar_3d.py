"""
3D虚拟形象模块 - 可视化AI角色
"""
import logging
import json
import requests
import threading
import queue
import math
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import random

try:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.messagebox as messagebox
except ImportError:
    tk = None

try:
    # 使用Ursina引擎创建3D场景
    from ursina import *
    from ursina.prefabs.first_person_controller import FirstPersonController
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

try:
    # 备用：使用matplotlib的3D绘图
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from config.settings import settings

logger = logging.getLogger(__name__)

class Avatar3D:
    """3D虚拟形象系统"""
    
    def __init__(self):
        self.avatar_window = None
        self.avatar_app = None
        
        # 形象状态
        self.current_emotion = 'neutral'
        self.current_animation = 'idle'
        self.is_speaking = False
        self.energy_level = 1.0
        
        # 动画队列
        self.animation_queue = queue.Queue()
        self.animation_thread = None
        
        # 形象配置
        self.avatar_config = {
            'model_type': 'simple',  # simple, detailed, custom
            'color_scheme': 'cute',  # cute, elegant, cool
            'size': 1.0,
            'position': (0, 0, 0),
            'animations_enabled': True
        }
        
        # 情绪表情映射
        self.emotion_expressions = {
            'joy': {'eye_scale': 1.2, 'mouth_curve': 0.8, 'color_tint': (1.0, 0.9, 0.9)},
            'sadness': {'eye_scale': 0.8, 'mouth_curve': -0.5, 'color_tint': (0.9, 0.9, 1.0)},
            'excitement': {'eye_scale': 1.4, 'mouth_curve': 1.0, 'color_tint': (1.0, 1.0, 0.8)},
            'curiosity': {'eye_scale': 1.1, 'mouth_curve': 0.3, 'color_tint': (0.95, 1.0, 0.95)},
            'anger': {'eye_scale': 0.9, 'mouth_curve': -0.8, 'color_tint': (1.0, 0.8, 0.8)},
            'neutral': {'eye_scale': 1.0, 'mouth_curve': 0.0, 'color_tint': (1.0, 1.0, 1.0)}
        }
        
        # 预定义动画
        self.animations = {
            'idle': self._create_idle_animation,
            'happy_bounce': self._create_happy_bounce,
            'sad_droop': self._create_sad_droop,
            'excited_jump': self._create_excited_jump,
            'curious_lean': self._create_curious_lean,
            'speaking': self._create_speaking_animation,
            'thinking': self._create_thinking_animation,
            'dancing': self._create_dancing_animation
        }
        
        # 启动动画处理线程
        self._start_animation_thread()
    
    def create_avatar_window(self, parent=None) -> tk.Toplevel:
        """创建3D形象窗口"""
        if self.avatar_window and self.avatar_window.winfo_exists():
            self.avatar_window.lift()
            return self.avatar_window
        
        try:
            if URSINA_AVAILABLE:
                return self._create_ursina_avatar()
            elif MATPLOTLIB_AVAILABLE:
                return self._create_matplotlib_avatar(parent)
            else:
                return self._create_simple_avatar(parent)
        except Exception as e:
            logger.error(f"创建3D形象窗口失败: {e}")
            return self._create_simple_avatar(parent)
    
    def _create_ursina_avatar(self) -> Optional[tk.Toplevel]:
        """使用Ursina引擎创建3D形象"""
        try:
            def start_ursina():
                app = Ursina()
                
                # 创建3D角色
                self.avatar_entity = self._create_3d_character()
                
                # 设置摄像机
                camera.position = (0, 2, -5)
                camera.rotation_x = 10
                
                # 创建简单环境
                ground = Entity(model='cube', scale=(10, 0.1, 10), color=color.green)
                sky = Sky()
                
                # 添加光源
                DirectionalLight().look_at(Vec3(1, -1, -1))
                
                # 启动应用
                app.run()
            
            # 在单独线程中运行Ursina
            ursina_thread = threading.Thread(target=start_ursina, daemon=True)
            ursina_thread.start()
            
            logger.info("Ursina 3D形象已启动")
            return None  # Ursina有自己的窗口系统
            
        except Exception as e:
            logger.error(f"Ursina 3D形象创建失败: {e}")
            return None
    
    def _create_3d_character(self):
        """创建3D角色模型"""
        # 创建简单的角色模型
        character = Entity()
        
        # 身体
        body = Entity(
            parent=character,
            model='cube',
            scale=(0.8, 1.2, 0.4),
            color=color.pink,
            position=(0, 0, 0)
        )
        
        # 头部
        head = Entity(
            parent=character,
            model='sphere',
            scale=0.6,
            color=color.peach,
            position=(0, 1.4, 0)
        )
        
        # 眼睛
        left_eye = Entity(
            parent=head,
            model='sphere',
            scale=0.1,
            color=color.black,
            position=(-0.15, 0.1, 0.25)
        )
        
        right_eye = Entity(
            parent=head,
            model='sphere',
            scale=0.1,
            color=color.black,
            position=(0.15, 0.1, 0.25)
        )
        
        # 嘴巴
        mouth = Entity(
            parent=head,
            model='cube',
            scale=(0.2, 0.05, 0.05),
            color=color.red,
            position=(0, -0.1, 0.25)
        )
        
        # 存储角色部件引用
        character.body = body
        character.head = head
        character.left_eye = left_eye
        character.right_eye = right_eye
        character.mouth = mouth
        
        return character
    
    def _create_matplotlib_avatar(self, parent) -> tk.Toplevel:
        """使用Matplotlib创建3D形象"""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from mpl_toolkits.mplot3d import Axes3D
        
        # 创建窗口
        avatar_window = tk.Toplevel(parent)
        avatar_window.title("🌟 AI 3D形象")
        avatar_window.geometry("600x500")
        
        # 创建3D图形
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection='3d')
        
        # 绘制简单的3D角色
        self._draw_3d_character(ax)
        
        # 嵌入到Tkinter窗口
        canvas = FigureCanvasTkAgg(fig, avatar_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 控制面板
        control_frame = ttk.Frame(avatar_window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="😊 开心", 
                  command=lambda: self.set_emotion('joy')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="😢 难过", 
                  command=lambda: self.set_emotion('sadness')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🎉 兴奋", 
                  command=lambda: self.set_emotion('excitement')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🤔 好奇", 
                  command=lambda: self.set_emotion('curiosity')).pack(side=tk.LEFT, padx=5)
        
        # 动画控制
        anim_frame = ttk.Frame(avatar_window)
        anim_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(anim_frame, text="🕺 跳舞", 
                  command=lambda: self.play_animation('dancing')).pack(side=tk.LEFT, padx=5)
        ttk.Button(anim_frame, text="💭 思考", 
                  command=lambda: self.play_animation('thinking')).pack(side=tk.LEFT, padx=5)
        ttk.Button(anim_frame, text="💬 说话", 
                  command=lambda: self.play_animation('speaking')).pack(side=tk.LEFT, padx=5)
        
        self.avatar_window = avatar_window
        self.avatar_canvas = canvas
        self.avatar_fig = fig
        self.avatar_ax = ax
        
        # 启动动画循环
        self._start_matplotlib_animation()
        
        return avatar_window
    
    def _draw_3d_character(self, ax):
        """绘制3D角色"""
        # 清除之前的绘图
        ax.clear()
        
        # 获取当前情绪表情
        expression = self.emotion_expressions.get(self.current_emotion, self.emotion_expressions['neutral'])
        
        # 身体（圆柱体）
        theta = np.linspace(0, 2 * np.pi, 20)
        z_body = np.linspace(-1, 1, 10)
        theta_body, z_body = np.meshgrid(theta, z_body)
        x_body = 0.5 * np.cos(theta_body)
        y_body = 0.5 * np.sin(theta_body)
        
        ax.plot_surface(x_body, y_body, z_body, alpha=0.7, color='lightblue')
        
        # 头部（球体）
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 20)
        x_head = 0.8 * np.outer(np.cos(u), np.sin(v))
        y_head = 0.8 * np.outer(np.sin(u), np.sin(v))
        z_head = 0.8 * np.outer(np.ones(np.size(u)), np.cos(v)) + 2.5
        
        color_tint = expression['color_tint']
        ax.plot_surface(x_head, y_head, z_head, alpha=0.8, color=color_tint)
        
        # 眼睛
        eye_scale = expression['eye_scale']
        ax.scatter([-0.3, 0.3], [0.6, 0.6], [2.8, 2.8], 
                  s=100*eye_scale, c='black', alpha=0.8)
        
        # 嘴巴
        mouth_curve = expression['mouth_curve']
        mouth_x = np.linspace(-0.3, 0.3, 10)
        mouth_y = np.full_like(mouth_x, 0.8)
        mouth_z = np.full_like(mouth_x, 2.3) + mouth_curve * 0.1 * (mouth_x**2)
        ax.plot(mouth_x, mouth_y, mouth_z, 'r-', linewidth=3)
        
        # 设置图形属性
        ax.set_xlim([-2, 2])
        ax.set_ylim([-2, 2])
        ax.set_zlim([-2, 4])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'AI小生命 - 情绪: {self.current_emotion}')
        
        # 隐藏坐标轴
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
    
    def _create_simple_avatar(self, parent) -> tk.Toplevel:
        """创建简单的2D形象"""
        avatar_window = tk.Toplevel(parent)
        avatar_window.title("🌟 AI形象")
        avatar_window.geometry("400x300")
        
        # 创建画布
        canvas = tk.Canvas(avatar_window, width=350, height=250, bg='lightblue')
        canvas.pack(pady=20)
        
        # 绘制简单角色
        self._draw_simple_character(canvas)
        
        # 控制按钮
        control_frame = ttk.Frame(avatar_window)
        control_frame.pack(pady=10)
        
        emotions = [('😊', 'joy'), ('😢', 'sadness'), ('🎉', 'excitement'), ('🤔', 'curiosity')]
        for emoji, emotion in emotions:
            ttk.Button(control_frame, text=emoji, 
                      command=lambda e=emotion: self.set_emotion(e)).pack(side=tk.LEFT, padx=5)
        
        self.avatar_window = avatar_window
        self.avatar_canvas = canvas
        
        return avatar_window
    
    def _draw_simple_character(self, canvas):
        """绘制简单2D角色"""
        canvas.delete("all")
        
        expression = self.emotion_expressions.get(self.current_emotion, self.emotion_expressions['neutral'])
        
        # 身体
        canvas.create_oval(125, 100, 225, 200, fill='lightpink', outline='pink', width=2)
        
        # 头部
        head_color = f"#{int(255*expression['color_tint'][0]):02x}{int(255*expression['color_tint'][1]):02x}{int(255*expression['color_tint'][2]):02x}"
        canvas.create_oval(150, 50, 200, 100, fill=head_color, outline='gray', width=2)
        
        # 眼睛
        eye_size = int(8 * expression['eye_scale'])
        canvas.create_oval(160-eye_size//2, 65-eye_size//2, 160+eye_size//2, 65+eye_size//2, fill='black')
        canvas.create_oval(190-eye_size//2, 65-eye_size//2, 190+eye_size//2, 65+eye_size//2, fill='black')
        
        # 嘴巴
        mouth_curve = expression['mouth_curve']
        if mouth_curve > 0:
            # 笑脸
            canvas.create_arc(165, 75, 185, 90, start=0, extent=180, style='arc', width=2, outline='red')
        elif mouth_curve < 0:
            # 哭脸
            canvas.create_arc(165, 85, 185, 95, start=180, extent=180, style='arc', width=2, outline='blue')
        else:
            # 中性
            canvas.create_line(165, 82, 185, 82, width=2, fill='gray')
        
        # 添加文字
        canvas.create_text(175, 220, text=f"情绪: {self.current_emotion}", font=('Arial', 12))
    
    def _start_animation_thread(self):
        """启动动画处理线程"""
        def animation_worker():
            while True:
                try:
                    animation_task = self.animation_queue.get(timeout=1)
                    if animation_task is None:
                        break
                    
                    self._execute_animation(animation_task)
                    self.animation_queue.task_done()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"动画执行失败: {e}")
        
        self.animation_thread = threading.Thread(target=animation_worker, daemon=True)
        self.animation_thread.start()
    
    def _start_matplotlib_animation(self):
        """启动matplotlib动画循环"""
        def animate(frame):
            if hasattr(self, 'avatar_ax'):
                self._draw_3d_character(self.avatar_ax)
                if hasattr(self, 'avatar_canvas'):
                    self.avatar_canvas.draw()
        
        if hasattr(self, 'avatar_fig'):
            self.animation_timer = self.avatar_fig.canvas.new_timer(interval=100)
            self.animation_timer.add_callback(animate, None)
            self.animation_timer.start()
    
    def set_emotion(self, emotion: str):
        """设置情绪表情"""
        if emotion in self.emotion_expressions:
            self.current_emotion = emotion
            logger.info(f"设置AI形象情绪为: {emotion}")
            
            # 触发相应动画
            if emotion == 'joy':
                self.play_animation('happy_bounce')
            elif emotion == 'sadness':
                self.play_animation('sad_droop')
            elif emotion == 'excitement':
                self.play_animation('excited_jump')
            elif emotion == 'curiosity':
                self.play_animation('curious_lean')
    
    def play_animation(self, animation_name: str, duration: float = 2.0):
        """播放动画"""
        if animation_name in self.animations:
            animation_task = {
                'name': animation_name,
                'duration': duration,
                'timestamp': datetime.now()
            }
            self.animation_queue.put(animation_task)
            logger.info(f"播放动画: {animation_name}")
    
    def _execute_animation(self, animation_task: Dict):
        """执行具体动画"""
        animation_name = animation_task['name']
        duration = animation_task['duration']
        
        if animation_name in self.animations:
            animation_func = self.animations[animation_name]
            animation_func(duration)
    
    def _create_idle_animation(self, duration: float):
        """创建idle动画"""
        # 简单的呼吸效果
        for i in range(int(duration * 10)):
            time.sleep(0.1)
            # 这里可以添加轻微的大小变化
    
    def _create_happy_bounce(self, duration: float):
        """创建开心跳跃动画"""
        self.current_animation = 'happy_bounce'
        # 添加跳跃效果
        for i in range(3):
            time.sleep(0.2)
            # 这里可以添加垂直移动效果
        self.current_animation = 'idle'
    
    def _create_sad_droop(self, duration: float):
        """创建悲伤下垂动画"""
        self.current_animation = 'sad_droop'
        time.sleep(duration)
        self.current_animation = 'idle'
    
    def _create_excited_jump(self, duration: float):
        """创建兴奋跳跃动画"""
        self.current_animation = 'excited_jump'
        for i in range(5):
            time.sleep(0.1)
            # 添加快速跳跃效果
        self.current_animation = 'idle'
    
    def _create_curious_lean(self, duration: float):
        """创建好奇倾斜动画"""
        self.current_animation = 'curious_lean'
        time.sleep(duration)
        self.current_animation = 'idle'
    
    def _create_speaking_animation(self, duration: float):
        """创建说话动画"""
        self.current_animation = 'speaking'
        self.is_speaking = True
        
        # 嘴巴动画
        for i in range(int(duration * 5)):
            time.sleep(0.2)
            # 这里可以添加嘴巴张合效果
        
        self.is_speaking = False
        self.current_animation = 'idle'
    
    def _create_thinking_animation(self, duration: float):
        """创建思考动画"""
        self.current_animation = 'thinking'
        time.sleep(duration)
        self.current_animation = 'idle'
    
    def _create_dancing_animation(self, duration: float):
        """创建跳舞动画"""
        self.current_animation = 'dancing'
        for i in range(int(duration * 2)):
            time.sleep(0.5)
            # 添加舞蹈动作
        self.current_animation = 'idle'
    
    def update_with_ai_state(self, ai_state: Dict):
        """根据AI状态更新形象"""
        # 根据情绪更新表情
        emotion = ai_state.get('emotion', {}).get('emotion', 'neutral')
        if emotion != self.current_emotion:
            self.set_emotion(emotion)
        
        # 根据活动状态更新动画
        if ai_state.get('is_speaking', False) and not self.is_speaking:
            self.play_animation('speaking', 1.0)
        
        # 根据能量水平调整活跃度
        energy = ai_state.get('energy', 1.0)
        self.energy_level = energy
    
    def create_custom_avatar_from_description(self, description: str) -> Dict[str, Any]:
        """根据描述创建自定义形象"""
        # 这里可以集成Ready Player Me或其他Avatar服务
        try:
            # 模拟API调用
            custom_config = {
                'style': 'cute' if '可爱' in description else 'normal',
                'hair_color': 'brown' if '棕色' in description else 'black',
                'eye_color': 'brown' if '棕色眼睛' in description else 'black',
                'clothing': 'casual'
            }
            
            logger.info(f"根据描述创建自定义形象: {description}")
            return custom_config
            
        except Exception as e:
            logger.error(f"创建自定义形象失败: {e}")
            return {}
    
    def export_avatar_config(self) -> Dict[str, Any]:
        """导出形象配置"""
        config = {
            'avatar_config': self.avatar_config,
            'current_emotion': self.current_emotion,
            'energy_level': self.energy_level,
            'timestamp': datetime.now().isoformat()
        }
        return config
    
    def load_avatar_config(self, config: Dict[str, Any]):
        """加载形象配置"""
        try:
            self.avatar_config.update(config.get('avatar_config', {}))
            self.current_emotion = config.get('current_emotion', 'neutral')
            self.energy_level = config.get('energy_level', 1.0)
            logger.info("形象配置加载成功")
        except Exception as e:
            logger.error(f"加载形象配置失败: {e}")
    
    def get_avatar_status(self) -> Dict[str, Any]:
        """获取形象状态"""
        return {
            'current_emotion': self.current_emotion,
            'current_animation': self.current_animation,
            'is_speaking': self.is_speaking,
            'energy_level': self.energy_level,
            'window_exists': self.avatar_window is not None and 
                           (hasattr(self.avatar_window, 'winfo_exists') and self.avatar_window.winfo_exists()),
            'available_engines': {
                'ursina': URSINA_AVAILABLE,
                'matplotlib': MATPLOTLIB_AVAILABLE,
                'simple': True
            }
        }
    
    def shutdown(self):
        """关闭3D形象系统"""
        # 停止动画
        self.animation_queue.put(None)
        
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=2)
        
        # 关闭窗口
        if self.avatar_window:
            try:
                self.avatar_window.destroy()
            except:
                pass
        
        logger.info("3D形象系统已关闭")

# 全局3D形象实例
avatar_3d = Avatar3D()