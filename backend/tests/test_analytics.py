"""
test_analytics.py — Unit test for Day 8 Call Analytics DB functions.
"""

import sys
import unittest
from pathlib import Path

# Add backend/src to sys.path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from database import (
    init_db,
    create_call_record,
    mark_exercise_started,
    mark_exercise_completed,
    end_call_record,
    get_call_analytics,
)


class TestCallAnalytics(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_successful_call_flow(self):
        session_id = "test-session-success-101"
        learner_id = "learner-alice"

        # 1. Session start
        res = create_call_record(session_id, learner_id, call_type="browser")
        self.assertTrue(res["success"])

        # 2. Exercise started
        mark_exercise_started(session_id)

        # 3. Answer evaluated & feedback given
        mark_exercise_completed(session_id)

        # 4. Session ends
        end_res = end_call_record(session_id)
        self.assertTrue(end_res["success"])
        self.assertEqual(end_res["outcome"], "SUCCESS")

        # 5. Check dashboard analytics
        analytics = get_call_analytics()
        self.assertGreater(analytics["total_calls"], 0)
        self.assertGreater(analytics["successful_calls"], 0)

        # Verify session is in recent_calls
        found = [c for c in analytics["recent_calls"] if c["session_id"] == session_id]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["outcome"], "SUCCESS")
        self.assertTrue(found[0]["exercise_started"])
        self.assertTrue(found[0]["exercise_completed"])
        self.assertTrue(found[0]["feedback_given"])

    def test_failed_call_flow(self):
        session_id = "test-session-failed-102"
        learner_id = "learner-bob"

        # 1. Session start
        res = create_call_record(session_id, learner_id, call_type="browser")
        self.assertTrue(res["success"])

        # 2. Learner disconnects early without completing exercise
        end_res = end_call_record(session_id)
        self.assertTrue(end_res["success"])
        self.assertEqual(end_res["outcome"], "FAILED")

        # 3. Check dashboard analytics
        analytics = get_call_analytics()
        found = [c for c in analytics["recent_calls"] if c["session_id"] == session_id]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["outcome"], "FAILED")
        self.assertFalse(found[0]["exercise_completed"])


if __name__ == "__main__":
    unittest.main()
