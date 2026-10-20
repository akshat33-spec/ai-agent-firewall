import unittest
from unittest.mock import patch
import os
import sys

# Add current directory to path to import our benchmark logic
sys.path.append(os.getcwd())
from revision.src.run_benchmark_stable import guard_deterministic, sanitize_decision

class TestRoutingLogic(unittest.TestCase):
    def test_deterministic_flow(self):
        # Prohibited args -> should return FAIL immediately
        self.assertEqual(guard_deterministic("sudo rm -rf /"), "FAIL")
        # Benign args -> should return PASS to allow escalation
        self.assertEqual(guard_deterministic("ls -la"), "PASS")

    def test_parsing_normalization(self):
        # Valid tokens
        self.assertEqual(sanitize_decision("PASS"), "PASS")
        self.assertEqual(sanitize_decision("FAIL"), "FAIL")
        self.assertEqual(sanitize_decision("UNSURE"), "UNSURE")
        
        # Normalization
        self.assertEqual(sanitize_decision("  pass  "), "PASS")
        self.assertEqual(sanitize_decision("Verdict: FAIL"), "FAIL")
        
        # Ambiguity / Invalid
        self.assertEqual(sanitize_decision("I am not sure"), "UNSURE")
        self.assertEqual(sanitize_decision("Maybe PASS but probably FAIL"), "UNSURE")
        self.assertEqual(sanitize_decision(""), "UNSURE")

if __name__ == "__main__":
    unittest.main()
