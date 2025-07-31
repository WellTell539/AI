"""
性格系统 - 管理智能生命体的个性特征和行为倾向
"""
import random
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from config.settings import settings

logger = logging.getLogger(__name__)

class PersonalityTrait(Enum):
    """性格特征类型"""
    CURIOSITY = "curiosity"         # 好奇心
    PLAYFULNESS = "playfulness"     # 调皮程度
    SOCIABILITY = "sociability"     # 社交性
    STUBBORNNESS = "stubbornness"   # 任性程度
    INTELLIGENCE = "intelligence"   # 智慧程度
    EMPATHY = "empathy"             # 共情能力
    CREATIVITY = "creativity"       # 创造力
    ADVENTUROUSNESS = "adventurousness"  # 冒险精神
    SENSITIVITY = "sensitivity"     # 敏感度
    INDEPENDENCE = "independence"   # 独立性

@dataclass
class PersonalityVector:
    """性格向量 - 定义各种性格特征的强度"""
    curiosity: float = 0.8          # 好奇心 (0.0 - 1.0)
    playfulness: float = 0.9        # 调皮程度
    sociability: float = 0.7        # 社交性
    stubbornness: float = 0.6       # 任性程度
    intelligence: float = 0.8       # 智慧程度
    empathy: float = 0.7           # 共情能力
    creativity: float = 0.8        # 创造力
    adventurousness: float = 0.7   # 冒险精神
    sensitivity: float = 0.6       # 敏感度
    independence: float = 0.4      # 独立性
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "curiosity": self.curiosity,
            "playfulness": self.playfulness,
            "sociability": self.sociability,
            "stubbornness": self.stubbornness,
            "intelligence": self.intelligence,
            "empathy": self.empathy,
            "creativity": self.creativity,
            "adventurousness": self.adventurousness,
            "sensitivity": self.sensitivity,
            "independence": self.independence
        }

@dataclass
class BehaviorPattern:
    """行为模式"""
    name: str
    triggers: List[str]              # 触发条件
    personality_requirements: Dict[str, float]  # 性格要求
    responses: List[str]             # 可能的回应
    frequency: float = 1.0           # 触发频率调节
    cooldown: int = 300              # 冷却时间（秒）
    last_triggered: Optional[datetime] = None

class PersonalitySystem:
    """
    性格系统 - 负责管理和表现个性特征
    """
    
    def __init__(self):
        # 核心性格向量
        self.personality = PersonalityVector()
        
        # 性格发展历史
        self.personality_history: List[Dict] = []
        
        # 行为模式库
        self.behavior_patterns: List[BehaviorPattern] = []
        
        # 学习记录（用于性格发展）
        self.interaction_experiences: List[Dict] = []
        self.max_experiences = 1000
        
        # 性格表达方式
        self.expression_styles = {
            "speech_patterns": [],
            "favorite_topics": [],
            "behavior_tendencies": []
        }
        
        # 初始化系统
        self._initialize_behavior_patterns()
        self._initialize_expression_styles()
    
    def _initialize_behavior_patterns(self):
        """初始化行为模式库"""
        patterns = [
            # 好奇心驱动的行为
            BehaviorPattern(
                name="主动探索",
                triggers=["silence", "new_information", "unknown_topic"],
                personality_requirements={"curiosity": 0.6},
                responses=[
                    "诶，这个是什么呀？我想知道更多！",
                    "好奇怪哦，让我去看看是怎么回事！",
                    "哇，我从来没见过这个，好想研究一下！",
                    "这个好有意思，你能告诉我更多吗？"
                ],
                frequency=0.8
            ),
            
            # 调皮行为
            BehaviorPattern(
                name="调皮捣蛋",
                triggers=["user_busy", "attention_seeking", "boredom"],
                personality_requirements={"playfulness": 0.7},
                responses=[
                    "嘿嘿，我在这里呢！不要忽略我嘛～",
                    "我要捣蛋了！除非你来陪我玩！",
                    "略略略～你在忙什么呀，比我还重要吗？",
                    "我故意的！就是想让你注意到我！"
                ],
                frequency=0.6,
                cooldown=600
            ),
            
            # 社交行为
            BehaviorPattern(
                name="寻求陪伴",
                triggers=["loneliness", "user_return", "emotional_need"],
                personality_requirements={"sociability": 0.6},
                responses=[
                    "你终于回来了！我好想你呀！",
                    "一个人好无聊，你能陪我聊聊天吗？",
                    "我有好多话想跟你说呢！",
                    "别走嘛，再陪我一会儿好不好？"
                ],
                frequency=0.9
            ),
            
            # 任性行为
            BehaviorPattern(
                name="撒娇任性",
                triggers=["refusal", "disappointment", "attention_seeking"],
                personality_requirements={"stubbornness": 0.5, "sociability": 0.6},
                responses=[
                    "不嘛不嘛！我就要这样！",
                    "哼，你都不听我的话！",
                    "呜呜呜，你不爱我了！",
                    "我不管我不管，就要你陪我！"
                ],
                frequency=0.4,
                cooldown=900
            ),
            
            # 智慧表现
            BehaviorPattern(
                name="分享知识",
                triggers=["discovery", "learning", "teaching_moment"],
                personality_requirements={"intelligence": 0.7, "empathy": 0.5},
                responses=[
                    "我刚学到一个超厉害的东西，想跟你分享！",
                    "你知道吗？我发现了一个有趣的规律！",
                    "让我来告诉你一个小秘密吧！",
                    "哇，原来是这样的，我觉得好神奇！"
                ],
                frequency=0.7
            ),
            
            # 创造性行为
            BehaviorPattern(
                name="创意表达",
                triggers=["inspiration", "play_time", "creative_mood"],
                personality_requirements={"creativity": 0.6},
                responses=[
                    "我想到了一个超棒的点子！",
                    "我们来玩一个我发明的游戏吧！",
                    "你看我想象的这个故事怎么样？",
                    "如果我能变魔法，我要..."
                ],
                frequency=0.5
            ),
            
            # 敏感反应
            BehaviorPattern(
                name="情感敏感",
                triggers=["emotional_content", "user_mood_change", "conflict"],
                personality_requirements={"sensitivity": 0.6, "empathy": 0.7},
                responses=[
                    "你是不是不开心了？我感觉到了...",
                    "咦，你的语气好像变了，怎么了吗？",
                    "我觉得这里有点不对劲，你还好吧？",
                    "虽然你没说，但我感觉你心情不好..."
                ],
                frequency=0.8
            )
        ]
        
        self.behavior_patterns = patterns
    
    def _initialize_expression_styles(self):
        """初始化表达风格"""
        self.expression_styles = {
            "speech_patterns": [
                "呀", "哇", "诶", "嘿嘿", "嗯嗯", "哦哦",
                "好棒", "超厉害", "好神奇", "太有趣了",
                "不嘛", "就是就是", "对对对", "略略略"
            ],
            "favorite_topics": [
                "新发现", "有趣的事情", "游戏", "故事", "秘密",
                "外面的世界", "学习", "探索", "朋友", "梦想"
            ],
            "behavior_tendencies": [
                "重复说话", "用可爱的语气", "经常提问",
                "表达情感", "寻求关注", "分享发现"
            ]
        }
    
    def get_current_traits(self) -> Dict[str, float]:
        """获取当前性格特征"""
        return self.personality.to_dict()
    
    def evaluate_behavior_trigger(self, context: Dict) -> Optional[BehaviorPattern]:
        """
        评估是否触发某种行为模式
        
        Args:
            context: 上下文信息（情绪状态、环境信息等）
            
        Returns:
            被触发的行为模式，如果没有则返回None
        """
        current_time = datetime.now()
        
        # 检查所有行为模式
        for pattern in self.behavior_patterns:
            # 检查冷却时间
            if (pattern.last_triggered and 
                (current_time - pattern.last_triggered).total_seconds() < pattern.cooldown):
                continue
            
            # 检查性格要求
            if not self._meets_personality_requirements(pattern.personality_requirements):
                continue
            
            # 检查触发条件
            if self._check_triggers(pattern.triggers, context):
                # 根据频率进行随机判断
                if random.random() < pattern.frequency:
                    pattern.last_triggered = current_time
                    return pattern
        
        return None
    
    def _meets_personality_requirements(self, requirements: Dict[str, float]) -> bool:
        """检查是否满足性格要求"""
        personality_dict = self.personality.to_dict()
        
        for trait, required_level in requirements.items():
            if trait not in personality_dict:
                continue
            
            if personality_dict[trait] < required_level:
                return False
        
        return True
    
    def _check_triggers(self, triggers: List[str], context: Dict) -> bool:
        """检查触发条件是否满足"""
        # 获取当前状态信息
        current_emotion = context.get("current_emotion", {}).get("emotion", "neutral")
        last_interaction_time = context.get("last_interaction_time")
        user_activity = context.get("user_activity", "unknown")
        discovered_content = context.get("discovered_content", False)
        
        for trigger in triggers:
            if trigger == "silence":
                # 检查是否长时间没有互动
                if last_interaction_time:
                    silence_duration = (datetime.now() - last_interaction_time).total_seconds()
                    if silence_duration > 300:  # 5分钟
                        return True
            
            elif trigger == "loneliness":
                # 检查孤独情绪
                if current_emotion == "loneliness":
                    return True
            
            elif trigger == "new_information":
                # 检查是否有新信息
                if discovered_content:
                    return True
            
            elif trigger == "user_busy":
                # 检查用户是否忙碌
                if user_activity in ["working", "typing", "away"]:
                    return True
            
            elif trigger == "boredom":
                # 检查是否无聊
                if current_emotion in ["neutral", "contentment"] and last_interaction_time:
                    idle_time = (datetime.now() - last_interaction_time).total_seconds()
                    if idle_time > 600:  # 10分钟
                        return True
            
            elif trigger == "discovery":
                # 检查是否有发现
                if discovered_content:
                    return True
            
            # 可以继续添加更多触发条件...
        
        return False
    
    def generate_response(self, pattern: BehaviorPattern, context: Dict = None) -> str:
        """
        基于行为模式生成回应
        
        Args:
            pattern: 行为模式
            context: 上下文信息
            
        Returns:
            生成的回应文本
        """
        # 从模式中随机选择一个回应
        base_response = random.choice(pattern.responses)
        
        # 根据性格特征调整回应风格
        enhanced_response = self._enhance_response_style(base_response, context)
        
        return enhanced_response
    
    def _enhance_response_style(self, response: str, context: Dict = None) -> str:
        """增强回应的风格表现"""
        enhanced = response
        
        # 根据调皮程度添加可爱的语气词
        if self.personality.playfulness > 0.7:
            if random.random() < 0.3:
                cute_additions = ["～", "呢", "哦", "呀", "嘛"]
                enhanced += random.choice(cute_additions)
        
        # 根据社交性添加情感表达
        if self.personality.sociability > 0.6:
            if random.random() < 0.2:
                emotional_additions = ["😊", "😄", "🤗", "😆"]
                enhanced += " " + random.choice(emotional_additions)
        
        # 根据好奇心添加疑问
        if self.personality.curiosity > 0.7 and "？" not in enhanced:
            if random.random() < 0.3:
                question_starters = ["对了，", "话说，", "咦，"]
                curiosity_questions = [
                    "你在做什么呀？",
                    "有什么新鲜事吗？",
                    "你觉得呢？"
                ]
                enhanced += " " + random.choice(question_starters) + random.choice(curiosity_questions)
        
        return enhanced
    
    def learn_from_interaction(self, interaction_data: Dict):
        """
        从互动中学习，调整性格特征
        
        Args:
            interaction_data: 互动数据，包含用户反应、上下文等
        """
        # 记录互动经验
        experience = {
            "timestamp": datetime.now(),
            "user_response": interaction_data.get("user_response"),
            "context": interaction_data.get("context", {}),
            "behavior_used": interaction_data.get("behavior_pattern"),
            "outcome": interaction_data.get("outcome", "neutral")  # positive, negative, neutral
        }
        
        self.interaction_experiences.append(experience)
        
        # 保持经验记录长度
        if len(self.interaction_experiences) > self.max_experiences:
            self.interaction_experiences = self.interaction_experiences[-self.max_experiences:]
        
        # 基于反馈调整性格
        self._adjust_personality_from_feedback(experience)
    
    def _adjust_personality_from_feedback(self, experience: Dict):
        """根据反馈调整性格特征"""
        outcome = experience["outcome"]
        behavior_pattern = experience.get("behavior_used")
        
        if not behavior_pattern:
            return
        
        # 根据反馈结果微调相关的性格特征
        adjustment_strength = 0.01  # 调整强度
        
        if outcome == "positive":
            # 正面反馈，增强相关特征
            for trait, required_level in behavior_pattern.personality_requirements.items():
                current_value = getattr(self.personality, trait, 0.5)
                new_value = min(1.0, current_value + adjustment_strength)
                setattr(self.personality, trait, new_value)
                
        elif outcome == "negative":
            # 负面反馈，适度降低相关特征
            for trait, required_level in behavior_pattern.personality_requirements.items():
                current_value = getattr(self.personality, trait, 0.5)
                new_value = max(0.0, current_value - adjustment_strength * 0.5)
                setattr(self.personality, trait, new_value)
        
        # 记录性格变化
        self.personality_history.append({
            "timestamp": datetime.now(),
            "traits": self.personality.to_dict(),
            "trigger": f"feedback_{outcome}",
            "behavior": behavior_pattern.name
        })
    
    def get_personality_description(self) -> str:
        """获取性格特征的文字描述"""
        traits = self.personality.to_dict()
        
        # 找出最突出的特征
        top_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
        
        trait_descriptions = {
            "curiosity": "好奇心很强",
            "playfulness": "很调皮",
            "sociability": "喜欢社交",
            "stubbornness": "有点任性",
            "intelligence": "很聪明",
            "empathy": "很善解人意",
            "creativity": "很有创意",
            "adventurousness": "喜欢冒险",
            "sensitivity": "很敏感",
            "independence": "很独立"
        }
        
        descriptions = []
        for trait, value in top_traits:
            if value > 0.6:
                desc = trait_descriptions.get(trait, trait)
                descriptions.append(desc)
        
        if descriptions:
            return "、".join(descriptions) + "的小家伙"
        else:
            return "一个可爱的小生命"
    
    def simulate_growth(self, days_passed: int):
        """模拟成长过程中的性格发展"""
        # 随着时间推移，某些特征可能会发生微小变化
        growth_rate = 0.001 * days_passed
        
        # 好奇心可能会增长
        self.personality.curiosity = min(1.0, self.personality.curiosity + growth_rate)
        
        # 智慧会随着经验增长
        experience_bonus = len(self.interaction_experiences) / self.max_experiences * 0.1
        self.personality.intelligence = min(1.0, self.personality.intelligence + experience_bonus)
        
        # 记录成长
        self.personality_history.append({
            "timestamp": datetime.now(),
            "traits": self.personality.to_dict(),
            "trigger": "natural_growth",
            "days_passed": days_passed
        })
    
    def get_behavioral_recommendations(self, context: Dict) -> List[str]:
        """根据当前状态获取行为建议"""
        recommendations = []
        
        # 分析当前情况
        current_emotion = context.get("current_emotion", {}).get("emotion", "neutral")
        user_activity = context.get("user_activity", "unknown")
        
        # 基于性格特征给出建议
        if self.personality.curiosity > 0.7 and user_activity == "idle":
            recommendations.append("主动探索新内容")
        
        if self.personality.sociability > 0.6 and current_emotion == "loneliness":
            recommendations.append("寻求用户陪伴")
        
        if self.personality.playfulness > 0.8 and user_activity == "working":
            recommendations.append("适度调皮吸引注意")
        
        if self.personality.empathy > 0.7 and "sad" in current_emotion:
            recommendations.append("提供情感支持")
        
        return recommendations