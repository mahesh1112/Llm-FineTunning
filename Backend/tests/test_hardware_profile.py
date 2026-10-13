import unittest

from services.operations import collect_hardware_profile


class HardwareProfileTests(unittest.TestCase):
    def test_profile_contains_display_and_resource_fields(self) -> None:
        profile = collect_hardware_profile()

        self.assertIsInstance(profile["collectedAt"], str)
        logical_cores = profile["cpu"]["logicalCores"]
        self.assertTrue(logical_cores is None or logical_cores > 0)
        self.assertIn(profile["memory"]["status"], {"available", "unknown"})
        self.assertIn(profile["gpuStatus"], {"available", "unavailable", "unknown"})
        self.assertIsInstance(profile["gpu"], str)
        self.assertIsInstance(profile["vram"], str)
        self.assertIsInstance(profile["storage"], str)
        self.assertIsInstance(profile["runtime"], str)


if __name__ == "__main__":
    unittest.main()