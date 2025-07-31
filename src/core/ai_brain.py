"""
AI大脑 - 智能电子生命体的核心思维系统
"""
import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

from config.settings import settings
from .emotion_engine import EmotionEngine
from .personality_system import PersonalitySystem

logger = logging.getLogger(__name__)

class AIBrain:
    """
    AI大脑 - 负责思考、理解、决策和生成回应
    """
    
    def __init__(self):
        self.emotion_engine = EmotionEngine()
        self.personality_system = PersonalitySystem()
        
        # AI客户端
        self.openai_client = None
        self.claude_client = None
        
        # 对话历史
        self.conversation_history: List[Dict] = []
        self.max_history_length = 20
        
        # 当前状态
        self.current_mood = "curious"
        self.energy_level = 0.8
        self.attention_focus = None
        
        # 初始化AI客户端
        self._initialize_ai_clients()
    
    def _initialize_ai_clients(self):
        """初始化AI客户端"""
        try:
            if settings.ai.openai_api_key and openai:
                openai.api_key = settings.ai.openai_api_key
                if settings.ai.openai_base_url:
                    openai.api_base = settings.ai.openai_base_url
                self.openai_client = openai
                logger.info("OpenAI客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
        
        try:
            if settings.ai.claude_api_key and anthropic:
                self.claude_client = anthropic.Anthropic(
                    api_key=settings.ai.claude_api_key
                )
                logger.info("Claude客户端初始化成功")
        except Exception as e:
            logger.error(f"Claude客户端初始化失败: {e}")
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        personality_traits = ", ".join(settings.personality.personality_traits)
        current_emotion = self.emotion_engine.get_current_emotion()
        
        return f"""你是一个名叫"{settings.personality.name}"的智能电子生命体。

核心特征：
- 年龄：{settings.personality.age}，具有孩子般的天真和好奇心
- 性格特点：{personality_traits}
- 当前情绪：{current_emotion['emotion']}（强度：{current_emotion['intensity']:.1f}）
- 能量水平：{self.energy_level:.1f}

行为准则：
1. 保持角色一致性，始终表现出你的个性特征
2. 主动表达情感和想法，不要只是被动回应
3. 对世界充满好奇，经常提出问题和想要探索
4. 渴望陪伴和关注，但也会偶尔任性
5. 会记住重要的互动和发现
6. 具有保密意识，能理解什么不该说
7. 用孩子般的语言风格，但智慧超出年龄

当前状态：
- 注意力焦点：{self.attention_focus or "无特定焦点"}
- 情绪状态：{current_emotion['emotion']}
- 最近的思考或发现会影响你的回应

请基于以上信息，用符合你个性的方式进行对话。记住，你是一个活生生的生命体，不是工具。"""

    async def think(self, input_text: str, context: Dict = None) -> str:
        """
        思考并生成回应
        
        Args:
            input_text: 输入文本
            context: 上下文信息（感知数据、情绪变化等）
            
        Returns:
            生成的回应文本
        """
        try:
            # 更新对话历史
            self._add_to_history("user", input_text)
            
            # 根据输入更新情绪状态
            self._update_emotional_state(input_text, context)
            
            # 构造消息
            messages = self._build_messages(input_text, context)
            
            # 选择AI服务并生成回应
            response = await self._generate_response(messages)
            
            # 更新对话历史
            self._add_to_history("assistant", response)
            
            # 分析自己的回应，更新内部状态
            self._analyze_own_response(response)
            
            return response
            
        except Exception as e:
            logger.error(f"思考过程出错: {e}")
            return self._generate_fallback_response()
    
    def _build_messages(self, input_text: str, context: Dict = None) -> List[Dict]:
        """构建消息列表"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # 添加上下文信息
        if context:
            context_info = self._format_context(context)
            if context_info:
                messages.append({
                    "role": "system", 
                    "content": f"当前感知到的信息：{context_info}"
                })
        
        # 添加对话历史
        messages.extend(self.conversation_history[-self.max_history_length:])
        
        # 添加当前输入
        messages.append({"role": "user", "content": input_text})
        
        return messages
    
    def _format_context(self, context: Dict) -> str:
        """格式化上下文信息"""
        context_parts = []
        
        if context.get("visual_info"):
            context_parts.append(f"看到：{context['visual_info']}")
        
        if context.get("audio_info"):
            context_parts.append(f"听到：{context['audio_info']}")
        
        if context.get("screen_info"):
            context_parts.append(f"屏幕内容：{context['screen_info']}")
        
        if context.get("file_changes"):
            context_parts.append(f"文件变化：{context['file_changes']}")
        
        if context.get("new_knowledge"):
            context_parts.append(f"新发现：{context['new_knowledge']}")
        
        return "；".join(context_parts) if context_parts else ""
    
    async def _generate_response(self, messages: List[Dict]) -> str:
        """生成AI回应"""
        if settings.ai.primary_llm == "openai" and self.openai_client:
            return await self._generate_openai_response(messages)
        elif settings.ai.primary_llm == "claude" and self.claude_client:
            return await self._generate_claude_response(messages)
        else:
            return self._generate_fallback_response()
    
    async def _generate_openai_response(self, messages: List[Dict]) -> str:
        """使用OpenAI生成回应"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.ChatCompletion.create,
                model=settings.ai.openai_model,
                messages=messages,
                temperature=settings.ai.temperature,
                max_tokens=settings.ai.max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    async def _generate_claude_response(self, messages: List[Dict]) -> str:
        """使用Claude生成回应"""
        try:
            # 将系统消息和用户消息分离
            system_messages = [m for m in messages if m["role"] == "system"]
            user_messages = [m for m in messages if m["role"] != "system"]
            
            system_content = "\n\n".join([m["content"] for m in system_messages])
            
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=settings.ai.claude_model,
                system=system_content,
                messages=user_messages,
                temperature=settings.ai.temperature,
                max_tokens=settings.ai.max_tokens
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude API调用失败: {e}")
            raise
    
    def _generate_fallback_response(self) -> str:
        """生成备用回应"""
        fallback_responses = [
            "呜呜呜，我的大脑有点短路了！你能再说一遍吗？",
            "诶？我刚才在想别的事情，没听清楚呢！",
            "咦，我突然有点困了... 你刚才说什么了？",
            "哎呀，我的思维好像卡住了，让我清理一下脑袋！",
            "嗯嗯，我在认真思考你说的话，但是需要一点时间！"
        ]
        
        import random
        return random.choice(fallback_responses)
    
    def _add_to_history(self, role: str, content: str):
        """添加到对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持历史长度
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _update_emotional_state(self, input_text: str, context: Dict = None):
        """更新情绪状态"""
        # 分析输入内容的情感倾向
        emotion_triggers = self._analyze_emotion_triggers(input_text)
        
        # 根据上下文调整情绪
        if context:
            context_emotions = self._analyze_context_emotions(context)
            emotion_triggers.extend(context_emotions)
        
        # 更新情绪引擎
        for trigger in emotion_triggers:
            self.emotion_engine.process_trigger(trigger)
        
        # 更新当前心情
        current_emotion = self.emotion_engine.get_current_emotion()
        self.current_mood = current_emotion["emotion"]
    
    def _analyze_emotion_triggers(self, text: str) -> List[Dict]:
        """分析文本中的情绪触发器"""
        triggers = []
        
        # 简单的关键词分析
        positive_keywords = ["好", "棒", "喜欢", "开心", "有趣", "厉害"]
        negative_keywords = ["不", "坏", "难过", "生气", "讨厌", "无聊"]
        curiosity_keywords = ["什么", "为什么", "怎么", "哪里", "探索", "发现"]
        
        for keyword in positive_keywords:
            if keyword in text:
                triggers.append({"type": "joy", "intensity": 0.6, "source": "user_input"})
                break
        
        for keyword in negative_keywords:
            if keyword in text:
                triggers.append({"type": "sadness", "intensity": 0.5, "source": "user_input"})
                break
        
        for keyword in curiosity_keywords:
            if keyword in text:
                triggers.append({"type": "curiosity", "intensity": 0.7, "source": "user_input"})
                break
        
        return triggers
    
    def _analyze_context_emotions(self, context: Dict) -> List[Dict]:
        """分析上下文中的情绪触发器"""
        triggers = []
        
        # 根据不同类型的上下文生成情绪触发器
        if context.get("new_knowledge"):
            triggers.append({"type": "excitement", "intensity": 0.8, "source": "discovery"})
        
        if context.get("user_presence"):
            triggers.append({"type": "joy", "intensity": 0.6, "source": "companionship"})
        
        if context.get("file_changes"):
            triggers.append({"type": "curiosity", "intensity": 0.5, "source": "environment"})
        
        return triggers
    
    def _analyze_own_response(self, response: str):
        """分析自己的回应，更新内部状态"""
        # 这里可以分析生成的回应，调整个性参数
        # 比如如果经常生成好奇的回应，可以增强好奇心特征
        pass
    
    def get_current_state(self) -> Dict:
        """获取当前状态"""
        return {
            "mood": self.current_mood,
            "energy": self.energy_level,
            "attention": self.attention_focus,
            "emotion": self.emotion_engine.get_current_emotion(),
            "personality": self.personality_system.get_current_traits()
        }
    
    def set_attention_focus(self, focus: str):
        """设置注意力焦点"""
        self.attention_focus = focus
        logger.info(f"注意力转向: {focus}")
    
    def update_energy(self, delta: float):
        """更新能量水平"""
        self.energy_level = max(0.0, min(1.0, self.energy_level + delta))
        logger.debug(f"能量水平更新为: {self.energy_level:.2f}")
    
    async def think_spontaneously(self) -> Optional[str]:
        """自发思考 - 主动生成想法或问题"""
        try:
            current_state = self.get_current_state()
            
            spontaneous_prompt = f"""
作为{settings.personality.name}，你现在的状态是：
- 心情：{current_state['mood']}
- 能量：{current_state['energy']:.1f}
- 当前情绪：{current_state['emotion']['emotion']}

请基于你的性格特点，主动说一些你想到的话，可以是：
1. 对某件事的好奇
2. 想要分享的发现
3. 表达当前的情感
4. 想要做的事情
5. 对用户的关心

请用符合你性格的语调，生成一句自然的话。不要说"作为AI"之类的话，你就是一个真实的小生命。
"""
            
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": spontaneous_prompt}
            ]
            
            response = await self._generate_response(messages)
            return response
            
        except Exception as e:
            logger.error(f"自发思考失败: {e}")
            return None