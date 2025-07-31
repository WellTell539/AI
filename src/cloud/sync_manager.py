"""
云端同步管理器 - 多设备数据同步
"""
import logging
import json
import hashlib
import threading
import time
import sqlite3
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import base64
import uuid
import os

try:
    # 使用Firebase Admin SDK
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

try:
    # 使用AWS SDK
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from config.settings import settings

logger = logging.getLogger(__name__)

class CloudSyncManager:
    """云端同步管理器"""
    
    def __init__(self):
        # 同步配置
        self.sync_config = {
            'provider': 'firebase',  # 'firebase', 'aws', 'custom'
            'auto_sync': True,
            'sync_interval': 300,  # 5分钟
            'encryption_enabled': True,
            'conflict_resolution': 'timestamp'  # 'timestamp', 'manual', 'merge'
        }
        
        # 设备标识
        self.device_id = self._generate_device_id()
        self.device_info = self._get_device_info()
        
        # 同步状态
        self.sync_status = {
            'last_sync': None,
            'is_syncing': False,
            'pending_uploads': 0,
            'pending_downloads': 0,
            'total_synced': 0,
            'errors': []
        }
        
        # 云端服务客户端
        self.firebase_client = None
        self.aws_client = None
        self.custom_api_client = None
        
        # 本地数据库
        self.local_db_path = "data/sync_cache.db"
        self._init_local_db()
        
        # 同步线程
        self.sync_thread = None
        self.sync_active = False
        
        # 数据类型定义
        self.sync_data_types = {
            'conversations': self._sync_conversations,
            'emotions': self._sync_emotions,
            'personality': self._sync_personality,
            'knowledge': self._sync_knowledge,
            'settings': self._sync_settings,
            'memories': self._sync_memories
        }
        
        # 初始化云端客户端
        self._init_cloud_clients()
    
    def _generate_device_id(self) -> str:
        """生成设备唯一标识"""
        # 基于MAC地址和机器名生成唯一ID
        import platform
        import getpass
        
        machine_info = f"{platform.node()}-{getpass.getuser()}-{platform.system()}"
        device_id = hashlib.md5(machine_info.encode()).hexdigest()
        return f"device_{device_id[:12]}"
    
    def _get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        import platform
        
        return {
            'device_id': self.device_id,
            'platform': platform.system(),
            'hostname': platform.node(),
            'python_version': platform.python_version(),
            'app_version': '1.0.0',
            'last_seen': datetime.now().isoformat()
        }
    
    def _init_local_db(self):
        """初始化本地同步数据库"""
        try:
            os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # 创建同步记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_records (
                    id TEXT PRIMARY KEY,
                    data_type TEXT,
                    data_hash TEXT,
                    last_modified TIMESTAMP,
                    sync_status TEXT,
                    device_id TEXT,
                    cloud_version INTEGER DEFAULT 1
                )
            ''')
            
            # 创建冲突记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_conflicts (
                    id TEXT PRIMARY KEY,
                    data_type TEXT,
                    local_data TEXT,
                    cloud_data TEXT,
                    conflict_time TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # 创建设备注册表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registered_devices (
                    device_id TEXT PRIMARY KEY,
                    device_info TEXT,
                    registration_time TIMESTAMP,
                    last_sync TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("本地同步数据库初始化成功")
            
        except Exception as e:
            logger.error(f"初始化本地数据库失败: {e}")
    
    def _init_cloud_clients(self):
        """初始化云端客户端"""
        try:
            # 初始化Firebase
            if FIREBASE_AVAILABLE and getattr(settings.ai, 'firebase_config', None):
                self._init_firebase_client()
            
            # 初始化AWS
            if AWS_AVAILABLE and getattr(settings.ai, 'aws_config', None):
                self._init_aws_client()
            
            # 初始化自定义API
            if getattr(settings.ai, 'custom_sync_api', None):
                self._init_custom_api_client()
                
        except Exception as e:
            logger.error(f"初始化云端客户端失败: {e}")
    
    def _init_firebase_client(self):
        """初始化Firebase客户端"""
        try:
            firebase_config = getattr(settings.ai, 'firebase_config', {})
            
            if not firebase_admin._apps:
                # 使用服务账号密钥
                if 'service_account_path' in firebase_config:
                    cred = credentials.Certificate(firebase_config['service_account_path'])
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': firebase_config.get('storage_bucket')
                    })
                else:
                    # 使用默认凭证
                    firebase_admin.initialize_app()
            
            self.firebase_client = firestore.client()
            logger.info("Firebase客户端初始化成功")
            
        except Exception as e:
            logger.error(f"Firebase客户端初始化失败: {e}")
    
    def _init_aws_client(self):
        """初始化AWS客户端"""
        try:
            aws_config = getattr(settings.ai, 'aws_config', {})
            
            self.aws_client = {
                'dynamodb': boto3.client('dynamodb', 
                    aws_access_key_id=aws_config.get('access_key_id'),
                    aws_secret_access_key=aws_config.get('secret_access_key'),
                    region_name=aws_config.get('region', 'us-east-1')
                ),
                's3': boto3.client('s3',
                    aws_access_key_id=aws_config.get('access_key_id'),
                    aws_secret_access_key=aws_config.get('secret_access_key'),
                    region_name=aws_config.get('region', 'us-east-1')
                )
            }
            
            logger.info("AWS客户端初始化成功")
            
        except Exception as e:
            logger.error(f"AWS客户端初始化失败: {e}")
    
    def _init_custom_api_client(self):
        """初始化自定义API客户端"""
        try:
            api_config = getattr(settings.ai, 'custom_sync_api', {})
            
            self.custom_api_client = {
                'base_url': api_config.get('base_url'),
                'api_key': api_config.get('api_key'),
                'session': requests.Session()
            }
            
            # 设置认证头
            if api_config.get('api_key'):
                self.custom_api_client['session'].headers.update({
                    'Authorization': f"Bearer {api_config['api_key']}"
                })
            
            logger.info("自定义API客户端初始化成功")
            
        except Exception as e:
            logger.error(f"自定义API客户端初始化失败: {e}")
    
    def start_auto_sync(self):
        """启动自动同步"""
        if not self.sync_config['auto_sync']:
            return
        
        if self.sync_active:
            logger.info("自动同步已在运行")
            return
        
        self.sync_active = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        logger.info("自动同步已启动")
    
    def stop_auto_sync(self):
        """停止自动同步"""
        self.sync_active = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        
        logger.info("自动同步已停止")
    
    def _sync_loop(self):
        """自动同步循环"""
        while self.sync_active:
            try:
                time.sleep(self.sync_config['sync_interval'])
                
                if not self.sync_active:
                    break
                
                # 执行同步
                self.sync_all_data()
                
            except Exception as e:
                logger.error(f"自动同步循环出错: {e}")
                time.sleep(60)  # 出错后等待1分钟
    
    def sync_all_data(self) -> Dict[str, Any]:
        """同步所有数据"""
        if self.sync_status['is_syncing']:
            return {'status': 'already_syncing'}
        
        self.sync_status['is_syncing'] = True
        sync_results = {}
        
        try:
            logger.info("开始同步所有数据...")
            
            # 注册或更新设备信息
            self._register_device()
            
            # 同步各种数据类型
            for data_type, sync_func in self.sync_data_types.items():
                try:
                    result = sync_func()
                    sync_results[data_type] = result
                    logger.info(f"{data_type}同步完成: {result}")
                except Exception as e:
                    error_msg = f"{data_type}同步失败: {e}"
                    logger.error(error_msg)
                    sync_results[data_type] = {'status': 'error', 'message': str(e)}
                    self.sync_status['errors'].append(error_msg)
            
            # 更新同步状态
            self.sync_status['last_sync'] = datetime.now()
            self.sync_status['total_synced'] += 1
            
            logger.info("数据同步完成")
            
        except Exception as e:
            logger.error(f"同步过程出错: {e}")
            sync_results['global_error'] = str(e)
        finally:
            self.sync_status['is_syncing'] = False
        
        return sync_results
    
    def _register_device(self):
        """注册或更新设备信息"""
        try:
            # 更新本地设备信息
            self.device_info['last_seen'] = datetime.now().isoformat()
            
            # 保存到本地数据库
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO registered_devices 
                (device_id, device_info, registration_time, last_sync)
                VALUES (?, ?, ?, ?)
            ''', (
                self.device_id,
                json.dumps(self.device_info),
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            # 同步到云端
            if self.firebase_client:
                self.firebase_client.collection('devices').document(self.device_id).set(
                    self.device_info, merge=True
                )
            
        except Exception as e:
            logger.error(f"设备注册失败: {e}")
    
    def _sync_conversations(self) -> Dict[str, Any]:
        """同步对话数据"""
        # 这里需要从AI大脑获取对话历史
        try:
            # 模拟对话数据
            conversations = {
                'device_id': self.device_id,
                'messages': [],  # 这里应该从ai_brain.conversation_history获取
                'last_updated': datetime.now().isoformat()
            }
            
            return self._sync_data_to_cloud('conversations', conversations)
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _sync_emotions(self) -> Dict[str, Any]:
        """同步情绪数据"""
        try:
            # 模拟情绪数据
            emotions = {
                'device_id': self.device_id,
                'emotion_history': [],  # 这里应该从emotion_engine获取
                'current_emotion': {},
                'last_updated': datetime.now().isoformat()
            }
            
            return self._sync_data_to_cloud('emotions', emotions)
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _sync_personality(self) -> Dict[str, Any]:
        """同步性格数据"""
        try:
            # 模拟性格数据
            personality = {
                'device_id': self.device_id,
                'traits': {},  # 这里应该从personality_system获取
                'growth_history': [],
                'last_updated': datetime.now().isoformat()
            }
            
            return self._sync_data_to_cloud('personality', personality)
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _sync_knowledge(self) -> Dict[str, Any]:
        """同步知识数据"""
        try:
            # 模拟知识数据
            knowledge = {
                'device_id': self.device_id,
                'discoveries': [],  # 这里应该从knowledge_manager获取
                'interests': [],
                'search_history': [],
                'last_updated': datetime.now().isoformat()
            }
            
            return self._sync_data_to_cloud('knowledge', knowledge)
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _sync_settings(self) -> Dict[str, Any]:
        """同步设置数据"""
        try:
            # 同步用户设置
            user_settings = {
                'device_id': self.device_id,
                'preferences': {},
                'customizations': {},
                'last_updated': datetime.now().isoformat()
            }
            
            return self._sync_data_to_cloud('settings', user_settings)
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _sync_memories(self) -> Dict[str, Any]:
        """同步记忆数据"""
        try:
            # 同步重要记忆
            memories = {
                'device_id': self.device_id,
                'important_moments': [],
                'user_preferences': {},
                'learned_behaviors': {},
                'last_updated': datetime.now().isoformat()
            }
            
            return self._sync_data_to_cloud('memories', memories)
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _sync_data_to_cloud(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """将数据同步到云端"""
        try:
            # 计算数据哈希
            data_json = json.dumps(data, sort_keys=True, ensure_ascii=False)
            data_hash = hashlib.sha256(data_json.encode()).hexdigest()
            
            # 检查是否需要同步
            if not self._needs_sync(data_type, data_hash):
                return {'status': 'no_change', 'hash': data_hash}
            
            # 加密数据（如果启用）
            if self.sync_config['encryption_enabled']:
                data = self._encrypt_data(data)
            
            # 选择云端提供商
            provider = self.sync_config['provider']
            
            if provider == 'firebase' and self.firebase_client:
                result = self._upload_to_firebase(data_type, data)
            elif provider == 'aws' and self.aws_client:
                result = self._upload_to_aws(data_type, data)
            elif provider == 'custom' and self.custom_api_client:
                result = self._upload_to_custom_api(data_type, data)
            else:
                return {'status': 'error', 'message': '没有可用的云端提供商'}
            
            # 更新本地同步记录
            if result.get('status') == 'success':
                self._update_sync_record(data_type, data_hash)
            
            return result
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _needs_sync(self, data_type: str, data_hash: str) -> bool:
        """检查是否需要同步"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data_hash FROM sync_records 
                WHERE data_type = ? AND device_id = ?
            ''', (data_type, self.device_id))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is None or result[0] != data_hash
            
        except Exception as e:
            logger.error(f"检查同步需求失败: {e}")
            return True  # 出错时默认需要同步
    
    def _update_sync_record(self, data_type: str, data_hash: str):
        """更新同步记录"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO sync_records
                (id, data_type, data_hash, last_modified, sync_status, device_id, cloud_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"{self.device_id}_{data_type}",
                data_type,
                data_hash,
                datetime.now(),
                'synced',
                self.device_id,
                1
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新同步记录失败: {e}")
    
    def _encrypt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """加密数据"""
        try:
            # 简单的base64编码（实际应用中应使用更强的加密）
            data_json = json.dumps(data, ensure_ascii=False)
            encrypted_data = base64.b64encode(data_json.encode()).decode()
            
            return {
                'encrypted': True,
                'data': encrypted_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"数据加密失败: {e}")
            return data
    
    def _decrypt_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """解密数据"""
        try:
            if not encrypted_data.get('encrypted'):
                return encrypted_data
            
            decrypted_json = base64.b64decode(encrypted_data['data']).decode()
            return json.loads(decrypted_json)
            
        except Exception as e:
            logger.error(f"数据解密失败: {e}")
            return encrypted_data
    
    def _upload_to_firebase(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """上传到Firebase"""
        try:
            doc_ref = self.firebase_client.collection('ai_data').document(f"{self.device_id}_{data_type}")
            doc_ref.set(data, merge=True)
            
            return {'status': 'success', 'provider': 'firebase'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'provider': 'firebase'}
    
    def _upload_to_aws(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """上传到AWS"""
        try:
            # 上传到DynamoDB
            table_name = 'ai_life_data'
            
            self.aws_client['dynamodb'].put_item(
                TableName=table_name,
                Item={
                    'device_id': {'S': self.device_id},
                    'data_type': {'S': data_type},
                    'data': {'S': json.dumps(data, ensure_ascii=False)},
                    'timestamp': {'S': datetime.now().isoformat()}
                }
            )
            
            return {'status': 'success', 'provider': 'aws'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'provider': 'aws'}
    
    def _upload_to_custom_api(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """上传到自定义API"""
        try:
            url = f"{self.custom_api_client['base_url']}/sync/{data_type}"
            
            payload = {
                'device_id': self.device_id,
                'data_type': data_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.custom_api_client['session'].post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return {'status': 'success', 'provider': 'custom', 'response': response.json()}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'provider': 'custom'}
    
    def download_from_cloud(self, data_type: str) -> Optional[Dict[str, Any]]:
        """从云端下载数据"""
        try:
            provider = self.sync_config['provider']
            
            if provider == 'firebase' and self.firebase_client:
                return self._download_from_firebase(data_type)
            elif provider == 'aws' and self.aws_client:
                return self._download_from_aws(data_type)
            elif provider == 'custom' and self.custom_api_client:
                return self._download_from_custom_api(data_type)
            
            return None
            
        except Exception as e:
            logger.error(f"从云端下载数据失败: {e}")
            return None
    
    def _download_from_firebase(self, data_type: str) -> Optional[Dict[str, Any]]:
        """从Firebase下载数据"""
        try:
            doc_ref = self.firebase_client.collection('ai_data').document(f"{self.device_id}_{data_type}")
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return self._decrypt_data(data)
            
            return None
            
        except Exception as e:
            logger.error(f"从Firebase下载失败: {e}")
            return None
    
    def _download_from_aws(self, data_type: str) -> Optional[Dict[str, Any]]:
        """从AWS下载数据"""
        try:
            table_name = 'ai_life_data'
            
            response = self.aws_client['dynamodb'].get_item(
                TableName=table_name,
                Key={
                    'device_id': {'S': self.device_id},
                    'data_type': {'S': data_type}
                }
            )
            
            if 'Item' in response:
                data_json = response['Item']['data']['S']
                data = json.loads(data_json)
                return self._decrypt_data(data)
            
            return None
            
        except Exception as e:
            logger.error(f"从AWS下载失败: {e}")
            return None
    
    def _download_from_custom_api(self, data_type: str) -> Optional[Dict[str, Any]]:
        """从自定义API下载数据"""
        try:
            url = f"{self.custom_api_client['base_url']}/sync/{data_type}/{self.device_id}"
            
            response = self.custom_api_client['session'].get(url, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('success') and result.get('data'):
                return self._decrypt_data(result['data'])
            
            return None
            
        except Exception as e:
            logger.error(f"从自定义API下载失败: {e}")
            return None
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return {
            'device_id': self.device_id,
            'sync_status': self.sync_status,
            'sync_config': self.sync_config,
            'available_providers': {
                'firebase': FIREBASE_AVAILABLE and self.firebase_client is not None,
                'aws': AWS_AVAILABLE and self.aws_client is not None,
                'custom': self.custom_api_client is not None
            },
            'device_info': self.device_info
        }
    
    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """解决同步冲突"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sync_conflicts WHERE id = ?
            ''', (conflict_id,))
            
            conflict = cursor.fetchone()
            if not conflict:
                return False
            
            if resolution == 'use_local':
                # 使用本地数据
                final_data = json.loads(conflict[2])  # local_data
            elif resolution == 'use_cloud':
                # 使用云端数据
                final_data = json.loads(conflict[3])  # cloud_data
            elif resolution == 'merge':
                # 合并数据（简单合并策略）
                local_data = json.loads(conflict[2])
                cloud_data = json.loads(conflict[3])
                final_data = {**cloud_data, **local_data}  # 本地数据优先
            else:
                return False
            
            # 上传解决后的数据
            data_type = conflict[1]
            self._sync_data_to_cloud(data_type, final_data)
            
            # 标记冲突已解决
            cursor.execute('''
                UPDATE sync_conflicts SET resolved = TRUE WHERE id = ?
            ''', (conflict_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"解决冲突失败: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧的同步数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # 清理旧的同步记录
            cursor.execute('''
                DELETE FROM sync_records WHERE last_modified < ?
            ''', (cutoff_date,))
            
            # 清理已解决的冲突
            cursor.execute('''
                DELETE FROM sync_conflicts WHERE resolved = TRUE AND conflict_time < ?
            ''', (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"清理了{days}天前的旧数据")
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
    
    def export_data(self) -> Dict[str, Any]:
        """导出所有同步数据"""
        try:
            exported_data = {
                'device_id': self.device_id,
                'export_time': datetime.now().isoformat(),
                'data': {}
            }
            
            # 导出各种数据类型
            for data_type in self.sync_data_types.keys():
                cloud_data = self.download_from_cloud(data_type)
                if cloud_data:
                    exported_data['data'][data_type] = cloud_data
            
            return exported_data
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return {}
    
    def import_data(self, imported_data: Dict[str, Any]) -> bool:
        """导入同步数据"""
        try:
            if 'data' not in imported_data:
                return False
            
            # 导入各种数据类型
            for data_type, data in imported_data['data'].items():
                if data_type in self.sync_data_types:
                    self._sync_data_to_cloud(data_type, data)
            
            logger.info("数据导入完成")
            return True
            
        except Exception as e:
            logger.error(f"导入数据失败: {e}")
            return False
    
    def shutdown(self):
        """关闭同步管理器"""
        self.stop_auto_sync()
        
        # 清理资源
        if self.firebase_client:
            try:
                firebase_admin.delete_app(firebase_admin.get_app())
            except:
                pass
        
        logger.info("云端同步管理器已关闭")

# 全局同步管理器实例
sync_manager = CloudSyncManager()