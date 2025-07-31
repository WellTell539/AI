"""
增强视觉感知模块 - 物体识别和场景理解
"""
import logging
import requests
import base64
import io
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from PIL import Image
except ImportError:
    Image = None

from config.settings import settings

logger = logging.getLogger(__name__)

class EnhancedVision:
    """增强视觉系统 - 支持物体识别、场景理解、OCR等"""
    
    def __init__(self):
        self.vision_services = {
            'google': self._analyze_with_google_vision,
            'azure': self._analyze_with_azure_vision,
            'openai': self._analyze_with_openai_vision
        }
        
        # 分析历史
        self.analysis_history = []
        self.max_history = 50
        
        # 物体分类映射
        self.object_categories = {
            'person': '人物',
            'animal': '动物',
            'vehicle': '交通工具',
            'furniture': '家具',
            'food': '食物',
            'nature': '自然景观',
            'building': '建筑',
            'electronics': '电子设备',
            'text': '文字内容'
        }
    
    def analyze_image(self, image_data: bytes, service: str = 'google') -> Dict[str, Any]:
        """分析图像 - 检测物体、理解场景"""
        try:
            if service not in self.vision_services:
                service = 'google'  # 默认使用Google Vision
            
            # 选择分析服务
            analysis_func = self.vision_services[service]
            result = analysis_func(image_data)
            
            # 记录分析历史
            self._record_analysis(result, service)
            
            return result
            
        except Exception as e:
            logger.error(f"图像分析失败: {e}")
            return self._get_fallback_analysis(image_data)
    
    def _analyze_with_google_vision(self, image_data: bytes) -> Dict[str, Any]:
        """使用Google Vision API分析图像"""
        try:
            api_key = getattr(settings.ai, 'google_vision_api_key', '')
            if not api_key:
                return self._get_fallback_analysis(image_data)
            
            # 编码图像为base64
            image_base64 = base64.b64encode(image_data).decode()
            
            url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
            
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                            {"type": "LABEL_DETECTION", "maxResults": 10},
                            {"type": "FACE_DETECTION", "maxResults": 10},
                            {"type": "TEXT_DETECTION", "maxResults": 5},
                            {"type": "LANDMARK_DETECTION", "maxResults": 5}
                        ]
                    }
                ]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_google_vision_response(data)
            
        except Exception as e:
            logger.error(f"Google Vision分析失败: {e}")
            return self._get_fallback_analysis(image_data)
    
    def _analyze_with_azure_vision(self, image_data: bytes) -> Dict[str, Any]:
        """使用Azure Computer Vision分析图像"""
        try:
            api_key = getattr(settings.ai, 'azure_vision_key', '')
            endpoint = getattr(settings.ai, 'azure_vision_endpoint', '')
            
            if not api_key or not endpoint:
                return self._get_fallback_analysis(image_data)
            
            url = f"{endpoint}/vision/v3.2/analyze"
            
            headers = {
                'Ocp-Apim-Subscription-Key': api_key,
                'Content-Type': 'application/octet-stream'
            }
            
            params = {
                'visualFeatures': 'Categories,Description,Objects,Faces,Tags,Color,Adult',
                'details': 'Landmarks,Celebrities'
            }
            
            response = requests.post(url, headers=headers, params=params, 
                                   data=image_data, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_azure_vision_response(data)
            
        except Exception as e:
            logger.error(f"Azure Vision分析失败: {e}")
            return self._get_fallback_analysis(image_data)
    
    def _analyze_with_openai_vision(self, image_data: bytes) -> Dict[str, Any]:
        """使用OpenAI GPT-4V分析图像"""
        try:
            api_key = getattr(settings.ai, 'openai_api_key', '')
            if not api_key:
                return self._get_fallback_analysis(image_data)
            
            # 编码图像为base64
            image_base64 = base64.b64encode(image_data).decode()
            
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请详细分析这张图片，包括：1.主要物体和人物 2.场景和环境 3.情绪氛围 4.有趣的细节。用中文回答。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_openai_vision_response(data)
            
        except Exception as e:
            logger.error(f"OpenAI Vision分析失败: {e}")
            return self._get_fallback_analysis(image_data)
    
    def _parse_google_vision_response(self, data: Dict) -> Dict[str, Any]:
        """解析Google Vision API响应"""
        result = {
            'service': 'google_vision',
            'timestamp': datetime.now(),
            'objects': [],
            'labels': [],
            'faces': [],
            'text': '',
            'landmarks': [],
            'scene_description': '',
            'confidence_score': 0.0
        }
        
        try:
            responses = data.get('responses', [])
            if not responses:
                return result
            
            response = responses[0]
            
            # 解析物体检测
            if 'localizedObjectAnnotations' in response:
                for obj in response['localizedObjectAnnotations']:
                    result['objects'].append({
                        'name': obj.get('name', ''),
                        'confidence': obj.get('score', 0.0),
                        'category': self._categorize_object(obj.get('name', ''))
                    })
            
            # 解析标签
            if 'labelAnnotations' in response:
                for label in response['labelAnnotations']:
                    result['labels'].append({
                        'name': label.get('description', ''),
                        'confidence': label.get('score', 0.0)
                    })
            
            # 解析人脸
            if 'faceAnnotations' in response:
                result['faces'] = [{
                    'emotions': self._parse_face_emotions(face),
                    'confidence': face.get('detectionConfidence', 0.0)
                } for face in response['faceAnnotations']]
            
            # 解析文字
            if 'textAnnotations' in response:
                texts = [t.get('description', '') for t in response['textAnnotations']]
                result['text'] = ' '.join(texts)
            
            # 生成场景描述
            result['scene_description'] = self._generate_scene_description(result)
            result['confidence_score'] = self._calculate_confidence(result)
            
        except Exception as e:
            logger.error(f"解析Google Vision响应失败: {e}")
        
        return result
    
    def _parse_azure_vision_response(self, data: Dict) -> Dict[str, Any]:
        """解析Azure Vision响应"""
        result = {
            'service': 'azure_vision',
            'timestamp': datetime.now(),
            'objects': [],
            'labels': [],
            'faces': [],
            'text': '',
            'scene_description': '',
            'confidence_score': 0.0
        }
        
        try:
            # 解析物体
            if 'objects' in data:
                for obj in data['objects']:
                    result['objects'].append({
                        'name': obj.get('object', ''),
                        'confidence': obj.get('confidence', 0.0),
                        'category': self._categorize_object(obj.get('object', ''))
                    })
            
            # 解析标签
            if 'tags' in data:
                for tag in data['tags']:
                    result['labels'].append({
                        'name': tag.get('name', ''),
                        'confidence': tag.get('confidence', 0.0)
                    })
            
            # 解析人脸
            if 'faces' in data:
                result['faces'] = [{
                    'age': face.get('age', 0),
                    'gender': face.get('gender', ''),
                    'confidence': 0.8  # Azure不提供人脸检测置信度
                } for face in data['faces']]
            
            # 解析描述
            if 'description' in data and 'captions' in data['description']:
                captions = data['description']['captions']
                if captions:
                    result['scene_description'] = captions[0].get('text', '')
                    result['confidence_score'] = captions[0].get('confidence', 0.0)
            
        except Exception as e:
            logger.error(f"解析Azure Vision响应失败: {e}")
        
        return result
    
    def _parse_openai_vision_response(self, data: Dict) -> Dict[str, Any]:
        """解析OpenAI Vision响应"""
        result = {
            'service': 'openai_vision',
            'timestamp': datetime.now(),
            'objects': [],
            'labels': [],
            'faces': [],
            'text': '',
            'scene_description': '',
            'confidence_score': 0.8  # OpenAI不提供置信度
        }
        
        try:
            choices = data.get('choices', [])
            if choices:
                content = choices[0].get('message', {}).get('content', '')
                result['scene_description'] = content
                
                # 从描述中提取关键信息
                result['objects'] = self._extract_objects_from_description(content)
                result['labels'] = self._extract_labels_from_description(content)
            
        except Exception as e:
            logger.error(f"解析OpenAI Vision响应失败: {e}")
        
        return result
    
    def _categorize_object(self, object_name: str) -> str:
        """将物体分类"""
        object_name_lower = object_name.lower()
        
        # 简单的分类逻辑
        if any(word in object_name_lower for word in ['person', 'man', 'woman', 'child', 'people']):
            return self.object_categories['person']
        elif any(word in object_name_lower for word in ['dog', 'cat', 'bird', 'animal']):
            return self.object_categories['animal']
        elif any(word in object_name_lower for word in ['car', 'bus', 'truck', 'bicycle']):
            return self.object_categories['vehicle']
        elif any(word in object_name_lower for word in ['chair', 'table', 'sofa', 'bed']):
            return self.object_categories['furniture']
        elif any(word in object_name_lower for word in ['food', 'drink', 'fruit', 'meal']):
            return self.object_categories['food']
        elif any(word in object_name_lower for word in ['tree', 'flower', 'grass', 'sky']):
            return self.object_categories['nature']
        elif any(word in object_name_lower for word in ['building', 'house', 'office']):
            return self.object_categories['building']
        elif any(word in object_name_lower for word in ['phone', 'computer', 'screen']):
            return self.object_categories['electronics']
        else:
            return '其他'
    
    def _parse_face_emotions(self, face_data: Dict) -> Dict[str, float]:
        """解析人脸情绪"""
        emotions = {}
        emotion_mapping = {
            'joyLikelihood': '快乐',
            'sorrowLikelihood': '悲伤',
            'angerLikelihood': '愤怒',
            'surpriseLikelihood': '惊讶'
        }
        
        for api_emotion, chinese_emotion in emotion_mapping.items():
            likelihood = face_data.get(api_emotion, 'UNKNOWN')
            emotions[chinese_emotion] = self._likelihood_to_score(likelihood)
        
        return emotions
    
    def _likelihood_to_score(self, likelihood: str) -> float:
        """将可能性转换为分数"""
        likelihood_scores = {
            'VERY_LIKELY': 0.9,
            'LIKELY': 0.7,
            'POSSIBLE': 0.5,
            'UNLIKELY': 0.3,
            'VERY_UNLIKELY': 0.1
        }
        return likelihood_scores.get(likelihood, 0.0)
    
    def _generate_scene_description(self, analysis_result: Dict) -> str:
        """生成场景描述"""
        parts = []
        
        # 描述主要物体
        if analysis_result['objects']:
            obj_names = [obj['name'] for obj in analysis_result['objects'][:3]]
            parts.append(f"看到了{', '.join(obj_names)}")
        
        # 描述人脸
        if analysis_result['faces']:
            face_count = len(analysis_result['faces'])
            parts.append(f"发现{face_count}个人脸")
        
        # 描述环境
        if analysis_result['labels']:
            env_labels = [label['name'] for label in analysis_result['labels'][:3]]
            parts.append(f"环境特征：{', '.join(env_labels)}")
        
        return "，".join(parts) if parts else "这是一个有趣的场景"
    
    def _calculate_confidence(self, analysis_result: Dict) -> float:
        """计算整体置信度"""
        confidences = []
        
        for obj in analysis_result['objects']:
            confidences.append(obj['confidence'])
        
        for label in analysis_result['labels']:
            confidences.append(label['confidence'])
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _extract_objects_from_description(self, description: str) -> List[Dict]:
        """从描述中提取物体信息"""
        # 简单的关键词匹配
        objects = []
        keywords = ['人', '车', '建筑', '动物', '植物', '食物', '家具']
        
        for keyword in keywords:
            if keyword in description:
                objects.append({
                    'name': keyword,
                    'confidence': 0.7,
                    'category': keyword
                })
        
        return objects
    
    def _extract_labels_from_description(self, description: str) -> List[Dict]:
        """从描述中提取标签"""
        # 简单的关键词提取
        labels = []
        keywords = ['室内', '室外', '白天', '夜晚', '明亮', '昏暗']
        
        for keyword in keywords:
            if keyword in description:
                labels.append({
                    'name': keyword,
                    'confidence': 0.6
                })
        
        return labels
    
    def _get_fallback_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """本地图像分析回退方案"""
        result = {
            'service': 'local_fallback',
            'timestamp': datetime.now(),
            'objects': [],
            'labels': [],
            'faces': [],
            'text': '',
            'scene_description': '正在本地分析图像...',
            'confidence_score': 0.3
        }
        
        try:
            if cv2 is not None and Image is not None:
                # 使用OpenCV进行基础分析
                result = self._basic_opencv_analysis(image_data)
        except Exception as e:
            logger.error(f"本地图像分析失败: {e}")
        
        return result
    
    def _basic_opencv_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """使用OpenCV进行基础图像分析"""
        result = {
            'service': 'opencv_local',
            'timestamp': datetime.now(),
            'objects': [],
            'labels': [],
            'faces': [],
            'text': '',
            'scene_description': '',
            'confidence_score': 0.5
        }
        
        try:
            # 将字节转换为numpy数组
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return result
            
            # 基础人脸检测
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            result['faces'] = [{'confidence': 0.7} for _ in faces]
            
            # 基础色彩分析
            avg_color = np.mean(img, axis=(0, 1))
            brightness = np.mean(avg_color)
            
            if brightness > 128:
                result['labels'].append({'name': '明亮', 'confidence': 0.6})
            else:
                result['labels'].append({'name': '昏暗', 'confidence': 0.6})
            
            # 生成描述
            face_count = len(faces)
            brightness_desc = '明亮' if brightness > 128 else '昏暗'
            result['scene_description'] = f"检测到{face_count}个人脸，环境{brightness_desc}"
            
        except Exception as e:
            logger.error(f"OpenCV分析失败: {e}")
        
        return result
    
    def _record_analysis(self, result: Dict, service: str):
        """记录分析历史"""
        record = {
            'timestamp': result['timestamp'],
            'service': service,
            'objects_count': len(result['objects']),
            'faces_count': len(result['faces']),
            'confidence': result['confidence_score'],
            'description': result['scene_description'][:50] + '...' if len(result['scene_description']) > 50 else result['scene_description']
        }
        
        self.analysis_history.append(record)
        
        # 保持历史长度
        if len(self.analysis_history) > self.max_history:
            self.analysis_history = self.analysis_history[-self.max_history:]
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析总结"""
        if not self.analysis_history:
            return {'total_analyses': 0}
        
        total_analyses = len(self.analysis_history)
        avg_confidence = sum(record['confidence'] for record in self.analysis_history) / total_analyses
        total_objects = sum(record['objects_count'] for record in self.analysis_history)
        total_faces = sum(record['faces_count'] for record in self.analysis_history)
        
        # 最常用的服务
        services = [record['service'] for record in self.analysis_history]
        most_used_service = max(set(services), key=services.count) if services else 'none'
        
        return {
            'total_analyses': total_analyses,
            'average_confidence': avg_confidence,
            'total_objects_detected': total_objects,
            'total_faces_detected': total_faces,
            'most_used_service': most_used_service,
            'last_analysis_time': self.analysis_history[-1]['timestamp']
        }
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """从图像中提取文字（OCR）"""
        try:
            # 优先使用云端OCR服务
            analysis = self.analyze_image(image_data, service='google')
            return analysis.get('text', '')
        except Exception as e:
            logger.error(f"OCR文字提取失败: {e}")
            return ""