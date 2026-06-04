import unittest
import os
from mirage.core.llm_adapters import MockAdapter
from mirage.models.llm import LLMResponse
from mirage.agents.llm_agent import LLMCommunicationAgent
from mirage.models.state import MirageState

class TestLLMAdapters(unittest.TestCase):
    def test_mock_adapter(self):
        adapter = MockAdapter("test-v1")
        response = adapter.generate("system", "user")
        self.assertTrue(response.success)
        self.assertEqual(response.provider, "MOCK")
        
    def test_adapter_abstraction(self):
        adapter = MockAdapter("test-v1")
        self.assertEqual(adapter.model_name, "test-v1")

class TestBulletins(unittest.TestCase):
    def test_agent_bulletin_generation(self):
        adapter = MockAdapter("test-v1")
        agent = LLMCommunicationAgent(adapter)
        state = MirageState(simulation_tick=1)
        bulletin = agent.generate_bulletin(state, "scenario_A")
        self.assertEqual(bulletin.scenario, "scenario_A")
        self.assertGreater(bulletin.confidence, 0.0)

if __name__ == "__main__":
    unittest.main()
