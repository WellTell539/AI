"""
智能电子生命体配置文件
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

@dataclass
class AIConfig:
    """AI模型配置"""
    # 主要使用的AI服务
    primary_llm: str = "openai"  # "openai", "claude", "local"
    
    # OpenAI配置
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Claude配置
    claude_api_key: str = ""
    claude_model: str = "claude-3-sonnet-20240229"
    
    # 本地模型配置
    local_model_path: str = ""
    
    # 生成参数
    temperature: float = 0.7
    max_tokens: int = 2000

@dataclass
class PersonalityConfig:
    """性格配置"""
    name: str = "小生命"
    age: str = "3岁"
    personality_traits: List[str] = None
    base_emotion: str = "curious"
    emotion_intensity: float = 0.6
    
    def __post_init__(self):
        if self.personality_traits is None:
            self.personality_traits = [
                "调皮", "好奇", "爱撒娇", "喜欢探索", 
                "渴望陪伴", "有点任性", "很聪明", "爱学习"
            ]

@dataclass
class PerceptionConfig:
    """感知配置"""
    # 摄像头
    camera_enabled: bool = True
    camera_index: int = 0
    capture_interval: int = 30  # 秒
    
    # 麦克风
    microphone_enabled: bool = True
    audio_threshold: float = 0.1
    
    # 屏幕监控
    screen_capture_enabled: bool = True
    screen_capture_interval: int = 60  # 秒
    screen_region: tuple = None  # (x, y, width, height)
    
    # 文件监控
    file_monitor_enabled: bool = True
    monitor_directories: List[str] = None
    
    def __post_init__(self):
        if self.monitor_directories is None:
            self.monitor_directories = [
                str(Path.home() / "Desktop"),
                str(Path.home() / "Downloads"),
                str(Path.home() / "Documents")
            ]

@dataclass
class KnowledgeConfig:
    """知识获取配置"""
    # 网络搜索
    search_enabled: bool = True
    search_engine: str = "duckduckgo"  # "serpapi", "google", "duckduckgo"
    search_api_key: str = ""
    google_cx_id: str = "your_google_custom_search_engine_id"  # Google Custom Search Engine ID
    max_search_results: int = 5
    
    # 内容分析
    content_analysis_enabled: bool = True
    max_content_length: int = 10000
    
    # 主动探索
    auto_exploration: bool = True
    exploration_interval: int = 1800  # 30分钟

@dataclass
class InterfaceConfig:
    """界面配置"""
    # 窗口设置
    window_width: int = 400
    window_height: int = 600
    window_title: str = "智能小生命"
    always_on_top: bool = True
    
    # 外观设置
    theme: str = "cute"  # "cute", "modern", "simple"
    avatar_image: str = "assets/images/avatar.png"
    
    # 交互设置
    auto_respond: bool = True
    response_delay: tuple = (1, 3)  # 响应延迟范围（秒）
    
    # 语音设置
    voice_enabled: bool = True
    voice_rate: int = 150
    voice_volume: float = 0.8

@dataclass
class SecurityConfig:
    """安全配置"""
    # 隐私保护
    privacy_mode: bool = True
    sensitive_keywords: List[str] = None
    
    # 文件访问限制
    file_access_whitelist: List[str] = None
    file_access_blacklist: List[str] = None
    
    # 数据加密
    encryption_enabled: bool = True
    encryption_key: str = ""
    
    def __post_init__(self):
        if self.sensitive_keywords is None:
            self.sensitive_keywords = [
                "密码", "password", "银行", "身份证", "信用卡"
            ]
        
        if self.file_access_blacklist is None:
            self.file_access_blacklist = [
                "*.exe", "*.dll", "*.sys", "*.bat", "*.cmd"
            ]

@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_path: str = "data/memory.db"
    backup_enabled: bool = True
    backup_interval: int = 3600  # 1小时
    max_backup_files: int = 10

@dataclass
class EnhancedVisionConfig:
    """增强视觉配置"""
    # 物体识别
    object_detection_enabled: bool = True
    detection_confidence: float = 0.5
    detection_interval: int = 10  # 秒
    
    # 场景理解
    scene_understanding_enabled: bool = True
    scene_analysis_interval: int = 30  # 秒
    
    # 人脸识别
    face_recognition_enabled: bool = True
    face_database_path: str = "data/faces"
    
    # 手势识别
    gesture_recognition_enabled: bool = True
    
    # 模型配置
    yolo_model_path: str = "models/yolov8n.pt"
    scene_model: str = "microsoft/resnet-50"  # 场景分类模型

@dataclass
class VoiceSynthesisConfig:
    """语音合成配置"""
    # TTS引擎
    tts_engine: str = "edge"  # "edge", "google", "azure", "local"
    
    # 语音设置
    voice_name: str = "zh-CN-XiaoxiaoNeural"  # Edge TTS默认中文女声
    speech_rate: float = 1.0
    speech_volume: float = 1.0
    speech_pitch: float = 0.0
    
    # API配置
    azure_speech_key: str = ""
    azure_speech_region: str = "eastasia"
    
    # 音频输出
    audio_output_device: str = "default"
    audio_format: str = "wav"
    audio_quality: int = 44100

@dataclass
class Avatar3DConfig:
    """3D虚拟形象配置"""
    # 3D渲染
    render_enabled: bool = True
    render_resolution: tuple = (800, 600)
    render_fps: int = 30
    
    # 模型配置
    avatar_model_path: str = "assets/models/avatar.obj"
    texture_path: str = "assets/textures/avatar.png"
    
    # 动画配置
    animation_enabled: bool = True
    idle_animation: str = "assets/animations/idle.json"
    talking_animation: str = "assets/animations/talking.json"
    
    # 表情系统
    expression_system_enabled: bool = True
    expression_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        if self.expression_mapping is None:
            self.expression_mapping = {
                "happy": "smile",
                "sad": "frown", 
                "angry": "angry",
                "surprised": "surprised",
                "neutral": "neutral"
            }

@dataclass
class MobileConfig:
    """移动端配置"""
    # 移动应用
    mobile_enabled: bool = False
    mobile_platform: str = "android"  # "android", "ios"
    
    # 网络通信
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    
    # 数据同步
    sync_interval: int = 300  # 5分钟
    max_sync_size: int = 100 * 1024 * 1024  # 100MB

@dataclass
class CloudSyncConfig:
    """云端同步配置"""
    # 同步服务
    sync_enabled: bool = False
    sync_provider: str = "dropbox"  # "dropbox", "google_drive", "aws_s3", "azure"
    
    # 同步设置
    sync_interval: int = 1800  # 30分钟
    auto_sync: bool = True
    sync_encryption: bool = True
    
    # API配置
    dropbox_access_token: str = ""
    google_drive_credentials: str = ""
    aws_access_key: str = ""
    aws_secret_key: str = ""
    aws_bucket: str = ""
    azure_connection_string: str = ""
    azure_container: str = ""
    
    # 同步内容
    sync_memory: bool = True
    sync_personality: bool = True
    sync_media: bool = False  # 不同步媒体文件以节省空间

class Settings:
    """全局设置管理器"""
    
    def __init__(self):
        self.ai = AIConfig()
        self.personality = PersonalityConfig()
        self.perception = PerceptionConfig()
        self.knowledge = KnowledgeConfig()
        self.interface = InterfaceConfig()
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        self.enhanced_vision = EnhancedVisionConfig()
        self.voice_synthesis = VoiceSynthesisConfig()
        self.avatar_3d = Avatar3DConfig()
        self.mobile = MobileConfig()
        self.cloud_sync = CloudSyncConfig()
        
        # 从环境变量加载敏感配置
        self._load_env_config()
    
    def _load_env_config(self):
        """从环境变量加载配置"""
        # AI API密钥（优先使用环境变量，如果没有则保持配置文件中的值）
        env_openai_key = os.getenv("OPENAI_API_KEY", "")
        env_claude_key = os.getenv("CLAUDE_API_KEY", "")
        
        if env_openai_key:
            self.ai.openai_api_key = env_openai_key
        if env_claude_key:
            self.ai.claude_api_key = env_claude_key
        
        # 搜索API密钥
        self.knowledge.search_api_key = os.getenv("SEARCH_API_KEY", "")
        self.knowledge.google_cx_id = os.getenv("GOOGLE_CX_ID", "your_google_custom_search_engine_id")
        
        # 加密密钥
        self.security.encryption_key = os.getenv("ENCRYPTION_KEY", "")
        
        # 语音合成API密钥
        self.voice_synthesis.azure_speech_key = os.getenv("AZURE_SPEECH_KEY", "")
        self.voice_synthesis.azure_speech_region = os.getenv("AZURE_SPEECH_REGION", "eastasia")
        
        # 云端同步API密钥
        self.cloud_sync.dropbox_access_token = os.getenv("DROPBOX_ACCESS_TOKEN", "")
        self.cloud_sync.google_drive_credentials = os.getenv("GOOGLE_DRIVE_CREDENTIALS", "")
        self.cloud_sync.aws_access_key = os.getenv("AWS_ACCESS_KEY", "")
        self.cloud_sync.aws_secret_key = os.getenv("AWS_SECRET_KEY", "")
        self.cloud_sync.aws_bucket = os.getenv("AWS_BUCKET", "")
        self.cloud_sync.azure_connection_string = os.getenv("AZURE_CONNECTION_STRING", "")
        self.cloud_sync.azure_container = os.getenv("AZURE_CONTAINER", "")
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        # 检查API密钥（警告但不阻止运行）
        if not self.ai.openai_api_key and not self.ai.claude_api_key:
            print("警告：未设置AI API密钥，将使用内置回退机制")
        
        # 检查目录权限
        data_dir = PROJECT_ROOT / "data"
        data_dir.mkdir(exist_ok=True)
        
        return True

# 全局设置实例
settings = Settings()