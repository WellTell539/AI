"""
视觉感知模块 - 处理摄像头输入和图像分析
"""
import cv2
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import base64
import io
from PIL import Image
import threading
import time

from config.settings import settings

logger = logging.getLogger(__name__)

class VisualPerception:
    """
    视觉感知系统 - 负责摄像头捕获、图像分析和视觉理解
    """
    
    def __init__(self):
        self.camera = None
        self.is_active = False
        self.current_frame = None
        self.frame_history = []
        self.max_history_frames = 10
        
        # 分析结果缓存
        self.last_analysis = None
        self.analysis_timestamp = None
        
        # 检测到的对象和变化
        self.detected_objects = []
        self.motion_detected = False
        self.face_detected = False
        
        # 图像分析工具
        self.face_cascade = None
        self.background_subtractor = None
        
        # 线程控制
        self.capture_thread = None
        self.should_stop = False
        
        # 初始化
        self._initialize_opencv_tools()
    
    def _initialize_opencv_tools(self):
        """初始化OpenCV工具"""
        try:
            # 加载人脸检测器
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            
            # 初始化背景减法器（用于动作检测）
            self.background_subtractor = cv2.createBackgroundSubtractorMOG2()
            
            logger.info("OpenCV工具初始化成功")
        except Exception as e:
            logger.error(f"OpenCV工具初始化失败: {e}")
    
    def start_camera(self) -> bool:
        """启动摄像头"""
        if not settings.perception.camera_enabled:
            logger.info("摄像头功能已禁用")
            return False
        
        try:
            # 初始化摄像头
            self.camera = cv2.VideoCapture(settings.perception.camera_index)
            
            if not self.camera.isOpened():
                logger.error("无法打开摄像头")
                return False
            
            # 设置摄像头参数
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 15)
            
            self.is_active = True
            
            # 启动捕获线程
            self.should_stop = False
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.info("摄像头启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动摄像头失败: {e}")
            return False
    
    def stop_camera(self):
        """停止摄像头"""
        self.should_stop = True
        self.is_active = False
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        logger.info("摄像头已停止")
    
    def _capture_loop(self):
        """摄像头捕获循环"""
        while not self.should_stop and self.is_active:
            try:
                if self.camera and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret:
                        self.current_frame = frame
                        self._process_frame(frame)
                    else:
                        logger.warning("摄像头读取失败")
                        time.sleep(1)
                else:
                    logger.warning("摄像头未正常工作")
                    time.sleep(1)
                
                time.sleep(1.0 / 15)  # 15 FPS
                
            except Exception as e:
                logger.error(f"摄像头捕获出错: {e}")
                time.sleep(1)
    
    def _process_frame(self, frame):
        """处理单帧图像"""
        try:
            # 添加到历史
            self._add_to_history(frame)
            
            # 基础图像分析
            self._detect_faces(frame)
            self._detect_motion(frame)
            
        except Exception as e:
            logger.error(f"处理帧图像失败: {e}")
    
    def _add_to_history(self, frame):
        """添加帧到历史记录"""
        timestamp = datetime.now()
        self.frame_history.append({
            'frame': frame.copy(),
            'timestamp': timestamp
        })
        
        # 保持历史长度
        if len(self.frame_history) > self.max_history_frames:
            self.frame_history.pop(0)
    
    def _detect_faces(self, frame):
        """检测人脸"""
        if self.face_cascade is None:
            return
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                self.face_detected = True
                logger.debug(f"检测到 {len(faces)} 张人脸")
            else:
                self.face_detected = False
                
        except Exception as e:
            logger.error(f"人脸检测失败: {e}")
    
    def _detect_motion(self, frame):
        """检测运动"""
        if self.background_subtractor is None:
            return
        
        try:
            # 应用背景减法
            fg_mask = self.background_subtractor.apply(frame)
            
            # 计算运动像素数量
            motion_pixels = cv2.countNonZero(fg_mask)
            total_pixels = fg_mask.shape[0] * fg_mask.shape[1]
            motion_ratio = motion_pixels / total_pixels
            
            # 如果运动像素超过阈值，认为检测到运动
            if motion_ratio > 0.02:  # 2%的像素发生变化
                self.motion_detected = True
                logger.debug(f"检测到运动: {motion_ratio:.3f}")
            else:
                self.motion_detected = False
                
        except Exception as e:
            logger.error(f"运动检测失败: {e}")
    
    def capture_photo(self) -> Optional[str]:
        """拍摄照片并返回base64编码"""
        if not self.is_active or self.current_frame is None:
            logger.warning("摄像头未启动或无图像")
            return None
        
        try:
            # 转换为PIL图像
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # 转换为base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG', quality=85)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info("照片拍摄成功")
            return image_base64
            
        except Exception as e:
            logger.error(f"拍摄照片失败: {e}")
            return None
    
    def analyze_current_view(self) -> Dict[str, Any]:
        """分析当前视野"""
        if not self.is_active or self.current_frame is None:
            return {"status": "inactive", "message": "摄像头未启动"}
        
        try:
            analysis = {
                "timestamp": datetime.now(),
                "status": "active",
                "face_detected": self.face_detected,
                "motion_detected": self.motion_detected,
                "brightness": self._analyze_brightness(),
                "color_info": self._analyze_colors(),
                "scene_description": ""
            }
            
            # 生成场景描述
            description_parts = []
            
            if self.face_detected:
                description_parts.append("看到了人脸")
            
            if self.motion_detected:
                description_parts.append("检测到运动")
            
            brightness = analysis["brightness"]
            if brightness < 50:
                description_parts.append("环境较暗")
            elif brightness > 200:
                description_parts.append("环境很亮")
            else:
                description_parts.append("光线适中")
            
            if description_parts:
                analysis["scene_description"] = "，".join(description_parts)
            else:
                analysis["scene_description"] = "环境平静"
            
            self.last_analysis = analysis
            self.analysis_timestamp = datetime.now()
            
            return analysis
            
        except Exception as e:
            logger.error(f"视觉分析失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _analyze_brightness(self) -> float:
        """分析图像亮度"""
        if self.current_frame is None:
            return 0.0
        
        try:
            gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY)
            return float(np.mean(gray))
        except Exception as e:
            logger.error(f"亮度分析失败: {e}")
            return 0.0
    
    def _analyze_colors(self) -> Dict[str, float]:
        """分析图像颜色信息"""
        if self.current_frame is None:
            return {}
        
        try:
            # 计算各颜色通道的平均值
            b, g, r = cv2.split(self.current_frame)
            
            return {
                "red": float(np.mean(r)),
                "green": float(np.mean(g)),
                "blue": float(np.mean(b))
            }
        except Exception as e:
            logger.error(f"颜色分析失败: {e}")
            return {}
    
    def detect_changes(self) -> List[str]:
        """检测视觉变化"""
        changes = []
        
        # 检测人脸状态变化
        if hasattr(self, '_prev_face_detected'):
            if self.face_detected != self._prev_face_detected:
                if self.face_detected:
                    changes.append("有人出现在摄像头前")
                else:
                    changes.append("人离开了摄像头范围")
        self._prev_face_detected = self.face_detected
        
        # 检测运动状态变化
        if hasattr(self, '_prev_motion_detected'):
            if self.motion_detected != self._prev_motion_detected:
                if self.motion_detected:
                    changes.append("检测到新的运动")
                else:
                    changes.append("环境恢复静止")
        self._prev_motion_detected = self.motion_detected
        
        # 检测亮度显著变化
        current_brightness = self._analyze_brightness()
        if hasattr(self, '_prev_brightness'):
            brightness_diff = abs(current_brightness - self._prev_brightness)
            if brightness_diff > 30:  # 亮度变化超过30
                if current_brightness > self._prev_brightness:
                    changes.append("环境变亮了")
                else:
                    changes.append("环境变暗了")
        self._prev_brightness = current_brightness
        
        return changes
    
    def get_visual_summary(self) -> Dict[str, Any]:
        """获取视觉感知摘要"""
        return {
            "camera_active": self.is_active,
            "last_analysis": self.last_analysis,
            "analysis_time": self.analysis_timestamp,
            "face_detected": self.face_detected,
            "motion_detected": self.motion_detected,
            "frame_history_count": len(self.frame_history)
        }
    
    def save_current_frame(self, filename: str) -> bool:
        """保存当前帧到文件"""
        if self.current_frame is None:
            return False
        
        try:
            cv2.imwrite(filename, self.current_frame)
            logger.info(f"图像已保存到: {filename}")
            return True
        except Exception as e:
            logger.error(f"保存图像失败: {e}")
            return False
    
    def __del__(self):
        """析构函数"""
        self.stop_camera()