"""
网络搜索模块 - 主动搜索网络信息
"""
import logging
import requests
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote, urljoin
import time

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from config.settings import settings

logger = logging.getLogger(__name__)

class WebSearcher:
    """网络搜索器 - 支持多种搜索引擎"""
    
    def __init__(self):
        self.search_history = []
        self.max_history = 100
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 搜索引擎配置
        self.search_engines = {
            'serpapi': self._search_serpapi,
            'duckduckgo': self._search_duckduckgo,
            'google': self._search_google_custom
        }
        
        # 兴趣关键词（AI会主动搜索这些）
        self.interest_keywords = [
            "最新科技", "人工智能", "有趣发现", "今日热点", 
            "新发明", "科学突破", "创意设计", "未来科技"
        ]
    
    def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """执行搜索"""
        if max_results is None:
            max_results = settings.knowledge.max_search_results
            
        try:
            # 选择搜索引擎
            search_engine = settings.knowledge.search_engine
            if search_engine not in self.search_engines:
                search_engine = 'duckduckgo'  # 默认使用DuckDuckGo
            
            logger.info(f"使用{search_engine}搜索: {query}")
            
            # 执行搜索
            results = self.search_engines[search_engine](query, max_results)
            
            # 记录搜索历史
            self._record_search(query, results)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return self._get_fallback_results(query)
    
    def _search_serpapi(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """使用SerpAPI搜索"""
        try:
            if not settings.knowledge.search_api_key:
                return self._search_duckduckgo(query, max_results)
            
            url = "https://serpapi.com/search"
            params = {
                'q': query,
                'api_key': settings.knowledge.search_api_key,
                'engine': 'google',
                'num': max_results,
                'hl': 'zh'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # 解析有机搜索结果
            if 'organic_results' in data:
                for item in data['organic_results'][:max_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'timestamp': datetime.now(),
                        'source': 'serpapi'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"SerpAPI搜索失败: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """使用DuckDuckGo搜索"""
        try:
            # DuckDuckGo即时答案API
            api_url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # 添加即时答案
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', query),
                    'url': data.get('AbstractURL', ''),
                    'snippet': data.get('Abstract', ''),
                    'timestamp': datetime.now(),
                    'source': 'duckduckgo_instant'
                })
            
            # 添加相关主题
            for topic in data.get('RelatedTopics', [])[:max_results-1]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('Text', '').split(' - ')[0],
                        'url': topic.get('FirstURL', ''),
                        'snippet': topic.get('Text', ''),
                        'timestamp': datetime.now(),
                        'source': 'duckduckgo_related'
                    })
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo搜索失败: {e}")
            return []
    
    def _search_google_custom(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """使用Google Custom Search API"""
        try:
            if not settings.knowledge.search_api_key:
                return self._search_duckduckgo(query, max_results)
            
            # Google Custom Search需要API密钥和搜索引擎ID
            api_key = settings.knowledge.search_api_key
            cx = getattr(settings.knowledge, 'google_cx_id', 'your_search_engine_id')
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': query,
                'num': min(max_results, 10),  # Google限制最多10个结果
                'hl': 'zh'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'items' in data:
                for item in data['items']:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'timestamp': datetime.now(),
                        'source': 'google_custom'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Google Custom Search失败: {e}")
            return []
    
    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        if BeautifulSoup:
            soup = BeautifulSoup(text, 'html.parser')
            return soup.get_text()
        else:
            # 简单的HTML标签清理
            clean = re.compile('<.*?>')
            return re.sub(clean, '', text)
    
    def _get_fallback_results(self, query: str) -> List[Dict[str, Any]]:
        """获取备用搜索结果"""
        return [
            {
                'title': f"关于'{query}'的信息",
                'url': "https://example.com",
                'snippet': f"由于网络搜索暂时不可用，这是关于{query}的基础信息。建议稍后重试或检查网络连接。",
                'timestamp': datetime.now(),
                'source': 'fallback'
            }
        ]
    
    def _record_search(self, query: str, results: List[Dict[str, Any]]):
        """记录搜索历史"""
        search_record = {
            'query': query,
            'results_count': len(results),
            'timestamp': datetime.now(),
            'success': len(results) > 0
        }
        
        self.search_history.append(search_record)
        
        # 保持历史长度
        if len(self.search_history) > self.max_history:
            self.search_history = self.search_history[-self.max_history:]
        
        logger.info(f"搜索记录: {query} -> {len(results)} 个结果")
    
    def get_random_interest_query(self) -> str:
        """获取随机的感兴趣查询"""
        import random
        return random.choice(self.interest_keywords)
    
    def suggest_search_topics(self, context: Dict[str, Any] = None) -> List[str]:
        """基于上下文建议搜索主题"""
        suggestions = []
        
        # 基础感兴趣的主题
        base_topics = ["今日新闻", "科技发展", "有趣发现", "创新发明"]
        suggestions.extend(base_topics)
        
        # 基于情绪状态的建议
        if context and context.get('emotion'):
            emotion = context['emotion'].get('emotion', '')
            if emotion == 'curiosity':
                suggestions.extend(["未解之谜", "科学探索", "新发现"])
            elif emotion == 'joy':
                suggestions.extend(["有趣视频", "搞笑内容", "快乐故事"])
            elif emotion == 'excitement':
                suggestions.extend(["最新科技", "突破性进展", "震撼发现"])
        
        # 基于时间的建议
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            suggestions.append("今日新闻")
        elif 12 <= current_hour < 18:
            suggestions.append("下午资讯")
        else:
            suggestions.append("晚间新闻")
        
        return suggestions[:5]  # 返回最多5个建议
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        if not self.search_history:
            return {'total_searches': 0, 'success_rate': 0.0}
        
        total_searches = len(self.search_history)
        successful_searches = sum(1 for search in self.search_history if search['success'])
        success_rate = successful_searches / total_searches
        
        # 最近搜索的主题
        recent_queries = [search['query'] for search in self.search_history[-5:]]
        
        return {
            'total_searches': total_searches,
            'success_rate': success_rate,
            'recent_queries': recent_queries,
            'last_search_time': self.search_history[-1]['timestamp'] if self.search_history else None
        }