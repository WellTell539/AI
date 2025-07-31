"""
文件监控模块 - 监控文件系统变化和读取文件内容
"""
import os
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = None

from config.settings import settings

logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    """文件变化处理器"""
    
    def __init__(self, monitor):
        self.monitor = monitor
    
    def on_modified(self, event):
        if not event.is_directory:
            self.monitor._on_file_changed(event.src_path, "modified")
    
    def on_created(self, event):
        if not event.is_directory:
            self.monitor._on_file_changed(event.src_path, "created")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.monitor._on_file_changed(event.src_path, "deleted")
    
    def on_moved(self, event):
        if not event.is_directory:
            self.monitor._on_file_changed(event.dest_path, "moved")

class FileMonitor:
    """
    文件监控系统 - 监控文件系统变化和分析文件内容
    """
    
    def __init__(self):
        self.is_active = False
        self.observer = None
        self.event_handler = None
        
        # 监控目录
        self.monitored_directories = settings.perception.monitor_directories
        self.watched_paths = []
        
        # 文件变化记录
        self.file_changes = []
        self.max_change_history = 100
        
        # 文件内容缓存
        self.file_contents = {}
        self.interesting_files = set()
        
        # 允许和禁止的文件类型
        self.allowed_extensions = {
            '.txt', '.md', '.json', '.xml', '.log', '.csv',
            '.py', '.js', '.html', '.css', '.yaml', '.yml',
            '.ini', '.cfg', '.conf'
        }
        self.blocked_extensions = {
            '.exe', '.dll', '.sys', '.bat', '.cmd', '.scr',
            '.com', '.pif', '.bin', '.iso', '.img'
        }
        
        # 线程控制
        self.analysis_thread = None
        self.should_stop = False
        
        # 统计信息
        self.stats = {
            "files_monitored": 0,
            "changes_detected": 0,
            "files_analyzed": 0,
            "interesting_content_found": 0
        }
    
    def start_monitoring(self) -> bool:
        """开始文件监控"""
        if not settings.perception.file_monitor_enabled:
            logger.info("文件监控功能已禁用")
            return False
        
        if Observer is None:
            logger.error("watchdog模块未安装，无法进行文件监控")
            return False
        
        try:
            # 创建观察者和事件处理器
            self.observer = Observer()
            self.event_handler = FileChangeHandler(self)
            
            # 添加监控目录
            for directory in self.monitored_directories:
                if os.path.exists(directory) and os.path.isdir(directory):
                    self.observer.schedule(self.event_handler, directory, recursive=True)
                    self.watched_paths.append(directory)
                    logger.info(f"开始监控目录: {directory}")
                else:
                    logger.warning(f"监控目录不存在: {directory}")
            
            if not self.watched_paths:
                logger.warning("没有有效的监控目录")
                return False
            
            # 启动观察者
            self.observer.start()
            self.is_active = True
            self.should_stop = False
            
            # 启动分析线程
            self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
            self.analysis_thread.start()
            
            # 初始扫描
            self._initial_scan()
            
            logger.info("文件监控已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            return False
    
    def stop_monitoring(self):
        """停止文件监控"""
        self.should_stop = True
        self.is_active = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=5)
        
        logger.info("文件监控已停止")
    
    def _initial_scan(self):
        """初始扫描现有文件"""
        try:
            for directory in self.watched_paths:
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._is_interesting_file(file_path):
                            self.interesting_files.add(file_path)
                            self.stats["files_monitored"] += 1
            
            logger.info(f"初始扫描完成，发现 {len(self.interesting_files)} 个感兴趣的文件")
            
        except Exception as e:
            logger.error(f"初始扫描失败: {e}")
    
    def _analysis_loop(self):
        """文件分析循环"""
        while not self.should_stop and self.is_active:
            try:
                # 分析新发现的有趣文件
                self._analyze_interesting_files()
                
                # 清理过期的变化记录
                self._cleanup_old_changes()
                
                time.sleep(30)  # 每30秒分析一次
                
            except Exception as e:
                logger.error(f"文件分析循环出错: {e}")
                time.sleep(60)
    
    def _on_file_changed(self, file_path: str, change_type: str):
        """处理文件变化事件"""
        try:
            # 检查文件是否在黑名单中
            if not self._is_allowed_file(file_path):
                return
            
            # 记录变化
            change_record = {
                "file_path": file_path,
                "change_type": change_type,
                "timestamp": datetime.now(),
                "analyzed": False
            }
            
            self.file_changes.append(change_record)
            self.stats["changes_detected"] += 1
            
            # 保持变化记录长度
            if len(self.file_changes) > self.max_change_history:
                self.file_changes.pop(0)
            
            # 如果是有趣的文件，添加到分析队列
            if self._is_interesting_file(file_path):
                self.interesting_files.add(file_path)
            
            logger.debug(f"文件变化: {change_type} - {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件变化失败: {e}")
    
    def _is_allowed_file(self, file_path: str) -> bool:
        """检查文件是否允许访问"""
        try:
            # 检查文件扩展名
            ext = Path(file_path).suffix.lower()
            
            if ext in self.blocked_extensions:
                return False
            
            # 检查文件大小（避免分析过大的文件）
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB限制
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查文件权限失败: {e}")
            return False
    
    def _is_interesting_file(self, file_path: str) -> bool:
        """判断文件是否有趣（值得分析）"""
        try:
            ext = Path(file_path).suffix.lower()
            
            # 检查是否是允许的文件类型
            if ext not in self.allowed_extensions:
                return False
            
            # 检查文件名是否包含有趣的关键词
            file_name = Path(file_path).name.lower()
            interesting_keywords = [
                'diary', 'note', 'todo', 'plan', 'idea', 'log',
                '日记', '笔记', '计划', '想法', '记录'
            ]
            
            for keyword in interesting_keywords:
                if keyword in file_name:
                    return True
            
            # 检查是否是最近修改的文件
            if os.path.exists(file_path):
                mtime = os.path.getmtime(file_path)
                current_time = time.time()
                if current_time - mtime < 86400:  # 24小时内修改
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"判断文件是否有趣失败: {e}")
            return False
    
    def _analyze_interesting_files(self):
        """分析有趣的文件"""
        files_to_analyze = list(self.interesting_files)[:5]  # 每次最多分析5个文件
        
        for file_path in files_to_analyze:
            try:
                if not os.path.exists(file_path):
                    self.interesting_files.discard(file_path)
                    continue
                
                content = self._read_file_content(file_path)
                if content:
                    self.file_contents[file_path] = {
                        "content": content,
                        "analyzed_at": datetime.now(),
                        "summary": self._analyze_content(content)
                    }
                    self.stats["files_analyzed"] += 1
                
                # 从队列中移除已分析的文件
                self.interesting_files.discard(file_path)
                
            except Exception as e:
                logger.error(f"分析文件失败 {file_path}: {e}")
                self.interesting_files.discard(file_path)
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        
                    # 限制内容长度
                    if len(content) > 10000:  # 10K字符限制
                        content = content[:10000] + "...[内容被截断]"
                    
                    return content
                    
                except UnicodeDecodeError:
                    continue
            
            logger.warning(f"无法读取文件内容: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return None
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """分析文件内容"""
        try:
            analysis = {
                "character_count": len(content),
                "line_count": content.count('\\n') + 1,
                "contains_personal_info": False,
                "content_type": "unknown",
                "interesting_keywords": [],
                "summary": ""
            }
            
            content_lower = content.lower()
            
            # 检测内容类型
            if any(keyword in content_lower for keyword in ['def ', 'class ', 'import ', 'function']):
                analysis["content_type"] = "code"
            elif any(keyword in content_lower for keyword in ['日记', 'diary', '今天', 'today']):
                analysis["content_type"] = "diary"
            elif any(keyword in content_lower for keyword in ['todo', '待办', '计划', 'plan']):
                analysis["content_type"] = "planning"
            elif content.startswith('{') or content.startswith('['):
                analysis["content_type"] = "data"
            
            # 检测个人信息（简单检测）
            personal_keywords = ['密码', 'password', '身份证', '银行', '信用卡']
            if any(keyword in content_lower for keyword in personal_keywords):
                analysis["contains_personal_info"] = True
            
            # 提取有趣的关键词
            interesting_keywords = [
                '项目', '计划', '想法', '创意', '目标', '梦想',
                'project', 'plan', 'idea', 'creative', 'goal', 'dream'
            ]
            
            found_keywords = []
            for keyword in interesting_keywords:
                if keyword in content_lower:
                    found_keywords.append(keyword)
            
            analysis["interesting_keywords"] = found_keywords[:10]  # 最多10个关键词
            
            # 生成简单摘要
            lines = content.split('\\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            if non_empty_lines:
                summary_lines = non_empty_lines[:3]  # 前三行非空内容
                analysis["summary"] = " | ".join(summary_lines)[:200] + "..."
            
            if found_keywords:
                self.stats["interesting_content_found"] += 1
            
            return analysis
            
        except Exception as e:
            logger.error(f"内容分析失败: {e}")
            return {"error": str(e)}
    
    def _cleanup_old_changes(self):
        """清理过期的变化记录"""
        try:
            cutoff_time = datetime.now().timestamp() - 86400  # 24小时前
            
            self.file_changes = [
                change for change in self.file_changes
                if change["timestamp"].timestamp() > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"清理过期记录失败: {e}")
    
    def get_recent_changes(self, hours: int = 1) -> List[Dict[str, Any]]:
        """获取最近的文件变化"""
        try:
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            
            recent_changes = [
                change for change in self.file_changes
                if change["timestamp"].timestamp() > cutoff_time
            ]
            
            return recent_changes[-20:]  # 最多返回20个变化
            
        except Exception as e:
            logger.error(f"获取最近变化失败: {e}")
            return []
    
    def get_interesting_content(self) -> List[Dict[str, Any]]:
        """获取有趣的文件内容"""
        try:
            interesting_content = []
            
            for file_path, file_info in self.file_contents.items():
                if file_info["summary"].get("interesting_keywords"):
                    interesting_content.append({
                        "file_path": file_path,
                        "content_type": file_info["summary"].get("content_type", "unknown"),
                        "keywords": file_info["summary"].get("interesting_keywords", []),
                        "summary": file_info["summary"].get("summary", ""),
                        "analyzed_at": file_info["analyzed_at"]
                    })
            
            # 按分析时间排序，最新的在前
            interesting_content.sort(key=lambda x: x["analyzed_at"], reverse=True)
            
            return interesting_content[:10]  # 最多返回10个
            
        except Exception as e:
            logger.error(f"获取有趣内容失败: {e}")
            return []
    
    def analyze_file_changes(self) -> Dict[str, Any]:
        """分析文件变化趋势"""
        if not self.is_active:
            return {"status": "inactive", "message": "文件监控未启动"}
        
        try:
            recent_changes = self.get_recent_changes(hours=6)  # 最近6小时
            
            analysis = {
                "timestamp": datetime.now(),
                "status": "active",
                "recent_changes_count": len(recent_changes),
                "change_types": {},
                "active_directories": set(),
                "interesting_files_found": len(self.get_interesting_content()),
                "description": ""
            }
            
            # 统计变化类型
            for change in recent_changes:
                change_type = change["change_type"]
                analysis["change_types"][change_type] = analysis["change_types"].get(change_type, 0) + 1
                
                # 记录活跃目录
                dir_path = os.path.dirname(change["file_path"])
                analysis["active_directories"].add(dir_path)
            
            analysis["active_directories"] = list(analysis["active_directories"])
            
            # 生成描述
            description_parts = []
            
            if len(recent_changes) > 10:
                description_parts.append("文件活动频繁")
            elif len(recent_changes) > 5:
                description_parts.append("有一定的文件活动")
            else:
                description_parts.append("文件活动较少")
            
            if analysis["interesting_files_found"] > 0:
                description_parts.append(f"发现{analysis['interesting_files_found']}个有趣文件")
            
            most_common_change = max(analysis["change_types"].items(), 
                                   key=lambda x: x[1], default=("", 0))
            if most_common_change[1] > 0:
                description_parts.append(f"主要是{most_common_change[0]}操作")
            
            analysis["description"] = "，".join(description_parts)
            
            return analysis
            
        except Exception as e:
            logger.error(f"文件变化分析失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_file_monitor_summary(self) -> Dict[str, Any]:
        """获取文件监控摘要"""
        return {
            "monitor_active": self.is_active,
            "watched_directories": self.watched_paths,
            "statistics": self.stats.copy(),
            "recent_changes": len(self.get_recent_changes()),
            "interesting_files": len(self.get_interesting_content())
        }
    
    def search_file_content(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索文件内容"""
        try:
            results = []
            keyword_lower = keyword.lower()
            
            for file_path, file_info in self.file_contents.items():
                content = file_info["content"].lower()
                if keyword_lower in content:
                    # 找到关键词所在的行
                    lines = file_info["content"].split('\\n')
                    matching_lines = []
                    
                    for i, line in enumerate(lines):
                        if keyword_lower in line.lower():
                            matching_lines.append(f"第{i+1}行: {line.strip()}")
                    
                    results.append({
                        "file_path": file_path,
                        "matching_lines": matching_lines[:5],  # 最多5行
                        "content_type": file_info["summary"].get("content_type", "unknown")
                    })
            
            return results[:10]  # 最多返回10个结果
            
        except Exception as e:
            logger.error(f"搜索文件内容失败: {e}")
            return []
    
    def __del__(self):
        """析构函数"""
        self.stop_monitoring()