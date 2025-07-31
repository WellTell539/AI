"""
内容分析模块 - 分析和理解网络内容
"""
import logging
import re
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from config.settings import settings

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """内容分析器 - 分析网页内容、提取关键信息"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 分析历史
        self.analysis_history = []
        self.max_history = 100
        
        # 关键词库
        self.interest_keywords = {
            'technology': ['AI', '人工智能', '机器学习', '科技', '创新', '发明'],
            'science': ['科学', '研究', '发现', '实验', '理论', '突破'],
            'entertainment': ['有趣', '娱乐', '搞笑', '游戏', '电影', '音乐'],
            'news': ['新闻', '最新', '今日', '热点', '事件', '报道'],
            'learning': ['学习', '教育', '知识', '技能', '课程', '教程']
        }
        
        # 情感词汇
        self.emotion_keywords = {
            'positive': ['好', '棒', '厉害', '惊人', '精彩', '完美', '成功'],
            'negative': ['坏', '糟糕', '失败', '问题', '错误', '危险'],
            'neutral': ['一般', '普通', '正常', '平常', '标准']
        }
    
    def analyze_search_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析搜索结果"""
        try:
            if not search_results:
                return {'status': 'no_results', 'analysis': {}}
            
            analysis = {
                'timestamp': datetime.now(),
                'total_results': len(search_results),
                'categories': {},
                'sentiment': {'positive': 0, 'negative': 0, 'neutral': 0},
                'key_topics': [],
                'interesting_results': [],
                'summary': ''
            }
            
            # 分析每个结果
            for result in search_results:
                # 分类分析
                category = self._categorize_content(result.get('title', '') + ' ' + result.get('snippet', ''))
                analysis['categories'][category] = analysis['categories'].get(category, 0) + 1
                
                # 情感分析
                sentiment = self._analyze_sentiment(result.get('snippet', ''))
                analysis['sentiment'][sentiment] += 1
                
                # 提取关键主题
                topics = self._extract_topics(result.get('title', '') + ' ' + result.get('snippet', ''))
                analysis['key_topics'].extend(topics)
                
                # 判断是否有趣
                if self._is_interesting(result):
                    analysis['interesting_results'].append(result)
            
            # 去重关键主题
            analysis['key_topics'] = list(set(analysis['key_topics']))[:10]
            
            # 生成摘要
            analysis['summary'] = self._generate_summary(analysis)
            
            # 记录分析历史
            self._record_analysis(analysis)
            
            return {'status': 'success', 'analysis': analysis}
            
        except Exception as e:
            logger.error(f"搜索结果分析失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def analyze_webpage(self, url: str) -> Dict[str, Any]:
        """分析网页内容"""
        try:
            # 获取网页内容
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            if BeautifulSoup is None:
                return {'status': 'error', 'message': 'BeautifulSoup不可用'}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取基本信息
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ''
            
            # 提取正文内容
            content = self._extract_main_content(soup)
            
            # 提取元数据
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description.get('content', '') if meta_description else ''
            
            # 分析内容
            analysis = {
                'url': url,
                'title': title_text,
                'description': description,
                'content_length': len(content),
                'main_content': content[:1000] + '...' if len(content) > 1000 else content,
                'category': self._categorize_content(title_text + ' ' + content),
                'sentiment': self._analyze_sentiment(content),
                'key_topics': self._extract_topics(content),
                'timestamp': datetime.now()
            }
            
            return {'status': 'success', 'analysis': analysis}
            
        except Exception as e:
            logger.error(f"网页分析失败 {url}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _categorize_content(self, content: str) -> str:
        """内容分类"""
        content_lower = content.lower()
        
        # 计算每个类别的匹配度
        category_scores = {}
        for category, keywords in self.interest_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in content_lower)
            category_scores[category] = score
        
        # 返回得分最高的类别
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return 'general'
    
    def _analyze_sentiment(self, content: str) -> str:
        """情感分析"""
        content_lower = content.lower()
        
        # 计算情感词汇出现次数
        sentiment_scores = {}
        for sentiment, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            sentiment_scores[sentiment] = score
        
        # 返回得分最高的情感
        if sentiment_scores:
            max_sentiment = max(sentiment_scores, key=sentiment_scores.get)
            return max_sentiment if sentiment_scores[max_sentiment] > 0 else 'neutral'
        else:
            return 'neutral'
    
    def _extract_topics(self, content: str) -> List[str]:
        """提取关键主题"""
        # 简单的关键词提取
        topics = []
        
        # 提取所有匹配的关键词
        content_lower = content.lower()
        for category, keywords in self.interest_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    topics.append(keyword)
        
        # 使用正则表达式提取可能的专有名词
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', content)
        topics.extend(proper_nouns[:5])  # 最多5个专有名词
        
        return list(set(topics))[:10]  # 去重并限制数量
    
    def _is_interesting(self, result: Dict[str, Any]) -> bool:
        """判断结果是否有趣"""
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        content = title + ' ' + snippet
        
        # 有趣内容的特征
        interesting_indicators = [
            '新发现', '突破', '创新', '惊人', '首次', '神奇',
            'breakthrough', 'amazing', 'incredible', 'discovery',
            '史上首次', '世界首个', '重大进展'
        ]
        
        return any(indicator in content for indicator in interesting_indicators)
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取网页主要内容"""
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 尝试找到主要内容区域
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        
        if main_content:
            content = main_content.get_text()
        else:
            # 获取所有段落文本
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text() for p in paragraphs])
        
        # 清理文本
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _generate_summary(self, analysis: Dict[str, Any]) -> str:
        """生成分析摘要"""
        summary_parts = []
        
        # 结果数量
        total = analysis['total_results']
        summary_parts.append(f"找到{total}个结果")
        
        # 主要类别
        if analysis['categories']:
            main_category = max(analysis['categories'], key=analysis['categories'].get)
            category_names = {
                'technology': '科技',
                'science': '科学',
                'entertainment': '娱乐',
                'news': '新闻',
                'learning': '学习',
                'general': '一般'
            }
            summary_parts.append(f"主要是{category_names.get(main_category, main_category)}类内容")
        
        # 情感倾向
        sentiment = analysis['sentiment']
        if sentiment['positive'] > sentiment['negative']:
            summary_parts.append("内容偏向积极")
        elif sentiment['negative'] > sentiment['positive']:
            summary_parts.append("内容偏向消极")
        else:
            summary_parts.append("内容相对中性")
        
        # 有趣结果
        if analysis['interesting_results']:
            count = len(analysis['interesting_results'])
            summary_parts.append(f"发现{count}个特别有趣的结果")
        
        return "，".join(summary_parts)
    
    def _record_analysis(self, analysis: Dict[str, Any]):
        """记录分析历史"""
        self.analysis_history.append({
            'timestamp': analysis['timestamp'],
            'total_results': analysis['total_results'],
            'main_category': max(analysis['categories'], key=analysis['categories'].get) if analysis['categories'] else 'unknown',
            'interesting_count': len(analysis['interesting_results'])
        })
        
        # 保持历史长度
        if len(self.analysis_history) > self.max_history:
            self.analysis_history = self.analysis_history[-self.max_history:]
    
    def get_analysis_trends(self) -> Dict[str, Any]:
        """获取分析趋势"""
        if not self.analysis_history:
            return {'total_analyses': 0}
        
        # 统计类别分布
        category_counts = {}
        total_interesting = 0
        
        for record in self.analysis_history:
            category = record['main_category']
            category_counts[category] = category_counts.get(category, 0) + 1
            total_interesting += record['interesting_count']
        
        return {
            'total_analyses': len(self.analysis_history),
            'category_distribution': category_counts,
            'average_interesting_per_analysis': total_interesting / len(self.analysis_history),
            'last_analysis_time': self.analysis_history[-1]['timestamp']
        }
    
    def find_related_content(self, topic: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据主题找到相关内容"""
        related_results = []
        topic_lower = topic.lower()
        
        for result in search_results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            # 计算相关度得分
            relevance_score = 0
            if topic_lower in title:
                relevance_score += 3
            if topic_lower in snippet:
                relevance_score += 2
            
            # 检查相关关键词
            for category, keywords in self.interest_keywords.items():
                if topic_lower in [kw.lower() for kw in keywords]:
                    for keyword in keywords:
                        if keyword.lower() in title or keyword.lower() in snippet:
                            relevance_score += 1
            
            if relevance_score > 0:
                result_copy = result.copy()
                result_copy['relevance_score'] = relevance_score
                related_results.append(result_copy)
        
        # 按相关度排序
        related_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return related_results[:5]  # 返回最相关的5个结果