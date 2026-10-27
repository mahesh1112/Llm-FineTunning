import unittest
from unittest.mock import patch

from services.operations import estimate_resources


class EstimateTests(unittest.TestCase):
    @patch("services.operations.collect_hardware_profile", return_value={"gpu": "Test GPU"})
    def test_missing_benchmark_returns_unknown_duration(self, _hardware) -> None:
        result = estimate_resources({
            "workflow": "instructional_finetuning",
            "datasetSizeBytes": 4000,
        })

        self.assertEqual(result["status"], "needs_calibration")
        self.assertIsNone(result["minSeconds"])
        self.assertIn("measuredTokensPerSecond", result["missingInputs"])

    @patch("services.operations.collect_hardware_profile", return_value={"gpu": "Test GPU"})
    def test_measured_training_rate_returns_duration_range(self, _hardware) -> None:
        result = estimate_resources({
            "workflow": "instructional_finetuning",
            "estimatedTokens": 1000,
            "epochs": 2,
            "measuredTokensPerSecond": 10,
        })

        self.assertEqual(result["status"], "estimated")
        self.assertLess(result["minSeconds"], result["maxSeconds"])
        self.assertEqual(result["confidence"], "low")

    @patch("services.operations.collect_hardware_profile", return_value={"gpu": "Test GPU"})
    def test_quantization_requires_size_and_benchmark(self, _hardware) -> None:
        result = estimate_resources({"workflow": "quantization"})

        self.assertEqual(result["status"], "needs_calibration")
        self.assertIn("estimatedModelSizeBytes", result["missingInputs"])
        self.assertIn("measuredBytesPerSecond", result["missingInputs"])

    def test_unknown_workflow_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported workflow"):
            estimate_resources({"workflow": "other"})


if __name__ == "__main__":
    unittest.main()