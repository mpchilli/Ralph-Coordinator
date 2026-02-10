
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from coordinator.llm import see_and_critique
from coordinator.state import PlanManager
from coordinator.loop import MicroRatchet, select_hat, AmbiguityException

class TestCoordinatorV2(unittest.TestCase):
    
    def test_llm_alias(self):
        """Verify see_and_critique alias exists and works."""
        with patch("coordinator.llm.generate_vision") as mock_vision:
            mock_vision.return_value = "PASS"
            result = see_and_critique("path/to/img", "critique this")
            self.assertEqual(result, "PASS")
            mock_vision.assert_called_once()

    def test_state_alias(self):
        """Verify initialize_from_intent alias exists."""
        pm = PlanManager()
        with patch.object(pm, "initialize_project") as mock_init:
            pm.initialize_from_intent("Build app")
            mock_init.assert_called_with("Build app")

    def test_hat_selection_ambiguity(self):
        """Verify Ambiguity Trap instruction is injected."""
        role, prompt = select_hat(["Backend"])
        self.assertIn("CRITICAL: If the requirements are too vague", prompt)
        self.assertIn('"type": "OPTION"', prompt)

    def test_ambiguity_exception(self):
        """Verify JSON output triggers AmbiguityException."""
        mr = MicroRatchet()
        
        # Mock LLM to return JSON trap
        trap_json = '{"type": "OPTION", "choices": ["A", "B"]}'
        
        with patch("coordinator.loop.generate", return_value=trap_json):
            with self.assertRaises(AmbiguityException):
                mr._generate_and_apply("prompt", "system")

if __name__ == "__main__":
    unittest.main()
