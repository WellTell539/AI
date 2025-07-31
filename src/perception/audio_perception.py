"""
音频感知模块 - 处理麦克风输入和语音识别
"""
import logging
import threading
import time
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import queue

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

from config.settings import settings

logger = logging.getLogger(__name__)

class AudioPerception:
    """
    音频感知系统 - 负责声音捕获、语音识别和音频分析
    """
    
    def __init__(self):
        self.is_active = False
        self.audio_stream = None
        self.recognizer = None
        self.microphone = None
        
        # 音频数据
        self.current_audio_data = None
        self.audio_history = []
        self.max_history_length = 50
        
        # 分析结果
        self.sound_detected = False
        self.voice_detected = False
        self.last_speech_text = ""
        self.ambient_noise_level = 0.0
        
        # 线程控制
        self.listening_thread = None
        self.should_stop = False
        self.audio_queue = queue.Queue()
        
        # 回调函数
        self.speech_callback: Optional[Callable] = None
        self.sound_callback: Optional[Callable] = None
        
        # 初始化
        self._initialize_audio_tools()
    
    def _initialize_audio_tools(self):
        """初始化音频工具"""
        if not settings.perception.microphone_enabled:
            logger.info("麦克风功能已禁用")
            return
        
        try:
            if sr is None:
                logger.error("speech_recognition模块未安装")
                return
                
            # 初始化语音识别器
            self.recognizer = sr.Recognizer()
            
            # 初始化麦克风
            if pyaudio:
                self.microphone = sr.Microphone()
                
                # 调整环境噪音
                with self.microphone as source:
                    logger.info("调整环境噪音...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    self.ambient_noise_level = self.recognizer.energy_threshold
                
                logger.info(f"音频工具初始化成功，噪音阈值: {self.ambient_noise_level}")
            else:
                logger.warning("pyaudio模块未安装，某些功能可能不可用")
                
        except Exception as e:
            logger.error(f"音频工具初始化失败: {e}")
    
    def start_listening(self, speech_callback: Optional[Callable] = None, 
                       sound_callback: Optional[Callable] = None) -> bool:
        """
        开始监听音频
        
        Args:
            speech_callback: 语音识别回调函数
            sound_callback: 声音检测回调函数
        """
        if not settings.perception.microphone_enabled:
            logger.info("麦克风功能已禁用")
            return False
            
        if self.recognizer is None or self.microphone is None:
            logger.error("音频工具未正确初始化")
            return False
        
        try:
            self.speech_callback = speech_callback
            self.sound_callback = sound_callback
            self.is_active = True
            self.should_stop = False
            
            # 启动监听线程
            self.listening_thread = threading.Thread(target=self._listening_loop, daemon=True)
            self.listening_thread.start()
            
            logger.info("开始音频监听")
            return True
            
        except Exception as e:
            logger.error(f"启动音频监听失败: {e}")
            return False
    
    def stop_listening(self):
        """停止音频监听"""
        self.should_stop = True
        self.is_active = False
        
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=5)
        
        logger.info("音频监听已停止")
    
    def _listening_loop(self):
        """音频监听循环"""
        while not self.should_stop and self.is_active:
            try:
                # 监听音频
                with self.microphone as source:
                    # 短时间监听，避免阻塞太久
                    try:
                        audio_data = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        self._process_audio(audio_data)
                    except sr.WaitTimeoutError:
                        # 超时是正常的，继续下一次循环
                        continue
                    
            except Exception as e:
                logger.error(f"音频监听出错: {e}")
                time.sleep(1)
    
    def _process_audio(self, audio_data):
        """处理音频数据"""
        try:
            # 更新音频数据
            self.current_audio_data = audio_data
            self._add_to_history(audio_data)
            
            # 检测声音
            self._detect_sound(audio_data)
            
            # 异步进行语音识别（避免阻塞主循环）
            threading.Thread(target=self._recognize_speech, args=(audio_data,), daemon=True).start()
            
        except Exception as e:
            logger.error(f"处理音频数据失败: {e}")
    
    def _add_to_history(self, audio_data):
        """添加音频数据到历史记录"""
        timestamp = datetime.now()
        self.audio_history.append({
            'audio_data': audio_data,
            'timestamp': timestamp
        })
        
        # 保持历史长度
        if len(self.audio_history) > self.max_history_length:
            self.audio_history.pop(0)
    
    def _detect_sound(self, audio_data):
        """检测声音存在"""
        try:
            # 简单的音量检测
            if hasattr(audio_data, 'frame_data'):
                # 计算音频能量
                audio_array = np.frombuffer(audio_data.frame_data, dtype=np.int16)
                energy = np.sqrt(np.mean(audio_array**2))
                
                # 如果能量超过阈值，认为检测到声音
                if energy > settings.perception.audio_threshold * 1000:
                    self.sound_detected = True
                    logger.debug(f"检测到声音，能量: {energy:.2f}")
                    
                    # 调用声音回调
                    if self.sound_callback:
                        threading.Thread(target=self.sound_callback, args=(energy,), daemon=True).start()
                else:
                    self.sound_detected = False
            
        except Exception as e:
            logger.error(f"声音检测失败: {e}")
    
    def _recognize_speech(self, audio_data):
        """识别语音内容"""
        try:
            # 使用Google语音识别
            text = self.recognizer.recognize_google(audio_data, language='zh-CN')
            
            if text:
                self.voice_detected = True
                self.last_speech_text = text
                logger.info(f"识别到语音: {text}")
                
                # 调用语音回调
                if self.speech_callback:
                    self.speech_callback(text)
            
        except sr.UnknownValueError:
            # 无法识别语音内容，但可能有声音
            logger.debug("检测到声音但无法识别内容")
            self.voice_detected = False
            
        except sr.RequestError as e:
            logger.error(f"语音识别请求失败: {e}")
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
    
    def recognize_speech_once(self) -> Optional[str]:
        """单次语音识别"""
        if not self.is_active or self.recognizer is None or self.microphone is None:
            return None
        
        try:
            logger.info("请说话...")
            with self.microphone as source:
                audio_data = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            text = self.recognizer.recognize_google(audio_data, language='zh-CN')
            logger.info(f"识别到: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.info("等待超时，未检测到语音")
            return None
            
        except sr.UnknownValueError:
            logger.info("无法识别语音内容")
            return None
            
        except sr.RequestError as e:
            logger.error(f"语音识别请求失败: {e}")
            return None
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return None
    
    def analyze_audio_environment(self) -> Dict[str, Any]:
        """分析音频环境"""
        if not self.is_active:
            return {"status": "inactive", "message": "音频监听未启动"}
        
        try:
            analysis = {
                "timestamp": datetime.now(),
                "status": "active",
                "sound_detected": self.sound_detected,
                "voice_detected": self.voice_detected,
                "last_speech": self.last_speech_text,
                "ambient_noise_level": self.ambient_noise_level,
                "audio_activity": self._calculate_audio_activity(),
                "environment_description": ""
            }
            
            # 生成环境描述
            description_parts = []
            
            if self.voice_detected and self.last_speech_text:
                description_parts.append(f"听到了语音：{self.last_speech_text}")
            elif self.sound_detected:
                description_parts.append("听到了声音")
            
            activity = analysis["audio_activity"]
            if activity > 0.7:
                description_parts.append("环境很嘈杂")
            elif activity > 0.3:
                description_parts.append("环境有一定声音")
            else:
                description_parts.append("环境比较安静")
            
            if description_parts:
                analysis["environment_description"] = "，".join(description_parts)
            else:
                analysis["environment_description"] = "环境安静"
            
            return analysis
            
        except Exception as e:
            logger.error(f"音频环境分析失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_audio_activity(self) -> float:
        """计算音频活动水平"""
        if not self.audio_history:
            return 0.0
        
        try:
            # 计算最近一段时间的音频活动
            recent_count = 0
            total_count = 0
            cutoff_time = datetime.now().timestamp() - 60  # 最近1分钟
            
            for record in self.audio_history:
                if record['timestamp'].timestamp() > cutoff_time:
                    total_count += 1
                    if self._has_significant_audio(record['audio_data']):
                        recent_count += 1
            
            if total_count > 0:
                return recent_count / total_count
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算音频活动失败: {e}")
            return 0.0
    
    def _has_significant_audio(self, audio_data) -> bool:
        """判断音频数据是否包含显著声音"""
        try:
            if hasattr(audio_data, 'frame_data'):
                audio_array = np.frombuffer(audio_data.frame_data, dtype=np.int16)
                energy = np.sqrt(np.mean(audio_array**2))
                return energy > self.ambient_noise_level * 1.5
            return False
        except Exception:
            return False
    
    def detect_audio_changes(self) -> List[str]:
        """检测音频环境变化"""
        changes = []
        
        # 检测声音状态变化
        if hasattr(self, '_prev_sound_detected'):
            if self.sound_detected != self._prev_sound_detected:
                if self.sound_detected:
                    changes.append("开始检测到声音")
                else:
                    changes.append("环境变安静了")
        self._prev_sound_detected = self.sound_detected
        
        # 检测语音状态变化
        if hasattr(self, '_prev_voice_detected'):
            if self.voice_detected != self._prev_voice_detected:
                if self.voice_detected:
                    changes.append("检测到有人说话")
                else:
                    changes.append("说话声停止了")
        self._prev_voice_detected = self.voice_detected
        
        # 检测新的语音内容
        if hasattr(self, '_prev_speech_text'):
            if self.last_speech_text != self._prev_speech_text and self.last_speech_text:
                changes.append(f"听到新的话：{self.last_speech_text}")
        self._prev_speech_text = self.last_speech_text
        
        return changes
    
    def get_audio_summary(self) -> Dict[str, Any]:
        """获取音频感知摘要"""
        return {
            "microphone_active": self.is_active,
            "sound_detected": self.sound_detected,
            "voice_detected": self.voice_detected,
            "last_speech": self.last_speech_text,
            "ambient_noise_level": self.ambient_noise_level,
            "audio_history_count": len(self.audio_history)
        }
    
    def adjust_sensitivity(self, sensitivity: float):
        """调整听力敏感度"""
        if self.recognizer:
            # 调整能量阈值
            self.recognizer.energy_threshold = self.ambient_noise_level * sensitivity
            logger.info(f"音频敏感度调整为: {sensitivity}, 新阈值: {self.recognizer.energy_threshold}")
    
    def __del__(self):
        """析构函数"""
        self.stop_listening()