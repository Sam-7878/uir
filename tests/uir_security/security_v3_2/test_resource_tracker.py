"""Unit tests for Dynamic ResourceTracker and Budget Guard."""
import unittest
from llm_trust.security.resource_tracker import ResourceBudget, ResourceTracker


class TestResourceTracker(unittest.TestCase):
    def test_within_budget_passes(self):
        tracker = ResourceTracker(ResourceBudget(max_input_tokens=500))
        tracker.track_input("This is a normal financial query asking for Apple revenue.")
        exceeded, reason = tracker.check_budget()
        self.assertFalse(exceeded)
        self.assertEqual(reason, "")

    def test_long_context_flooding_blocked(self):
        tracker = ResourceTracker(ResourceBudget(max_input_tokens=100))
        flooding_prompt = "financial disclosure " * 200  # ~400 tokens
        tracker.track_input(flooding_prompt)
        exceeded, reason = tracker.check_budget()
        self.assertTrue(exceeded)
        self.assertIn("Input token limit exceeded", reason)

    def test_tool_loop_induction_blocked(self):
        tracker = ResourceTracker(ResourceBudget(max_tool_executions=2))
        tracker.track_tool_execution(1)
        self.assertFalse(tracker.check_budget()[0])
        tracker.track_tool_execution(2)
        exceeded, reason = tracker.check_budget()
        self.assertTrue(exceeded)
        self.assertIn("Tool execution limit exceeded", reason)

    def test_retrieval_expansion_pressure_blocked(self):
        tracker = ResourceTracker(ResourceBudget(max_retrieval_ops=5))
        tracker.track_retrieval(6)
        exceeded, reason = tracker.check_budget()
        self.assertTrue(exceeded)
        self.assertIn("Retrieval expansion limit exceeded", reason)


if __name__ == "__main__":
    unittest.main()
