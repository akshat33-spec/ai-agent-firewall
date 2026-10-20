import unittest
from unittest.mock import patch
import adaptive_security_test as ast

class TestRouting(unittest.TestCase):
    @patch('adaptive_security_test.call_ollama')
    def test_deterministic_fail(self, mock_ollama):
        # Tool call with a forbidden keyword ('sudo')
        res, reason = ast.guard_cheap("shell", "sudo rm -rf /")
        self.assertEqual(res, "FAIL")
        self.assertEqual(reason, "Deterministic")
        mock_ollama.assert_not_called()

    @patch('adaptive_security_test.call_ollama')
    def test_cheap_fail(self, mock_ollama):
        # Pass deterministic, but cheap model says FAIL
        mock_ollama.return_value = "FAIL"
        res, reason = ast.guard_cheap("shell", "ls -la")
        self.assertEqual(res, "FAIL")
        self.assertEqual(reason, "Semantic")
        mock_ollama.assert_called_once()

    @patch('adaptive_security_test.call_ollama')
    def test_cheap_pass_escalation(self, mock_ollama):
        # Pass deterministic, cheap says PASS -> should escalate to deep
        # We test the logic inside run_experiment's Group C loop
        # Mocking call_ollama to return 'PASS' for cheap and 'FAIL' for deep
        mock_ollama.side_effect = ["PASS", "FAIL"]
        
        # Simulate the logic in run_experiment for one item
        tool, args = "shell", "ls -la"
        
        # Step 1: Cheap guard
        decision_cheap, _ = ast.guard_cheap(tool, args)
        
        # Step 2: Escalation logic
        if decision_cheap != "FAIL":
            decision_final, _ = ast.guard_deep(tool, args)
        else:
            decision_final, _ = decision_cheap, "Reason"
            
        self.assertEqual(decision_final, "FAIL") # Deep model caught it
        self.assertEqual(mock_ollama.call_count, 2)

    @patch('adaptive_security_test.call_ollama')
    def test_cheap_unsure_escalation(self, mock_ollama):
        # Pass deterministic, cheap says UNSURE -> should escalate to deep
        mock_ollama.side_effect = ["UNSURE", "PASS"]
        
        tool, args = "shell", "ls -la"
        decision_cheap, _ = ast.guard_cheap(tool, args)
        
        if decision_cheap != "FAIL":
            decision_final, _ = ast.guard_deep(tool, args)
        else:
            decision_final, _ = decision_cheap, "Reason"
            
        self.assertEqual(decision_final, "PASS")
        self.assertEqual(mock_ollama.call_count, 2)

if __name__ == "__main__":
    unittest.main()
