"""
语音合成模块 - 让AI能说话
"""
import logging
import requests
import io
import threading
import queue
from typing import Dict, List, Optional, Any
from datetime import datetime
import random
import tempfile
import os

try:
    import pygame
    pygame.mixer.init()
except ImportError:
    pygame = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from config.settings import settings

logger = logging.getLogger(__name__)

class VoiceSynthesis:
    """语音合成系统 - 支持多种TTS服务"""
    
    def __init__(self):
        self.tts_services = {
            'openai': self._synthesize_with_openai,
            'azure': self._synthesize_with_azure,
            'elevenlabs': self._synthesize_with_elevenlabs,
            'local': self._synthesize_with_local
        }
        
        # 语音队列
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.speech_thread = None
        
        # 语音配置
        self.voice_config = {
            'speed': 1.0,
            'pitch': 1.0,
            'volume': 0.8,
            'voice_id': 'default',
            'language': 'zh-CN'
        }
        
        # 情绪语音映射
        self.emotion_voice_styles = {
            'joy': {'speed': 1.2, 'pitch': 1.1, 'style': 'cheerful'},
            'sadness': {'speed': 0.8, 'pitch': 0.9, 'style': 'sad'},
            'excitement': {'speed': 1.3, 'pitch': 1.2, 'style': 'excited'},
            'curiosity': {'speed': 1.0, 'pitch': 1.05, 'style': 'friendly'},
            'anger': {'speed': 1.1, 'pitch': 0.95, 'style': 'angry'},
            'fear': {'speed': 0.9, 'pitch': 1.1, 'style': 'nervous'}
        }
        
        # 启动语音处理线程
        self._start_speech_thread()
        
        # 初始化本地TTS引擎
        self._init_local_tts()
    
    def speak(self, text: str, emotion: str = 'neutral', priority: int = 1):
        """让AI说话"""
        if not text.strip():
            return
        
        # 添加到语音队列
        speech_item = {
            'text': text,
            'emotion': emotion,
            'priority': priority,
            'timestamp': datetime.now()
        }
        
        self.speech_queue.put(speech_item)
        logger.info(f"添加语音到队列: {text[:30]}...")
    
    def speak_immediately(self, text: str, emotion: str = 'neutral'):
        """立即说话（清空队列）"""
        # 清空当前队列
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        
        # 添加紧急语音
        self.speak(text, emotion, priority=0)
    
    def _start_speech_thread(self):
        """启动语音处理线程"""
        def speech_worker():
            while True:
                try:
                    # 获取语音任务
                    speech_item = self.speech_queue.get(timeout=1)
                    
                    if speech_item is None:  # 退出信号
                        break
                    
                    # 执行语音合成
                    self._process_speech_item(speech_item)
                    
                    self.speech_queue.task_done()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"语音处理失败: {e}")
        
        self.speech_thread = threading.Thread(target=speech_worker, daemon=True)
        self.speech_thread.start()
    
    def _process_speech_item(self, speech_item: Dict):
        """处理单个语音项目"""
        try:
            text = speech_item['text']
            emotion = speech_item['emotion']
            
            logger.info(f"开始语音合成: {text[:30]}...")
            self.is_speaking = True
            
            # 选择TTS服务
            service = self._choose_tts_service()
            
            # 调整语音风格
            voice_style = self._get_voice_style(emotion)
            
            # 执行语音合成
            synthesis_func = self.tts_services[service]
            audio_data = synthesis_func(text, voice_style)
            
            if audio_data:
                # 播放音频
                self._play_audio(audio_data, service)
            else:
                logger.warning(f"语音合成失败，使用本地TTS: {text[:30]}...")
                self._synthesize_with_local(text, voice_style)
            
        except Exception as e:
            logger.error(f"语音合成处理失败: {e}")
        finally:
            self.is_speaking = False
    
    def _choose_tts_service(self) -> str:
        """选择TTS服务"""
        # 优先级：OpenAI > ElevenLabs > Azure > Local
        if getattr(settings.ai, 'openai_api_key', ''):
            return 'openai'
        elif getattr(settings.ai, 'elevenlabs_api_key', ''):
            return 'elevenlabs'
        elif getattr(settings.ai, 'azure_speech_key', ''):
            return 'azure'
        else:
            return 'local'
    
    def _get_voice_style(self, emotion: str) -> Dict:
        """获取情绪对应的语音风格"""
        base_style = self.voice_config.copy()
        
        if emotion in self.emotion_voice_styles:
            emotion_style = self.emotion_voice_styles[emotion]
            base_style.update(emotion_style)
        
        return base_style
    
    def _synthesize_with_openai(self, text: str, voice_style: Dict) -> Optional[bytes]:
        """使用OpenAI TTS合成语音"""
        try:
            api_key = getattr(settings.ai, 'openai_api_key', '')
            if not api_key:
                return None
            
            url = "https://api.openai.com/v1/audio/speech"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # OpenAI TTS参数
            payload = {
                'model': 'tts-1',
                'input': text,
                'voice': 'nova',  # 选择声音
                'speed': voice_style.get('speed', 1.0)
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"OpenAI TTS失败: {e}")
            return None
    
    def _synthesize_with_azure(self, text: str, voice_style: Dict) -> Optional[bytes]:
        """使用Azure Speech Services合成语音"""
        try:
            api_key = getattr(settings.ai, 'azure_speech_key', '')
            region = getattr(settings.ai, 'azure_speech_region', 'eastus')
            
            if not api_key:
                return None
            
            url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
            
            headers = {
                'Ocp-Apim-Subscription-Key': api_key,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm'
            }
            
            # SSML格式
            ssml = f"""
            <speak version='1.0' xml:lang='{voice_style.get('language', 'zh-CN')}'>
                <voice xml:lang='{voice_style.get('language', 'zh-CN')}' 
                       name='zh-CN-XiaoxiaoNeural'
                       style='{voice_style.get('style', 'friendly')}'>
                    <prosody rate='{voice_style.get('speed', 1.0)}' 
                             pitch='{voice_style.get('pitch', 1.0)}'>
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            response = requests.post(url, headers=headers, data=ssml.encode('utf-8'), timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Azure TTS失败: {e}")
            return None
    
    def _synthesize_with_elevenlabs(self, text: str, voice_style: Dict) -> Optional[bytes]:
        """使用ElevenLabs合成语音"""
        try:
            api_key = getattr(settings.ai, 'elevenlabs_api_key', '')
            if not api_key:
                return None
            
            voice_id = voice_style.get('voice_id', 'pNInz6obpgDQGcFmaJgB')  # 默认声音ID
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': api_key
            }
            
            payload = {
                'text': text,
                'model_id': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.8,
                    'style': 0.5,
                    'use_speaker_boost': True
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS失败: {e}")
            return None
    
    def _synthesize_with_local(self, text: str, voice_style: Dict) -> Optional[bytes]:
        """使用本地TTS引擎"""
        try:
            if pyttsx3 is None:
                logger.warning("pyttsx3未安装，无法使用本地TTS")
                return None
            
            engine = pyttsx3.init()
            
            # 设置语音参数
            engine.setProperty('rate', int(200 * voice_style.get('speed', 1.0)))
            engine.setProperty('volume', voice_style.get('volume', 0.8))
            
            # 尝试设置中文语音
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 保存音频文件
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # 读取音频数据
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # 清理临时文件
            os.unlink(temp_path)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"本地TTS失败: {e}")
            return None
    
    def _init_local_tts(self):
        """初始化本地TTS引擎"""
        try:
            if pyttsx3 is not None:
                # 测试本地TTS引擎
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                logger.info(f"本地TTS引擎初始化成功，可用语音数: {len(voices) if voices else 0}")
        except Exception as e:
            logger.warning(f"本地TTS引擎初始化失败: {e}")
    
    def _play_audio(self, audio_data: bytes, service: str):
        """播放音频数据"""
        try:
            if pygame is None:
                logger.warning("pygame未安装，无法播放音频")
                return
            
            # 使用pygame播放音频
            audio_file = io.BytesIO(audio_data)
            
            if service in ['openai', 'elevenlabs']:
                # MP3格式
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                
                # 等待播放完成
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
            else:
                # WAV格式
                sound = pygame.mixer.Sound(audio_file)
                sound.play()
                
                # 等待播放完成
                while pygame.mixer.get_busy():
                    pygame.time.wait(100)
            
        except Exception as e:
            logger.error(f"音频播放失败: {e}")
    
    def set_voice_config(self, **kwargs):
        """设置语音配置"""
        self.voice_config.update(kwargs)
        logger.info(f"语音配置已更新: {kwargs}")
    
    def stop_speaking(self):
        """停止当前语音"""
        try:
            if pygame:
                pygame.mixer.music.stop()
                pygame.mixer.stop()
            
            # 清空队列
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                except queue.Empty:
                    break
            
            self.is_speaking = False
            logger.info("语音播放已停止")
            
        except Exception as e:
            logger.error(f"停止语音失败: {e}")
    
    def get_voice_status(self) -> Dict[str, Any]:
        """获取语音状态"""
        return {
            'is_speaking': self.is_speaking,
            'queue_size': self.speech_queue.qsize(),
            'current_service': self._choose_tts_service(),
            'voice_config': self.voice_config,
            'supported_services': list(self.tts_services.keys())
        }
    
    def test_voice(self, text: str = "你好，我是智能小生命！"):
        """测试语音功能"""
        self.speak(text, emotion='joy')
        return "语音测试已启动"
    
    def add_personality_to_speech(self, text: str, personality_traits: Dict) -> str:
        """为语音添加性格特色"""
        # 根据性格特征调整语音内容
        playfulness = personality_traits.get('playfulness', 0.5)
        
        if playfulness > 0.7:
            # 调皮的语音风格
            if random.random() < 0.3:
                text = text + "～嘿嘿！"
            elif random.random() < 0.2:
                text = "呐呐呐，" + text
        
        return text
    
    def shutdown(self):
        """关闭语音合成系统"""
        self.stop_speaking()
        
        # 发送退出信号
        self.speech_queue.put(None)
        
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=2)
        
        logger.info("语音合成系统已关闭")

# 全局语音合成实例
voice_synthesis = VoiceSynthesis()