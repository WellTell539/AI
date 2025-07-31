"""
知识管理器 - 整合搜索、分析和知识存储
"""
import logging
import asyncio
import threading
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .web_searcher import WebSearcher
from .content_analyzer import ContentAnalyzer
from config.settings import settings

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """知识管理器 - 智能生命体的知识获取和管理系统"""
    
    def __init__(self, ai_brain=None, emotion_engine=None):
        self.ai_brain = ai_brain
        self.emotion_engine = emotion_engine
        
        # 核心组件
        self.web_searcher = WebSearcher()
        self.content_analyzer = ContentAnalyzer()
        
        # 知识库
        self.knowledge_base = {
            'discoveries': [],        # 发现的有趣内容
            'learned_facts': [],      # 学到的事实
            'interests': set(),       # 兴趣主题
            'search_preferences': {}  # 搜索偏好
        }
        
        # 自动探索控制
        self.auto_exploration_active = False
        self.exploration_thread = None
        self.last_exploration_time = None
        
        # 学习统计
        self.learning_stats = {
            'total_searches': 0,
            'discoveries_made': 0,
            'topics_explored': set(),
            'favorite_categories': {}
        }
    
    def start_auto_exploration(self):
        """启动自动探索模式"""
        if not settings.knowledge.auto_exploration:
            logger.info("自动探索功能已禁用")
            return
        
        if self.auto_exploration_active:
            logger.info("自动探索已在运行")
            return
        
        self.auto_exploration_active = True
        self.exploration_thread = threading.Thread(target=self._exploration_loop, daemon=True)
        self.exploration_thread.start()
        
        logger.info("自动探索模式已启动")
    
    def stop_auto_exploration(self):
        """停止自动探索模式"""
        self.auto_exploration_active = False
        if self.exploration_thread:
            self.exploration_thread.join(timeout=5)
        
        logger.info("自动探索模式已停止")
    
    def _exploration_loop(self):
        """自动探索循环"""
        while self.auto_exploration_active:
            try:
                # 等待探索间隔
                time.sleep(settings.knowledge.exploration_interval)
                
                if not self.auto_exploration_active:
                    break
                
                # 执行探索
                self._perform_exploration()
                
            except Exception as e:
                logger.error(f"自动探索循环出错: {e}")
                time.sleep(60)  # 出错后等待1分钟
    
    def _perform_exploration(self):
        """执行一次探索"""
        try:
            # 选择探索主题
            topic = self._choose_exploration_topic()
            
            logger.info(f"开始探索主题: {topic}")
            
            # 执行搜索
            search_results = self.web_searcher.search(topic)
            
            if not search_results:
                logger.info(f"未找到关于'{topic}'的搜索结果")
                return
            
            # 分析结果
            analysis_result = self.content_analyzer.analyze_search_results(search_results)
            
            if analysis_result['status'] != 'success':
                logger.error(f"内容分析失败: {analysis_result.get('message', '未知错误')}")
                return
            
            analysis = analysis_result['analysis']
            
            # 处理发现的内容
            discoveries = self._process_discoveries(topic, search_results, analysis)
            
            # 更新知识库
            self._update_knowledge_base(topic, discoveries, analysis)
            
            # 更新统计
            self._update_learning_stats(topic, analysis)
            
            # 记录探索时间
            self.last_exploration_time = datetime.now()
            
            # 通知AI大脑有新发现
            if self.ai_brain and discoveries:
                self._notify_ai_about_discoveries(topic, discoveries)
            
        except Exception as e:
            logger.error(f"执行探索失败: {e}")
    
    def _choose_exploration_topic(self) -> str:
        """选择探索主题"""
        # 获取当前情绪状态来影响主题选择
        current_emotion = None
        if self.emotion_engine:
            emotion_state = self.emotion_engine.get_current_emotion()
            current_emotion = emotion_state.get('emotion', 'curious')
        
        # 根据情绪选择主题
        context = {'emotion': {'emotion': current_emotion}} if current_emotion else None
        suggested_topics = self.web_searcher.suggest_search_topics(context)
        
        # 结合兴趣和随机性
        if self.knowledge_base['interests']:
            interests = list(self.knowledge_base['interests'])
            suggested_topics.extend(interests[:3])
        
        # 添加一些随机性
        if random.random() < 0.3:  # 30%概率选择完全随机的主题
            topic = self.web_searcher.get_random_interest_query()
        else:
            topic = random.choice(suggested_topics) if suggested_topics else "有趣发现"
        
        return topic
    
    def _process_discoveries(self, topic: str, search_results: List[Dict[str, Any]], 
                           analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理发现的内容"""
        discoveries = []
        
        # 处理有趣的结果
        for result in analysis.get('interesting_results', []):
            discovery = {
                'topic': topic,
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'url': result.get('url', ''),
                'category': analysis.get('category', 'general'),
                'sentiment': analysis.get('sentiment', 'neutral'),
                'discovered_at': datetime.now(),
                'interest_score': self._calculate_interest_score(result, analysis)
            }
            discoveries.append(discovery)
        
        # 如果没有特别有趣的结果，选择最相关的
        if not discoveries and search_results:
            best_result = search_results[0]  # 假设第一个结果最相关
            discovery = {
                'topic': topic,
                'title': best_result.get('title', ''),
                'snippet': best_result.get('snippet', ''),
                'url': best_result.get('url', ''),
                'category': analysis.get('category', 'general'),
                'sentiment': analysis.get('sentiment', 'neutral'),
                'discovered_at': datetime.now(),
                'interest_score': 0.5
            }
            discoveries.append(discovery)
        
        return discoveries
    
    def _calculate_interest_score(self, result: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """计算兴趣得分"""
        score = 0.5  # 基础分数
        
        # 基于类别调整
        category = analysis.get('category', 'general')
        category_preferences = self.learning_stats['favorite_categories']
        if category in category_preferences:
            score += 0.2 * (category_preferences[category] / max(category_preferences.values()))
        
        # 基于情感倾向调整
        sentiment = analysis.get('sentiment', 'neutral')
        if sentiment == 'positive':
            score += 0.2
        elif sentiment == 'negative':
            score -= 0.1
        
        # 基于关键词匹配调整
        content = result.get('title', '') + ' ' + result.get('snippet', '')
        for interest in self.knowledge_base['interests']:
            if interest.lower() in content.lower():
                score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _update_knowledge_base(self, topic: str, discoveries: List[Dict[str, Any]], 
                             analysis: Dict[str, Any]):
        """更新知识库"""
        # 添加发现
        self.knowledge_base['discoveries'].extend(discoveries)
        
        # 保持发现列表长度
        if len(self.knowledge_base['discoveries']) > 200:
            # 按兴趣得分排序，保留最有趣的
            self.knowledge_base['discoveries'].sort(key=lambda x: x['interest_score'], reverse=True)
            self.knowledge_base['discoveries'] = self.knowledge_base['discoveries'][:150]
        
        # 更新兴趣主题
        self.knowledge_base['interests'].add(topic)
        
        # 添加关键主题到兴趣中
        for key_topic in analysis.get('key_topics', []):
            if len(key_topic) > 2:  # 忽略太短的词
                self.knowledge_base['interests'].add(key_topic)
        
        # 保持兴趣列表大小
        if len(self.knowledge_base['interests']) > 50:
            # 这里可以实现更智能的裁剪策略
            interests_list = list(self.knowledge_base['interests'])
            self.knowledge_base['interests'] = set(interests_list[-40:])
    
    def _update_learning_stats(self, topic: str, analysis: Dict[str, Any]):
        """更新学习统计"""
        self.learning_stats['total_searches'] += 1
        self.learning_stats['discoveries_made'] += len(analysis.get('interesting_results', []))
        self.learning_stats['topics_explored'].add(topic)
        
        # 更新类别偏好
        category = analysis.get('category', 'general')
        self.learning_stats['favorite_categories'][category] = \
            self.learning_stats['favorite_categories'].get(category, 0) + 1
    
    def _notify_ai_about_discoveries(self, topic: str, discoveries: List[Dict[str, Any]]):
        """通知AI大脑有新发现"""
        if not discoveries:
            return
        
        try:
            # 选择最有趣的发现
            best_discovery = max(discoveries, key=lambda x: x['interest_score'])
            
            # 触发好奇心和兴奋情绪
            if self.emotion_engine:
                self.emotion_engine.process_trigger({
                    'type': 'curiosity',
                    'intensity': 0.7,
                    'source': 'new_discovery',
                    'duration': 600
                })
                
                self.emotion_engine.process_trigger({
                    'type': 'excitement',
                    'intensity': 0.6,
                    'source': 'interesting_content',
                    'duration': 300
                })
            
            # 设置AI的注意力焦点
            if hasattr(self.ai_brain, 'set_attention_focus'):
                self.ai_brain.set_attention_focus(f"发现了关于{topic}的有趣内容")
            
            logger.info(f"通知AI关于新发现: {best_discovery['title']}")
            
        except Exception as e:
            logger.error(f"通知AI发现失败: {e}")
    
    def manual_search(self, query: str) -> Dict[str, Any]:
        """手动搜索"""
        try:
            logger.info(f"执行手动搜索: {query}")
            
            # 执行搜索
            search_results = self.web_searcher.search(query)
            
            if not search_results:
                return {
                    'success': False,
                    'message': f"未找到关于'{query}'的搜索结果",
                    'results': []
                }
            
            # 分析结果
            analysis_result = self.content_analyzer.analyze_search_results(search_results)
            
            if analysis_result['status'] != 'success':
                return {
                    'success': False,
                    'message': f"内容分析失败: {analysis_result.get('message', '未知错误')}",
                    'results': search_results
                }
            
            analysis = analysis_result['analysis']
            
            # 处理发现
            discoveries = self._process_discoveries(query, search_results, analysis)
            
            # 更新知识库
            self._update_knowledge_base(query, discoveries, analysis)
            
            # 更新统计
            self._update_learning_stats(query, analysis)
            
            return {
                'success': True,
                'message': f"搜索完成，找到{len(search_results)}个结果",
                'results': search_results,
                'analysis': analysis,
                'discoveries': discoveries
            }
            
        except Exception as e:
            logger.error(f"手动搜索失败: {e}")
            return {
                'success': False,
                'message': f"搜索失败: {str(e)}",
                'results': []
            }
    
    def get_recent_discoveries(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的发现"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_discoveries = [
            discovery for discovery in self.knowledge_base['discoveries']
            if discovery['discovered_at'] > cutoff_time
        ]
        
        # 按兴趣得分排序
        recent_discoveries.sort(key=lambda x: x['interest_score'], reverse=True)
        
        return recent_discoveries[:10]  # 最多返回10个
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """获取知识库摘要"""
        recent_discoveries = self.get_recent_discoveries()
        
        return {
            'total_discoveries': len(self.knowledge_base['discoveries']),
            'total_interests': len(self.knowledge_base['interests']),
            'recent_discoveries_count': len(recent_discoveries),
            'learning_stats': {
                'total_searches': self.learning_stats['total_searches'],
                'discoveries_made': self.learning_stats['discoveries_made'],
                'topics_explored_count': len(self.learning_stats['topics_explored']),
                'favorite_categories': dict(list(self.learning_stats['favorite_categories'].items())[:5])
            },
            'last_exploration': self.last_exploration_time,
            'auto_exploration_active': self.auto_exploration_active,
            'top_interests': list(self.knowledge_base['interests'])[:10]
        }
    
    def share_discovery(self) -> Optional[Dict[str, Any]]:
        """分享一个有趣的发现"""
        if not self.knowledge_base['discoveries']:
            return None
        
        # 从最近的发现中选择一个有趣的
        recent_discoveries = self.get_recent_discoveries(hours=72)  # 最近3天
        
        if recent_discoveries:
            discovery = random.choice(recent_discoveries[:5])  # 从前5个中随机选择
        else:
            # 如果没有最近的发现，从所有发现中选择
            discovery = random.choice(self.knowledge_base['discoveries'])
        
        return discovery
    
    def get_search_suggestions(self, context: Dict[str, Any] = None) -> List[str]:
        """获取搜索建议"""
        suggestions = []
        
        # 基于兴趣的建议
        if self.knowledge_base['interests']:
            interests = list(self.knowledge_base['interests'])
            suggestions.extend(random.sample(interests, min(3, len(interests))))
        
        # 基于情绪的建议
        if context and self.emotion_engine:
            emotion_suggestions = self.web_searcher.suggest_search_topics(context)
            suggestions.extend(emotion_suggestions[:3])
        
        # 基于类别偏好的建议
        if self.learning_stats['favorite_categories']:
            favorite_category = max(self.learning_stats['favorite_categories'], 
                                  key=self.learning_stats['favorite_categories'].get)
            category_suggestions = {
                'technology': ['最新科技', 'AI发展', '科技创新'],
                'science': ['科学发现', '研究突破', '科学新闻'],
                'entertainment': ['有趣内容', '娱乐新闻', '创意作品'],
                'news': ['今日新闻', '热点事件', '时事分析'],
                'learning': ['学习资源', '教育内容', '知识分享']
            }
            suggestions.extend(category_suggestions.get(favorite_category, []))
        
        # 去重并限制数量
        unique_suggestions = list(set(suggestions))
        return unique_suggestions[:8]