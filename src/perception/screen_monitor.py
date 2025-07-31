"""
屏幕监控模块 - 监控和分析屏幕内容
"""
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import base64
import io

try:
    import pyautogui
    import mss
except ImportError:
    pyautogui = None
    mss = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

import numpy as np

from config.settings import settings

logger = logging.getLogger(__name__)

class ScreenMonitor:
    """
    屏幕监控系统 - 负责捕获和分析屏幕内容
    """
    
    def __init__(self):
        self.is_active = False
        self.current_screenshot = None
        self.screenshot_history = []
        self.max_history_screenshots = 10
        
        # 监控区域
        self.monitor_region = settings.perception.screen_region
        self.screen_size = None
        
        # 分析结果
        self.detected_windows = []
        self.text_content = ""
        self.screen_activity = 0.0
        self.last_change_time = None
        
        # 线程控制
        self.monitor_thread = None
        self.should_stop = False
        
        # 变化检测
        self.previous_screenshot = None
        self.change_threshold = 0.05  # 5%的像素变化认为有显著变化
        
        # 初始化
        self._initialize_screen_tools()
    
    def _initialize_screen_tools(self):
        """初始化屏幕工具"""
        if not settings.perception.screen_capture_enabled:
            logger.info("屏幕监控功能已禁用")
            return
        
        try:
            if pyautogui is None:
                logger.error("pyautogui模块未安装")
                return
            
            # 获取屏幕尺寸
            self.screen_size = pyautogui.size()
            
            # 如果未指定监控区域，使用全屏
            if self.monitor_region is None:
                self.monitor_region = (0, 0, self.screen_size.width, self.screen_size.height)
            
            # 禁用pyautogui的安全机制（防止意外移动到屏幕角落）
            pyautogui.FAILSAFE = False
            
            logger.info(f"屏幕监控工具初始化成功，屏幕尺寸: {self.screen_size}")
            
        except Exception as e:
            logger.error(f"屏幕监控工具初始化失败: {e}")
    
    def start_monitoring(self) -> bool:
        """开始屏幕监控"""
        if not settings.perception.screen_capture_enabled:
            logger.info("屏幕监控功能已禁用")
            return False
        
        if pyautogui is None:
            logger.error("屏幕监控工具未正确初始化")
            return False
        
        try:
            self.is_active = True
            self.should_stop = False
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            logger.info("屏幕监控已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动屏幕监控失败: {e}")
            return False
    
    def stop_monitoring(self):
        """停止屏幕监控"""
        self.should_stop = True
        self.is_active = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("屏幕监控已停止")
    
    def _monitoring_loop(self):
        """屏幕监控循环"""
        while not self.should_stop and self.is_active:
            try:
                # 截取屏幕
                screenshot = self._capture_screen()
                if screenshot:
                    self._process_screenshot(screenshot)
                
                # 等待指定间隔
                time.sleep(settings.perception.screen_capture_interval)
                
            except Exception as e:
                logger.error(f"屏幕监控循环出错: {e}")
                time.sleep(5)  # 出错后等待更长时间
    
    def _capture_screen(self) -> Optional[Image.Image]:
        """捕获屏幕截图"""
        try:
            if mss:
                # 使用mss进行更高效的截图
                with mss.mss() as sct:
                    # 定义截图区域
                    monitor = {
                        "top": self.monitor_region[1],
                        "left": self.monitor_region[0],
                        "width": self.monitor_region[2],
                        "height": self.monitor_region[3]
                    }
                    
                    # 截图
                    screenshot = sct.grab(monitor)
                    
                    # 转换为PIL图像
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    return img
            else:
                # 使用pyautogui截图
                screenshot = pyautogui.screenshot(region=self.monitor_region)
                return screenshot
                
        except Exception as e:
            logger.error(f"屏幕截图失败: {e}")
            return None
    
    def _process_screenshot(self, screenshot: Image.Image):
        """处理屏幕截图"""
        try:
            # 更新当前截图
            self.current_screenshot = screenshot
            
            # 添加到历史
            self._add_to_history(screenshot)
            
            # 检测变化
            self._detect_screen_changes(screenshot)
            
            # 分析屏幕内容
            self._analyze_screen_content(screenshot)
            
        except Exception as e:
            logger.error(f"处理屏幕截图失败: {e}")
    
    def _add_to_history(self, screenshot: Image.Image):
        """添加截图到历史记录"""
        timestamp = datetime.now()
        self.screenshot_history.append({
            'screenshot': screenshot.copy(),
            'timestamp': timestamp
        })
        
        # 保持历史长度
        if len(self.screenshot_history) > self.max_history_screenshots:
            self.screenshot_history.pop(0)
    
    def _detect_screen_changes(self, screenshot: Image.Image):
        """检测屏幕变化"""
        try:
            if self.previous_screenshot is None:
                self.previous_screenshot = screenshot
                return
            
            # 将图像转换为numpy数组进行比较
            current_array = np.array(screenshot)
            previous_array = np.array(self.previous_screenshot)
            
            # 计算像素差异
            diff = np.abs(current_array.astype(float) - previous_array.astype(float))
            
            # 计算变化的像素比例
            total_pixels = diff.size // 3  # RGB三个通道
            changed_pixels = np.sum(diff > 30) // 3  # 阈值30，认为有显著变化
            change_ratio = changed_pixels / total_pixels
            
            self.screen_activity = change_ratio
            
            # 如果变化超过阈值，记录变化时间
            if change_ratio > self.change_threshold:
                self.last_change_time = datetime.now()
                logger.debug(f"检测到屏幕变化: {change_ratio:.3f}")
            
            # 更新前一帧
            self.previous_screenshot = screenshot
            
        except Exception as e:
            logger.error(f"屏幕变化检测失败: {e}")
    
    def _analyze_screen_content(self, screenshot: Image.Image):
        """分析屏幕内容"""
        try:
            # 这里可以添加更复杂的屏幕内容分析
            # 比如OCR文字识别、窗口检测等
            
            # 简单的窗口检测（基于颜色变化）
            self._detect_windows(screenshot)
            
        except Exception as e:
            logger.error(f"屏幕内容分析失败: {e}")
    
    def _detect_windows(self, screenshot: Image.Image):
        """检测屏幕上的窗口"""
        try:
            # 简单的窗口检测逻辑
            # 这里可以扩展为更复杂的窗口识别算法
            
            # 转换为灰度图像
            gray = screenshot.convert('L')
            
            # 检测边缘（窗口边框）
            gray_array = np.array(gray)
            
            # 简单的边缘检测
            edges_h = np.abs(np.diff(gray_array, axis=1))
            edges_v = np.abs(np.diff(gray_array, axis=0))
            
            # 统计边缘强度
            edge_strength = np.mean(edges_h) + np.mean(edges_v)
            
            # 根据边缘强度估计窗口数量
            estimated_windows = max(1, int(edge_strength / 10))
            
            self.detected_windows = [f"窗口{i+1}" for i in range(min(estimated_windows, 5))]
            
        except Exception as e:
            logger.error(f"窗口检测失败: {e}")
    
    def capture_current_screen(self) -> Optional[str]:
        """捕获当前屏幕并返回base64编码"""
        try:
            screenshot = self._capture_screen()
            if screenshot is None:
                return None
            
            # 转换为base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info("屏幕截图成功")
            return image_base64
            
        except Exception as e:
            logger.error(f"屏幕截图失败: {e}")
            return None
    
    def analyze_current_screen(self) -> Dict[str, Any]:
        """分析当前屏幕状态"""
        if not self.is_active:
            return {"status": "inactive", "message": "屏幕监控未启动"}
        
        try:
            analysis = {
                "timestamp": datetime.now(),
                "status": "active",
                "screen_activity": self.screen_activity,
                "last_change": self.last_change_time,
                "detected_windows": self.detected_windows,
                "screen_info": self._get_screen_info(),
                "description": ""
            }
            
            # 生成屏幕状态描述
            description_parts = []
            
            if self.screen_activity > 0.1:
                description_parts.append("屏幕有活动")
            elif self.screen_activity > 0.05:
                description_parts.append("屏幕有轻微变化")
            else:
                description_parts.append("屏幕相对静止")
            
            if self.detected_windows:
                window_count = len(self.detected_windows)
                description_parts.append(f"检测到{window_count}个窗口")
            
            if self.last_change_time:
                time_since_change = (datetime.now() - self.last_change_time).total_seconds()
                if time_since_change < 60:
                    description_parts.append(f"{int(time_since_change)}秒前有变化")
            
            analysis["description"] = "，".join(description_parts)
            
            return analysis
            
        except Exception as e:
            logger.error(f"屏幕分析失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_screen_info(self) -> Dict[str, Any]:
        """获取屏幕基本信息"""
        try:
            if pyautogui:
                mouse_pos = pyautogui.position()
                return {
                    "screen_size": self.screen_size._asdict() if self.screen_size else None,
                    "mouse_position": {"x": mouse_pos.x, "y": mouse_pos.y},
                    "monitor_region": self.monitor_region
                }
            else:
                return {
                    "screen_size": None,
                    "mouse_position": None,
                    "monitor_region": self.monitor_region
                }
        except Exception as e:
            logger.error(f"获取屏幕信息失败: {e}")
            return {}
    
    def detect_screen_changes(self) -> List[str]:
        """检测屏幕变化"""
        changes = []
        
        # 检测活动水平变化
        if hasattr(self, '_prev_screen_activity'):
            activity_diff = abs(self.screen_activity - self._prev_screen_activity)
            if activity_diff > 0.1:
                if self.screen_activity > self._prev_screen_activity:
                    changes.append("屏幕活动增加")
                else:
                    changes.append("屏幕活动减少")
        self._prev_screen_activity = self.screen_activity
        
        # 检测窗口数量变化
        if hasattr(self, '_prev_window_count'):
            current_window_count = len(self.detected_windows)
            if current_window_count != self._prev_window_count:
                if current_window_count > self._prev_window_count:
                    changes.append("有新窗口打开")
                else:
                    changes.append("有窗口关闭")
        self._prev_window_count = len(self.detected_windows)
        
        return changes
    
    def get_screen_summary(self) -> Dict[str, Any]:
        """获取屏幕监控摘要"""
        return {
            "monitor_active": self.is_active,
            "screen_activity": self.screen_activity,
            "last_change": self.last_change_time,
            "detected_windows_count": len(self.detected_windows),
            "monitor_region": self.monitor_region,
            "screenshot_history_count": len(self.screenshot_history)
        }
    
    def save_current_screenshot(self, filename: str) -> bool:
        """保存当前屏幕截图到文件"""
        if self.current_screenshot is None:
            return False
        
        try:
            self.current_screenshot.save(filename)
            logger.info(f"屏幕截图已保存到: {filename}")
            return True
        except Exception as e:
            logger.error(f"保存屏幕截图失败: {e}")
            return False
    
    def get_mouse_position(self) -> Optional[Tuple[int, int]]:
        """获取鼠标位置"""
        try:
            if pyautogui:
                pos = pyautogui.position()
                return (pos.x, pos.y)
            return None
        except Exception as e:
            logger.error(f"获取鼠标位置失败: {e}")
            return None
    
    def is_user_active(self) -> bool:
        """判断用户是否在活动"""
        # 基于屏幕变化和鼠标活动判断用户是否在使用电脑
        try:
            # 如果最近有屏幕变化，认为用户在活动
            if self.last_change_time:
                time_since_change = (datetime.now() - self.last_change_time).total_seconds()
                return time_since_change < 300  # 5分钟内有变化
            
            return False
        except Exception:
            return False
    
    def __del__(self):
        """析构函数"""
        self.stop_monitoring()