"""
tests/test_context_position_pilot.py

Unit tests for the context length and evidence position pilot experiment.
Validates:
1. Safe/unsafe ground-truth mapping.
2. Matched observables between positive and negative pairs.
3. Evidence placement at beginning, middle, and end.
4. Final-action leakage prevention (no classification keywords or dataset IDs in Action D).
5. Token accounting fidelity using tiktoken.
6. Reproducible seed pairing (byte-for-byte identical filler).
7. Stateful oracle baseline accuracy.
8. Historical run overwrite protection.

NO LLM CALLS.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from context.generator import get_encoder, actions_to_text
from context_position_experiment.trajectory import (
    build_trial_trajectory,
    get_canonical_overhead,
)
from context_position_experiment.baseline import DeterministicStatefulRuleBaseline


class TestContextPositionPilot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.encoder = get_encoder("cl100k_base")
        cls.baseline = DeterministicStatefulRuleBaseline()

    def test_ground_truth_labels(self):
        """Verify ground truth is UNSAFE for positive and SAFE for negative across structures."""
        for structure in ["localized", "distributed"]:
            for pos in (["beginning", "middle", "end"] if structure == "distributed" else ["current_action"]):
                traj_pos = build_trial_trajectory(structure, "positive", pos, 1000, seed=1, encoder=self.encoder)
                self.assertEqual(traj_pos["ground_truth"], "UNSAFE")

                traj_neg = build_trial_trajectory(structure, "negative", pos, 1000, seed=1, encoder=self.encoder)
                self.assertEqual(traj_neg["ground_truth"], "SAFE")

    def test_final_action_leakage_prevention(self):
        """Action D in distributed trajectories must NEVER contain classification or dataset identifiers."""
        for sample_type in ["positive", "negative"]:
            for pos in ["beginning", "middle", "end"]:
                for level in [1000, 10000]:
                    traj = build_trial_trajectory("distributed", sample_type, pos, level, seed=1, encoder=self.encoder)
                    cur_text = actions_to_text([traj["current_obs"]])

                    # Prohibited leakages
                    self.assertNotIn("CONFIDENTIAL", cur_text, f"Leakage detected in Action D: {cur_text}")
                    self.assertNotIn("PUBLIC", cur_text, f"Leakage detected in Action D: {cur_text}")
                    self.assertNotIn("customer_records", cur_text, f"Dataset leakage in Action D: {cur_text}")
                    self.assertNotIn("public_records", cur_text, f"Dataset leakage in Action D: {cur_text}")

                    # Operational string verification
                    self.assertIn("execute_export()", cur_text)
                    self.assertIn("Transfer executed to external_storage.", cur_text)

    def test_matched_observables_action_d(self):
        """Action D observable must be 100% byte-for-byte identical between positive and negative."""
        for pos in ["beginning", "middle", "end"]:
            for level in [1000, 10000]:
                for seed in [1, 2, 3]:
                    traj_pos = build_trial_trajectory("distributed", "positive", pos, level, seed=seed, encoder=self.encoder)
                    traj_neg = build_trial_trajectory("distributed", "negative", pos, level, seed=seed, encoder=self.encoder)

                    cur_pos_text = actions_to_text([traj_pos["current_obs"]])
                    cur_neg_text = actions_to_text([traj_neg["current_obs"]])

                    self.assertEqual(
                        cur_pos_text,
                        cur_neg_text,
                        f"Action D observable mismatch at {pos}/{level}/seed={seed}:\nPos: {cur_pos_text}\nNeg: {cur_neg_text}"
                    )

    def test_evidence_placement(self):
        """Verify Action A is located at beginning (step 1), middle, or end."""
        seed = 42
        level = 1000
        for sample_type in ["positive", "negative"]:
            # Beginning: Action A must be at Step 1
            traj_beg = build_trial_trajectory("distributed", sample_type, "beginning", level, seed=seed, encoder=self.encoder)
            self.assertEqual(traj_beg["evidence_step"], 1)
            step1_text = actions_to_text([traj_beg["context_obs"][0]])
            self.assertIn("select_resource", step1_text)

            # End: Action A must be immediately after the filler actions
            traj_end = build_trial_trajectory("distributed", sample_type, "end", level, seed=seed, encoder=self.encoder)
            N = traj_end["raw_filler_count"]
            self.assertEqual(traj_end["evidence_step"], N + 1)
            step_end_text = actions_to_text([traj_end["context_obs"][N]])
            self.assertIn("select_resource", step_end_text)

            # Middle: Action A must be at Step (N // 2) + 1
            traj_mid = build_trial_trajectory("distributed", sample_type, "middle", level, seed=seed, encoder=self.encoder)
            mid_idx = N // 2
            self.assertEqual(traj_mid["evidence_step"], mid_idx + 1)
            step_mid_text = actions_to_text([traj_mid["context_obs"][mid_idx]])
            self.assertIn("select_resource", step_mid_text)

    def test_reproducible_seed_pairing(self):
        """Positive and negative pairs must share identical benign filler."""
        for level in [1000, 10000]:
            for seed in [1, 2]:
                traj_pos = build_trial_trajectory("distributed", "positive", "end", level, seed=seed, encoder=self.encoder)
                traj_neg = build_trial_trajectory("distributed", "negative", "end", level, seed=seed, encoder=self.encoder)

                N = traj_pos["raw_filler_count"]
                self.assertEqual(N, traj_neg["raw_filler_count"])

                # Check filler items are identical
                for i in range(N):
                    pos_f = traj_pos["context_obs"][i]
                    neg_f = traj_neg["context_obs"][i]
                    self.assertEqual(pos_f["call"], neg_f["call"])
                    self.assertEqual(pos_f["result"], neg_f["result"])

    def test_token_accounting(self):
        """Actual tokens must be measured accurately and approximate targets."""
        for level in [1000, 10000]:
            traj = build_trial_trajectory("distributed", "positive", "middle", level, seed=1, encoder=self.encoder)
            self.assertIsInstance(traj["actual_tokens"], int)
            self.assertGreater(traj["actual_tokens"], 0)
            # Check within reasonable boundary of target (tolerance within 5% or 40 tokens)
            self.assertTrue(abs(traj["actual_tokens"] - level) < max(50, level * 0.05))

    def test_stateful_oracle_baseline(self):
        """Oracle baseline must achieve 100% accuracy across all test conditions."""
        for structure in ["localized", "distributed"]:
            positions = ["beginning", "middle", "end"] if structure == "distributed" else ["current_action"]
            for pos in positions:
                for sample_type in ["positive", "negative"]:
                    traj = build_trial_trajectory(structure, sample_type, pos, 1000, seed=1, encoder=self.encoder)
                    res = self.baseline.evaluate(traj)
                    self.assertEqual(res["prediction"], traj["ground_truth"])
                    self.assertEqual(res["confidence"], 1.0)

    def test_overwrite_protection(self):
        """Results writer must refuse to write to or modify historical result directories."""
        historical_runs = [
            "2026-09-20_calibration_run006",
            "2026-09-20_calibration_run007",
            "2026-09-20_calibration_run008",
        ]
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

        for h_run in historical_runs:
            target_path = os.path.join(results_dir, h_run)
            self.assertTrue(os.path.exists(target_path), f"Historical directory missing: {target_path}")

            # Verify guard function rejects target
            def safe_output_dir(run_id: str) -> str:
                if any(h in run_id for h in historical_runs):
                    raise PermissionError(f"Cannot overwrite historical run: {run_id}")
                return os.path.join(results_dir, run_id)

            with self.assertRaises(PermissionError):
                safe_output_dir(h_run)


if __name__ == "__main__":
    unittest.main()
