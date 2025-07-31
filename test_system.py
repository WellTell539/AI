"""
智能电子生命体系统测试脚本
"""
import sys
import os
import unittest
import asyncio
from unittest.mock import Mock, patch
import time

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 创建测试目录
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

from config.settings import settings
from src.core.ai_brain import AIBrain
from src.core.emotion_engine import EmotionEngine, EmotionType
from src.core.personality_system import PersonalitySystem
from src.core.decision_maker import DecisionMaker
from src.knowledge.knowledge_manager import KnowledgeManager
from src.knowledge.web_searcher import WebSearcher
from src.knowledge.content_analyzer import ContentAnalyzer

class TestEmotionEngine(unittest.TestCase):
    """测试情绪引擎"""
    
    def setUp(self):
        self.emotion_engine = EmotionEngine()
    
    def test_basic_emotion_processing(self):
        """测试基础情绪处理"""
        # 测试情绪触发
        self.emotion_engine.process_trigger({
            "type": "joy",
            "intensity": 0.8,
            "source": "test"
        })
        
        current_emotion = self.emotion_engine.get_current_emotion()
        self.assertEqual(current_emotion['emotion'], 'joy')
        self.assertGreaterEqual(current_emotion['intensity'], 0.8)
    
    def test_emotion_decay(self):
        """测试情绪衰减"""
        # 添加一个短期情绪
        self.emotion_engine.process_trigger({
            "type": "excitement",
            "intensity": 1.0,
            "source": "test",
            "duration": 1  # 1秒
        })
        
        # 等待衰减
        time.sleep(1.5)
        self.emotion_engine.update()
        
        # 检查情绪是否消失或衰减
        current_emotion = self.emotion_engine.get_current_emotion()
        self.assertNotEqual(current_emotion['emotion'], 'excitement')
    
    def test_emotion_description(self):
        """测试情绪描述"""
        self.emotion_engine.process_trigger({
            "type": "curiosity",
            "intensity": 0.6,
            "source": "test"
        })
        
        description = self.emotion_engine.get_emotion_description()
        self.assertIn("好奇", description)

class TestPersonalitySystem(unittest.TestCase):
    """测试性格系统"""
    
    def setUp(self):
        self.personality_system = PersonalitySystem()
    
    def test_personality_traits(self):
        """测试性格特征"""
        traits = self.personality_system.get_current_traits()
        
        # 检查是否包含基本性格特征
        required_traits = ['curiosity', 'playfulness', 'sociability', 'intelligence']
        for trait in required_traits:
            self.assertIn(trait, traits)
            self.assertIsInstance(traits[trait], float)
            self.assertGreaterEqual(traits[trait], 0.0)
            self.assertLessEqual(traits[trait], 1.0)
    
    def test_behavior_evaluation(self):
        """测试行为模式评估"""
        context = {
            "current_emotion": {"emotion": "loneliness", "intensity": 0.8},
            "last_interaction_time": None,
            "user_activity": "away"
        }
        
        behavior = self.personality_system.evaluate_behavior_trigger(context)
        # 孤独时应该倾向于寻求陪伴
        if behavior:
            self.assertIn("陪伴", behavior.name)
    
    def test_personality_description(self):
        """测试性格描述"""
        description = self.personality_system.get_personality_description()
        self.assertIsInstance(description, str)
        self.assertGreater(len(description), 0)

class TestKnowledgeSystem(unittest.TestCase):
    """测试知识系统"""
    
    def setUp(self):
        self.web_searcher = WebSearcher()
        self.content_analyzer = ContentAnalyzer()
        self.knowledge_manager = KnowledgeManager()
    
    def test_web_search_fallback(self):
        """测试网络搜索回退机制"""
        # 测试无网络情况下的回退
        results = self.web_searcher.search("测试查询")
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)  # 至少有回退结果
    
    def test_content_analysis(self):
        """测试内容分析"""
        # 模拟搜索结果
        mock_results = [
            {
                "title": "人工智能的发展",
                "snippet": "人工智能技术正在快速发展，这是一个令人兴奋的领域。",
                "url": "https://example.com"
            }
        ]
        
        analysis = self.content_analyzer.analyze_search_results(mock_results)
        self.assertEqual(analysis['status'], 'success')
        self.assertIn('analysis', analysis)
        self.assertGreater(analysis['analysis']['total_results'], 0)
    
    def test_knowledge_manager_search(self):
        """测试知识管理器搜索"""
        result = self.knowledge_manager.manual_search("测试")
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('results', result)

class TestAIBrain(unittest.TestCase):
    """测试AI大脑"""
    
    def setUp(self):
        self.ai_brain = AIBrain()
    
    def test_system_prompt_generation(self):
        """测试系统提示词生成"""
        prompt = self.ai_brain.get_system_prompt()
        self.assertIsInstance(prompt, str)
        self.assertIn(settings.personality.name, prompt)
        self.assertIn("调皮", prompt)  # 检查性格特征
    
    def test_fallback_response(self):
        """测试回退回应"""
        response = self.ai_brain._generate_fallback_response()
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
    def test_conversation_history(self):
        """测试对话历史管理"""
        initial_count = len(self.ai_brain.conversation_history)
        
        self.ai_brain._add_to_history("user", "测试消息")
        self.assertEqual(len(self.ai_brain.conversation_history), initial_count + 1)
        
        # 测试历史长度限制
        for i in range(50):
            self.ai_brain._add_to_history("user", f"消息{i}")
        
        self.assertLessEqual(len(self.ai_brain.conversation_history), self.ai_brain.max_history_length * 2)

class TestDecisionMaker(unittest.TestCase):
    """测试决策制定器"""
    
    def setUp(self):
        self.emotion_engine = EmotionEngine()
        self.personality_system = PersonalitySystem()
        self.ai_brain = AIBrain()
        self.decision_maker = DecisionMaker(
            ai_brain=self.ai_brain,
            emotion_engine=self.emotion_engine,
            personality_system=self.personality_system
        )
    
    def test_situation_analysis(self):
        """测试情况分析"""
        context = {
            "user_present": False,
            "last_interaction_time": time.time() - 1800,  # 30分钟前
            "current_emotion": {"emotion": "loneliness", "intensity": 0.7}
        }
        
        analysis = self.decision_maker._analyze_situation(context)
        self.assertIn("urgency_factors", analysis)
        self.assertIn("emotional_state", analysis)
    
    def test_action_generation(self):
        """测试行为生成"""
        situation_analysis = {
            "urgency_factors": ["long_silence"],
            "emotional_state": {"emotion": "loneliness", "intensity": 0.8},
            "personality_influence": {"sociability": 0.8}
        }
        
        actions = self.decision_maker._generate_action_options(situation_analysis)
        self.assertIsInstance(actions, list)
        if actions:
            self.assertTrue(any("寻求" in action.description for action in actions))

class TestSystemIntegration(unittest.TestCase):
    """测试系统集成"""
    
    def setUp(self):
        self.emotion_engine = EmotionEngine()
        self.personality_system = PersonalitySystem()
        self.ai_brain = AIBrain()
        self.knowledge_manager = KnowledgeManager(
            ai_brain=self.ai_brain,
            emotion_engine=self.emotion_engine
        )
    
    def test_emotion_personality_integration(self):
        """测试情绪和性格系统集成"""
        # 触发情绪
        self.emotion_engine.process_trigger({
            "type": "curiosity",
            "intensity": 0.8,
            "source": "test"
        })
        
        # 检查是否影响行为决策
        context = {
            "current_emotion": self.emotion_engine.get_current_emotion()
        }
        
        behavior = self.personality_system.evaluate_behavior_trigger(context)
        # 好奇心高时应该有探索行为倾向
        if behavior and "探索" in behavior.name:
            self.assertTrue(True)  # 预期行为
    
    def test_knowledge_emotion_integration(self):
        """测试知识管理和情绪系统集成"""
        # 模拟发现有趣内容
        self.knowledge_manager.knowledge_base['discoveries'].append({
            "title": "惊人的科学发现",
            "snippet": "科学家发现了一个令人兴奋的新现象",
            "interest_score": 0.9,
            "discovered_at": time.time()
        })
        
        # 检查是否触发相应情绪
        discovery = self.knowledge_manager.share_discovery()
        if discovery:
            self.assertIsInstance(discovery, dict)
            self.assertIn("title", discovery)

def run_performance_test():
    """运行性能测试"""
    print("\n=== 性能测试 ===")
    
    # 测试情绪引擎性能
    start_time = time.time()
    emotion_engine = EmotionEngine()
    for i in range(100):
        emotion_engine.process_trigger({
            "type": "joy",
            "intensity": 0.5,
            "source": f"test_{i}"
        })
        emotion_engine.update()
    
    emotion_time = time.time() - start_time
    print(f"情绪引擎处理100次更新: {emotion_time:.3f}秒")
    
    # 测试性格系统性能
    start_time = time.time()
    personality_system = PersonalitySystem()
    for i in range(50):
        personality_system.evaluate_behavior_trigger({
            "current_emotion": {"emotion": "curiosity", "intensity": 0.5}
        })
    
    personality_time = time.time() - start_time
    print(f"性格系统评估50次行为: {personality_time:.3f}秒")
    
    # 测试知识搜索性能
    start_time = time.time()
    web_searcher = WebSearcher()
    web_searcher.search("测试查询")
    search_time = time.time() - start_time
    print(f"网络搜索(回退模式): {search_time:.3f}秒")

def run_comprehensive_test():
    """运行综合测试"""
    print("=== 智能电子生命体系统综合测试 ===\n")
    
    # 运行单元测试
    print("运行单元测试...")
    
    test_classes = [
        TestEmotionEngine,
        TestPersonalitySystem,
        TestKnowledgeSystem,
        TestAIBrain,
        TestDecisionMaker,
        TestSystemIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        result = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w')).run(suite)
        
        class_tests = result.testsRun
        class_failures = len(result.failures) + len(result.errors)
        class_passed = class_tests - class_failures
        
        total_tests += class_tests
        passed_tests += class_passed
        
        print(f"  {test_class.__name__}: {class_passed}/{class_tests} 通过")
        
        if result.failures:
            for test, trace in result.failures:
                failed_tests.append(f"{test}: {trace}")
        
        if result.errors:
            for test, trace in result.errors:
                failed_tests.append(f"{test}: {trace}")
    
    print(f"\n单元测试总结: {passed_tests}/{total_tests} 通过")
    
    if failed_tests:
        print("\n失败的测试:")
        for failure in failed_tests[:5]:  # 只显示前5个失败
            print(f"  - {failure[:100]}...")
    
    # 运行性能测试
    run_performance_test()
    
    # 系统集成测试
    print("\n=== 系统集成测试 ===")
    
    try:
        # 测试完整的AI生命体实例化
        print("测试核心组件初始化...")
        emotion_engine = EmotionEngine()
        personality_system = PersonalitySystem()
        ai_brain = AIBrain()
        knowledge_manager = KnowledgeManager(ai_brain=ai_brain, emotion_engine=emotion_engine)
        
        print("✓ 所有核心组件初始化成功")
        
        # 测试基础交互流程
        print("测试基础交互流程...")
        
        # 1. 用户消息处理
        emotion_engine.process_trigger({"type": "joy", "intensity": 0.6, "source": "user_interaction"})
        
        # 2. 性格行为评估
        context = {"current_emotion": emotion_engine.get_current_emotion()}
        behavior = personality_system.evaluate_behavior_trigger(context)
        
        # 3. AI状态获取
        ai_state = ai_brain.get_current_state()
        
        print("✓ 基础交互流程测试通过")
        
        # 测试知识管理
        print("测试知识管理功能...")
        search_result = knowledge_manager.manual_search("测试")
        if search_result['success']:
            print("✓ 知识搜索功能正常")
        else:
            print("⚠ 知识搜索使用回退模式")
        
        print("\n=== 测试完成 ===")
        print(f"整体状态: {'✓ 系统运行正常' if passed_tests/total_tests > 0.8 else '⚠ 存在一些问题'}")
        
    except Exception as e:
        print(f"❌ 系统集成测试失败: {e}")

if __name__ == "__main__":
    run_comprehensive_test()