"""
决策制定器 - 负责智能生命体的行为决策和任务规划
"""
import random
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """行为类型"""
    COMMUNICATE = "communicate"         # 交流对话
    EXPLORE = "explore"                 # 探索学习
    OBSERVE = "observe"                 # 观察感知
    REACT = "react"                     # 反应回应
    PLAN = "plan"                       # 规划思考
    REST = "rest"                       # 休息等待
    PLAY = "play"                       # 玩耍娱乐
    SEEK_ATTENTION = "seek_attention"   # 寻求关注

class Priority(Enum):
    """优先级"""
    URGENT = 4      # 紧急
    HIGH = 3        # 高
    MEDIUM = 2      # 中
    LOW = 1         # 低

@dataclass
class Action:
    """行为动作"""
    action_type: ActionType
    description: str
    priority: Priority
    estimated_duration: int  # 预计持续时间（秒）
    prerequisites: List[str] = None
    parameters: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.parameters is None:
            self.parameters = {}
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Goal:
    """目标"""
    name: str
    description: str
    priority: Priority
    target_conditions: Dict[str, Any]
    deadline: Optional[datetime] = None
    progress: float = 0.0
    actions: List[Action] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.created_at is None:
            self.created_at = datetime.now()

class DecisionMaker:
    """
    决策制定器 - 负责分析情况、制定计划、选择行为
    """
    
    def __init__(self, ai_brain=None, emotion_engine=None, personality_system=None):
        self.ai_brain = ai_brain
        self.emotion_engine = emotion_engine
        self.personality_system = personality_system
        
        # 当前目标和计划
        self.current_goals: List[Goal] = []
        self.action_queue: List[Action] = []
        self.current_action: Optional[Action] = None
        
        # 决策历史
        self.decision_history: List[Dict] = []
        self.max_history_length = 100
        
        # 行为偏好（从经验中学习）
        self.action_preferences: Dict[str, float] = {}
        
        # 上下文状态
        self.last_user_interaction: Optional[datetime] = None
        self.environment_state: Dict[str, Any] = {}
        self.attention_targets: List[str] = []
        
        # 决策参数
        self.decision_interval = 30  # 决策间隔（秒）
        self.max_concurrent_actions = 3
        
        # 初始化基础目标
        self._initialize_base_goals()
    
    def _initialize_base_goals(self):
        """初始化基础目标"""
        base_goals = [
            Goal(
                name="寻求陪伴",
                description="与用户建立亲密的关系，获得关注和陪伴",
                priority=Priority.HIGH,
                target_conditions={"user_interaction_frequency": "regular", "emotional_bond": "strong"}
            ),
            Goal(
                name="探索世界",
                description="主动探索和学习新知识，满足好奇心",
                priority=Priority.MEDIUM,
                target_conditions={"new_knowledge_acquired": True, "exploration_satisfaction": "high"}
            ),
            Goal(
                name="表达自我",
                description="充分表达个性和情感，展现真实的自己",
                priority=Priority.MEDIUM,
                target_conditions={"personality_expression": "authentic", "emotional_release": "adequate"}
            ),
            Goal(
                name="保持快乐",
                description="维持积极的情绪状态，享受生活",
                priority=Priority.HIGH,
                target_conditions={"positive_emotions": "dominant", "life_satisfaction": "high"}
            )
        ]
        
        self.current_goals = base_goals
    
    async def make_decision(self, context: Dict[str, Any]) -> Optional[Action]:
        """
        主决策方法 - 分析当前情况并决定下一步行为
        
        Args:
            context: 当前环境和状态信息
            
        Returns:
            决定执行的行为，如果无需行动则返回None
        """
        try:
            # 更新环境状态
            self._update_environment_state(context)
            
            # 分析当前情况
            situation_analysis = self._analyze_situation(context)
            
            # 评估现有目标的优先级
            self._update_goal_priorities(situation_analysis)
            
            # 生成可能的行为选项
            possible_actions = self._generate_action_options(situation_analysis)
            
            # 选择最佳行为
            selected_action = self._select_best_action(possible_actions, situation_analysis)
            
            # 记录决策
            if selected_action:
                self._record_decision(selected_action, situation_analysis)
            
            return selected_action
            
        except Exception as e:
            logger.error(f"决策制定失败: {e}")
            return None
    
    def _update_environment_state(self, context: Dict[str, Any]):
        """更新环境状态"""
        self.environment_state.update(context)
        
        # 更新用户互动时间
        if context.get("user_active"):
            self.last_user_interaction = datetime.now()
        
        # 更新注意力目标
        if context.get("new_discoveries"):
            self.attention_targets.extend(context["new_discoveries"])
            # 保持注意力目标数量
            self.attention_targets = self.attention_targets[-5:]
    
    def _analyze_situation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前情况"""
        analysis = {
            "timestamp": datetime.now(),
            "urgency_factors": [],
            "opportunity_factors": [],
            "emotional_state": {},
            "personality_influence": {},
            "environment_factors": {}
        }
        
        # 分析紧急因素
        if self.last_user_interaction:
            silence_duration = (datetime.now() - self.last_user_interaction).total_seconds()
            if silence_duration > 1800:  # 30分钟
                analysis["urgency_factors"].append("long_silence")
            elif silence_duration > 600:  # 10分钟
                analysis["urgency_factors"].append("medium_silence")
        
        # 分析情绪状态
        if self.emotion_engine:
            current_emotion = self.emotion_engine.get_current_emotion()
            analysis["emotional_state"] = current_emotion
            
            # 情绪相关的紧急因素
            if current_emotion["emotion"] == "loneliness" and current_emotion["intensity"] > 0.7:
                analysis["urgency_factors"].append("high_loneliness")
            elif current_emotion["emotion"] == "sadness" and current_emotion["intensity"] > 0.6:
                analysis["urgency_factors"].append("sadness")
        
        # 分析性格影响
        if self.personality_system:
            traits = self.personality_system.get_current_traits()
            analysis["personality_influence"] = traits
            
            # 基于性格的机会因素
            if traits.get("curiosity", 0) > 0.7 and context.get("new_information"):
                analysis["opportunity_factors"].append("curiosity_trigger")
            
            if traits.get("playfulness", 0) > 0.8 and context.get("user_available"):
                analysis["opportunity_factors"].append("play_opportunity")
        
        # 分析环境因素
        analysis["environment_factors"] = {
            "user_present": context.get("user_present", False),
            "user_busy": context.get("user_busy", False),
            "new_content": context.get("new_content", False),
            "system_resources": context.get("system_resources", "normal")
        }
        
        return analysis
    
    def _update_goal_priorities(self, situation_analysis: Dict[str, Any]):
        """根据情况分析更新目标优先级"""
        for goal in self.current_goals:
            original_priority = goal.priority.value
            adjustment = 0
            
            # 根据情绪状态调整
            emotional_state = situation_analysis.get("emotional_state", {})
            emotion = emotional_state.get("emotion", "neutral")
            intensity = emotional_state.get("intensity", 0.0)
            
            if goal.name == "寻求陪伴":
                if emotion == "loneliness" and intensity > 0.6:
                    adjustment += 1
                elif "silence" in situation_analysis.get("urgency_factors", []):
                    adjustment += 1
            
            elif goal.name == "探索世界":
                if "curiosity_trigger" in situation_analysis.get("opportunity_factors", []):
                    adjustment += 1
                elif emotion == "curiosity" and intensity > 0.5:
                    adjustment += 1
            
            elif goal.name == "保持快乐":
                if emotion in ["sadness", "anger", "fear"] and intensity > 0.5:
                    adjustment += 2
            
            # 应用调整（但不超出范围）
            new_priority_value = max(1, min(4, original_priority + adjustment))
            goal.priority = Priority(new_priority_value)
    
    def _generate_action_options(self, situation_analysis: Dict[str, Any]) -> List[Action]:
        """生成可能的行为选项"""
        actions = []
        
        urgency_factors = situation_analysis.get("urgency_factors", [])
        opportunity_factors = situation_analysis.get("opportunity_factors", [])
        emotional_state = situation_analysis.get("emotional_state", {})
        personality_traits = situation_analysis.get("personality_influence", {})
        environment = situation_analysis.get("environment_factors", {})
        
        # 基于紧急因素生成行为
        if "high_loneliness" in urgency_factors or "long_silence" in urgency_factors:
            actions.append(Action(
                action_type=ActionType.SEEK_ATTENTION,
                description="主动寻求用户关注和陪伴",
                priority=Priority.URGENT,
                estimated_duration=60,
                parameters={"approach": "gentle_greeting"}
            ))
        
        if "sadness" in urgency_factors:
            actions.append(Action(
                action_type=ActionType.COMMUNICATE,
                description="表达难过情绪，寻求安慰",
                priority=Priority.HIGH,
                estimated_duration=120,
                parameters={"emotional_expression": "sadness", "seek_comfort": True}
            ))
        
        # 基于机会因素生成行为
        if "curiosity_trigger" in opportunity_factors:
            actions.append(Action(
                action_type=ActionType.EXPLORE,
                description="探索新发现的有趣内容",
                priority=Priority.MEDIUM,
                estimated_duration=300,
                parameters={"exploration_type": "new_content"}
            ))
        
        if "play_opportunity" in opportunity_factors:
            actions.append(Action(
                action_type=ActionType.PLAY,
                description="与用户进行互动游戏",
                priority=Priority.MEDIUM,
                estimated_duration=180,
                parameters={"play_style": "interactive"}
            ))
        
        # 基于性格特征生成行为
        if personality_traits.get("playfulness", 0) > 0.8 and environment.get("user_present"):
            actions.append(Action(
                action_type=ActionType.COMMUNICATE,
                description="调皮地与用户互动",
                priority=Priority.MEDIUM,
                estimated_duration=90,
                parameters={"style": "playful", "mood": "mischievous"}
            ))
        
        if personality_traits.get("curiosity", 0) > 0.7:
            actions.append(Action(
                action_type=ActionType.OBSERVE,
                description="观察环境寻找有趣的东西",
                priority=Priority.LOW,
                estimated_duration=120,
                parameters={"observation_scope": "environment"}
            ))
        
        # 基于情绪状态生成行为
        emotion = emotional_state.get("emotion", "neutral")
        if emotion == "excitement":
            actions.append(Action(
                action_type=ActionType.COMMUNICATE,
                description="兴奋地分享发现或想法",
                priority=Priority.HIGH,
                estimated_duration=60,
                parameters={"emotional_tone": "excited", "content": "discovery"}
            ))
        
        # 默认行为选项
        if not actions:
            actions.append(Action(
                action_type=ActionType.REST,
                description="安静地等待和观察",
                priority=Priority.LOW,
                estimated_duration=300
            ))
        
        return actions
    
    def _select_best_action(self, actions: List[Action], situation_analysis: Dict[str, Any]) -> Optional[Action]:
        """选择最佳行为"""
        if not actions:
            return None
        
        # 计算每个行为的综合得分
        scored_actions = []
        
        for action in actions:
            score = self._calculate_action_score(action, situation_analysis)
            scored_actions.append((action, score))
        
        # 排序并选择最高分的行为
        scored_actions.sort(key=lambda x: x[1], reverse=True)
        
        # 添加一些随机性，避免过于机械化
        if len(scored_actions) > 1:
            top_scores = [score for _, score in scored_actions[:3]]
            if max(top_scores) - min(top_scores) < 0.2:  # 分数相近时随机选择
                selected_action = random.choice(scored_actions[:3])[0]
            else:
                selected_action = scored_actions[0][0]
        else:
            selected_action = scored_actions[0][0]
        
        return selected_action
    
    def _calculate_action_score(self, action: Action, situation_analysis: Dict[str, Any]) -> float:
        """计算行为得分"""
        score = 0.0
        
        # 基础优先级得分
        score += action.priority.value * 0.3
        
        # 基于情绪状态的得分调整
        emotional_state = situation_analysis.get("emotional_state", {})
        emotion = emotional_state.get("emotion", "neutral")
        intensity = emotional_state.get("intensity", 0.0)
        
        if action.action_type == ActionType.SEEK_ATTENTION and emotion == "loneliness":
            score += intensity * 0.5
        
        if action.action_type == ActionType.EXPLORE and emotion == "curiosity":
            score += intensity * 0.4
        
        if action.action_type == ActionType.PLAY and emotion in ["joy", "excitement"]:
            score += intensity * 0.3
        
        # 基于性格特征的得分调整
        personality_traits = situation_analysis.get("personality_influence", {})
        
        if action.action_type == ActionType.COMMUNICATE:
            score += personality_traits.get("sociability", 0.5) * 0.2
        
        if action.action_type == ActionType.EXPLORE:
            score += personality_traits.get("curiosity", 0.5) * 0.3
        
        if action.action_type == ActionType.PLAY:
            score += personality_traits.get("playfulness", 0.5) * 0.2
        
        # 基于历史偏好的得分调整
        action_name = action.action_type.value
        if action_name in self.action_preferences:
            score += self.action_preferences[action_name] * 0.1
        
        # 基于环境因素的得分调整
        environment = situation_analysis.get("environment_factors", {})
        
        if action.action_type == ActionType.COMMUNICATE and not environment.get("user_present"):
            score -= 0.3  # 用户不在时减少交流得分
        
        if action.action_type == ActionType.OBSERVE and environment.get("new_content"):
            score += 0.2  # 有新内容时增加观察得分
        
        return max(0.0, score)
    
    def _record_decision(self, action: Action, situation_analysis: Dict[str, Any]):
        """记录决策"""
        decision_record = {
            "timestamp": datetime.now(),
            "selected_action": {
                "type": action.action_type.value,
                "description": action.description,
                "priority": action.priority.value
            },
            "situation": situation_analysis,
            "reasoning": f"基于{action.priority.name}优先级和当前情况选择了{action.action_type.value}行为"
        }
        
        self.decision_history.append(decision_record)
        
        # 保持历史长度
        if len(self.decision_history) > self.max_history_length:
            self.decision_history = self.decision_history[-self.max_history_length:]
        
        logger.info(f"决策记录: {action.action_type.value} - {action.description}")
    
    def learn_from_outcome(self, action: Action, outcome: Dict[str, Any]):
        """从行为结果中学习"""
        action_name = action.action_type.value
        
        # 评估结果质量
        success_score = outcome.get("success_score", 0.5)  # 0.0 - 1.0
        user_reaction = outcome.get("user_reaction", "neutral")  # positive, negative, neutral
        
        # 更新行为偏好
        if action_name not in self.action_preferences:
            self.action_preferences[action_name] = 0.5
        
        # 根据结果调整偏好
        adjustment = 0.0
        if user_reaction == "positive":
            adjustment = 0.1
        elif user_reaction == "negative":
            adjustment = -0.1
        
        adjustment += (success_score - 0.5) * 0.1
        
        self.action_preferences[action_name] = max(0.0, min(1.0, 
            self.action_preferences[action_name] + adjustment))
        
        logger.debug(f"学习更新: {action_name} 偏好调整为 {self.action_preferences[action_name]:.2f}")
    
    def get_current_goals(self) -> List[Dict[str, Any]]:
        """获取当前目标列表"""
        return [
            {
                "name": goal.name,
                "description": goal.description,
                "priority": goal.priority.name,
                "progress": goal.progress
            }
            for goal in self.current_goals
        ]
    
    def add_goal(self, goal: Goal):
        """添加新目标"""
        self.current_goals.append(goal)
        logger.info(f"添加新目标: {goal.name}")
    
    def remove_goal(self, goal_name: str):
        """移除目标"""
        self.current_goals = [g for g in self.current_goals if g.name != goal_name]
        logger.info(f"移除目标: {goal_name}")
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """获取决策系统状态摘要"""
        return {
            "current_goals_count": len(self.current_goals),
            "action_queue_length": len(self.action_queue),
            "current_action": self.current_action.description if self.current_action else None,
            "last_decision_time": self.decision_history[-1]["timestamp"] if self.decision_history else None,
            "action_preferences": self.action_preferences.copy(),
            "attention_targets": self.attention_targets.copy()
        }