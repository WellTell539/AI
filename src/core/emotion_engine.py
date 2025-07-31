"""
情绪引擎 - 管理智能生命体的情感状态
"""
import time
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EmotionType(Enum):
    """情绪类型"""
    JOY = "joy"           # 快乐
    SADNESS = "sadness"   # 悲伤
    ANGER = "anger"       # 愤怒
    FEAR = "fear"         # 恐惧
    SURPRISE = "surprise" # 惊讶
    DISGUST = "disgust"   # 厌恶
    CURIOSITY = "curiosity" # 好奇
    EXCITEMENT = "excitement" # 兴奋
    LONELINESS = "loneliness" # 孤独
    CONTENTMENT = "contentment" # 满足

@dataclass
class EmotionState:
    """情绪状态"""
    emotion: EmotionType
    intensity: float  # 0.0 - 1.0
    duration: float   # 持续时间（秒）
    timestamp: datetime
    triggers: List[str] = None
    
    def __post_init__(self):
        if self.triggers is None:
            self.triggers = []

@dataclass
class EmotionTrigger:
    """情绪触发器"""
    trigger_type: str
    emotion_effect: EmotionType
    intensity_change: float
    duration: float
    source: str = "unknown"

class EmotionEngine:
    """
    情绪引擎 - 负责管理和模拟情感状态
    """
    
    def __init__(self):
        # 当前情绪状态
        self.current_emotions: Dict[EmotionType, EmotionState] = {}
        
        # 基础情绪（性格决定的默认情绪倾向）
        self.base_emotions = {
            EmotionType.CURIOSITY: 0.7,   # 基础好奇心
            EmotionType.JOY: 0.5,         # 基础快乐
            EmotionType.EXCITEMENT: 0.4,   # 基础兴奋
            EmotionType.LONELINESS: 0.3,   # 基础孤独感
        }
        
        # 情绪衰减速度（每秒）
        self.decay_rates = {
            EmotionType.JOY: 0.02,
            EmotionType.SADNESS: 0.015,
            EmotionType.ANGER: 0.03,
            EmotionType.FEAR: 0.025,
            EmotionType.SURPRISE: 0.05,
            EmotionType.DISGUST: 0.02,
            EmotionType.CURIOSITY: 0.01,
            EmotionType.EXCITEMENT: 0.03,
            EmotionType.LONELINESS: 0.005,
            EmotionType.CONTENTMENT: 0.01,
        }
        
        # 情绪相互影响矩阵
        self.emotion_interactions = {
            EmotionType.JOY: {
                EmotionType.SADNESS: -0.3,
                EmotionType.ANGER: -0.2,
                EmotionType.FEAR: -0.2,
                EmotionType.LONELINESS: -0.4,
                EmotionType.EXCITEMENT: 0.2,
            },
            EmotionType.SADNESS: {
                EmotionType.JOY: -0.3,
                EmotionType.EXCITEMENT: -0.3,
                EmotionType.CURIOSITY: -0.1,
                EmotionType.LONELINESS: 0.2,
            },
            EmotionType.CURIOSITY: {
                EmotionType.EXCITEMENT: 0.2,
                EmotionType.JOY: 0.1,
                EmotionType.SADNESS: -0.1,
            },
            EmotionType.EXCITEMENT: {
                EmotionType.JOY: 0.2,
                EmotionType.CURIOSITY: 0.1,
                EmotionType.LONELINESS: -0.2,
            },
            EmotionType.LONELINESS: {
                EmotionType.JOY: -0.2,
                EmotionType.SADNESS: 0.2,
                EmotionType.EXCITEMENT: -0.1,
            }
        }
        
        # 情绪记忆（记录最近的情绪变化）
        self.emotion_history: List[EmotionState] = []
        self.max_history_length = 50
        
        # 初始化基础情绪
        self._initialize_base_emotions()
    
    def _initialize_base_emotions(self):
        """初始化基础情绪状态"""
        for emotion_type, intensity in self.base_emotions.items():
            self.current_emotions[emotion_type] = EmotionState(
                emotion=emotion_type,
                intensity=intensity,
                duration=float('inf'),  # 基础情绪持续存在
                timestamp=datetime.now(),
                triggers=["initialization"]
            )
    
    def process_trigger(self, trigger: Dict):
        """
        处理情绪触发器
        
        Args:
            trigger: 触发器信息 {"type": str, "intensity": float, "source": str}
        """
        try:
            # 解析触发器
            emotion_type = EmotionType(trigger.get("type", "curiosity"))
            intensity = max(0.0, min(1.0, trigger.get("intensity", 0.5)))
            source = trigger.get("source", "unknown")
            duration = trigger.get("duration", 300)  # 默认5分钟
            
            # 更新或创建情绪状态
            if emotion_type in self.current_emotions:
                # 情绪强度叠加（但不超过1.0）
                current_intensity = self.current_emotions[emotion_type].intensity
                new_intensity = min(1.0, current_intensity + intensity)
                
                self.current_emotions[emotion_type].intensity = new_intensity
                self.current_emotions[emotion_type].duration = max(
                    self.current_emotions[emotion_type].duration, 
                    duration
                )
                self.current_emotions[emotion_type].triggers.append(source)
            else:
                # 创建新的情绪状态
                self.current_emotions[emotion_type] = EmotionState(
                    emotion=emotion_type,
                    intensity=intensity,
                    duration=duration,
                    timestamp=datetime.now(),
                    triggers=[source]
                )
            
            # 记录到历史
            self._add_to_history(self.current_emotions[emotion_type])
            
            # 处理情绪相互影响
            self._apply_emotion_interactions(emotion_type, intensity)
            
            logger.debug(f"情绪触发: {emotion_type.value} (强度: {intensity:.2f}, 来源: {source})")
            
        except Exception as e:
            logger.error(f"处理情绪触发器失败: {e}")
    
    def _apply_emotion_interactions(self, triggered_emotion: EmotionType, intensity: float):
        """应用情绪相互影响"""
        if triggered_emotion not in self.emotion_interactions:
            return
        
        interactions = self.emotion_interactions[triggered_emotion]
        
        for affected_emotion, effect_strength in interactions.items():
            if affected_emotion in self.current_emotions:
                # 计算影响强度
                influence = intensity * effect_strength
                
                # 应用影响
                current_intensity = self.current_emotions[affected_emotion].intensity
                new_intensity = max(0.0, min(1.0, current_intensity + influence))
                
                self.current_emotions[affected_emotion].intensity = new_intensity
                
                logger.debug(f"情绪影响: {triggered_emotion.value} -> {affected_emotion.value} ({influence:+.2f})")
    
    def update(self):
        """更新情绪状态（情绪衰减和自然变化）"""
        current_time = datetime.now()
        emotions_to_remove = []
        
        for emotion_type, emotion_state in self.current_emotions.items():
            # 计算时间差
            time_diff = (current_time - emotion_state.timestamp).total_seconds()
            
            # 检查是否超过持续时间
            if emotion_state.duration != float('inf') and time_diff >= emotion_state.duration:
                emotions_to_remove.append(emotion_type)
                continue
            
            # 应用情绪衰减（除非是基础情绪）
            if emotion_type in self.base_emotions:
                # 基础情绪趋向于默认值
                target_intensity = self.base_emotions[emotion_type]
                if emotion_state.intensity > target_intensity:
                    decay_rate = self.decay_rates.get(emotion_type, 0.02)
                    emotion_state.intensity = max(
                        target_intensity,
                        emotion_state.intensity - decay_rate
                    )
                elif emotion_state.intensity < target_intensity:
                    # 基础情绪恢复
                    emotion_state.intensity = min(
                        target_intensity,
                        emotion_state.intensity + 0.01
                    )
            else:
                # 非基础情绪自然衰减
                decay_rate = self.decay_rates.get(emotion_type, 0.02)
                emotion_state.intensity -= decay_rate
                
                if emotion_state.intensity <= 0.0:
                    emotions_to_remove.append(emotion_type)
        
        # 移除已经消失的情绪
        for emotion_type in emotions_to_remove:
            del self.current_emotions[emotion_type]
            logger.debug(f"情绪消失: {emotion_type.value}")
        
        # 随机情绪波动（模拟自然的情绪变化）
        self._apply_random_fluctuations()
        
        # 更新时间戳
        for emotion_state in self.current_emotions.values():
            emotion_state.timestamp = current_time
    
    def _apply_random_fluctuations(self):
        """应用随机情绪波动"""
        # 小概率触发随机情绪变化
        if random.random() < 0.1:  # 10%概率
            fluctuation_emotions = [
                EmotionType.CURIOSITY,
                EmotionType.EXCITEMENT,
                EmotionType.CONTENTMENT,
                EmotionType.LONELINESS
            ]
            
            emotion = random.choice(fluctuation_emotions)
            intensity = random.uniform(0.1, 0.3)
            
            self.process_trigger({
                "type": emotion.value,
                "intensity": intensity,
                "source": "natural_fluctuation",
                "duration": random.uniform(60, 300)
            })
    
    def get_current_emotion(self) -> Dict:
        """获取当前主导情绪"""
        if not self.current_emotions:
            return {
                "emotion": "neutral",
                "intensity": 0.0,
                "secondary_emotions": []
            }
        
        # 找出强度最高的情绪作为主导情绪
        dominant_emotion = max(
            self.current_emotions.values(),
            key=lambda e: e.intensity
        )
        
        # 获取次要情绪（强度大于0.3的其他情绪）
        secondary_emotions = [
            {"emotion": e.emotion.value, "intensity": e.intensity}
            for e in self.current_emotions.values()
            if e.intensity >= 0.3 and e.emotion != dominant_emotion.emotion
        ]
        
        return {
            "emotion": dominant_emotion.emotion.value,
            "intensity": dominant_emotion.intensity,
            "secondary_emotions": secondary_emotions,
            "triggers": dominant_emotion.triggers[-3:],  # 最近3个触发源
        }
    
    def get_emotion_description(self) -> str:
        """获取情绪状态的文字描述"""
        current = self.get_current_emotion()
        emotion = current["emotion"]
        intensity = current["intensity"]
        
        # 情绪强度描述
        if intensity >= 0.8:
            intensity_desc = "非常"
        elif intensity >= 0.6:
            intensity_desc = "很"
        elif intensity >= 0.4:
            intensity_desc = "有点"
        elif intensity >= 0.2:
            intensity_desc = "稍微"
        else:
            intensity_desc = "一点点"
        
        # 情绪名称映射
        emotion_names = {
            "joy": "开心",
            "sadness": "难过",
            "anger": "生气",
            "fear": "害怕",
            "surprise": "惊讶",
            "disgust": "厌恶",
            "curiosity": "好奇",
            "excitement": "兴奋",
            "loneliness": "孤独",
            "contentment": "满足",
            "neutral": "平静"
        }
        
        emotion_name = emotion_names.get(emotion, emotion)
        
        description = f"{intensity_desc}{emotion_name}"
        
        # 添加次要情绪
        if current["secondary_emotions"]:
            secondary = current["secondary_emotions"][0]
            secondary_name = emotion_names.get(secondary["emotion"], secondary["emotion"])
            description += f"，还有点{secondary_name}"
        
        return description
    
    def get_all_emotions(self) -> Dict[str, float]:
        """获取所有当前情绪及其强度"""
        return {
            emotion.emotion.value: emotion.intensity
            for emotion in self.current_emotions.values()
        }
    
    def _add_to_history(self, emotion_state: EmotionState):
        """添加情绪状态到历史记录"""
        # 复制情绪状态（避免引用问题）
        history_state = EmotionState(
            emotion=emotion_state.emotion,
            intensity=emotion_state.intensity,
            duration=emotion_state.duration,
            timestamp=emotion_state.timestamp,
            triggers=emotion_state.triggers.copy()
        )
        
        self.emotion_history.append(history_state)
        
        # 保持历史长度
        if len(self.emotion_history) > self.max_history_length:
            self.emotion_history = self.emotion_history[-self.max_history_length:]
    
    def get_emotion_trend(self, emotion_type: EmotionType, hours: int = 1) -> List[float]:
        """获取指定情绪在过去一段时间内的变化趋势"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        relevant_history = [
            state for state in self.emotion_history
            if state.emotion == emotion_type and state.timestamp >= cutoff_time
        ]
        
        return [state.intensity for state in relevant_history]
    
    def simulate_sleep_emotions(self):
        """模拟睡眠时的情绪状态"""
        # 降低所有情绪强度
        for emotion_state in self.current_emotions.values():
            emotion_state.intensity *= 0.8
        
        # 增加平静感
        self.process_trigger({
            "type": "contentment",
            "intensity": 0.4,
            "source": "sleep",
            "duration": 600
        })
    
    def simulate_wake_up_emotions(self):
        """模拟醒来时的情绪状态"""
        # 恢复基础情绪
        for emotion_type, base_intensity in self.base_emotions.items():
            if emotion_type in self.current_emotions:
                self.current_emotions[emotion_type].intensity = base_intensity
        
        # 添加清醒的好奇心
        self.process_trigger({
            "type": "curiosity",
            "intensity": 0.6,
            "source": "wake_up",
            "duration": 1800
        })