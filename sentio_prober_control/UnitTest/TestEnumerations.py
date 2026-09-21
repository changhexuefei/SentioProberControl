import unittest
from sentio_prober_control.Sentio.Enumerations import FiberType, PowerMeterUnit, Stage


class TestStage(unittest.TestCase):
    def test_to_probe_selector_top(self):
        self.assertEqual(Stage.TopProbe.to_probe_selector(), "top")

    def test_to_probe_selector_bottom(self):
        self.assertEqual(Stage.BottomProbe.to_probe_selector(), "bottom")

    def test_to_probe_selector_rejects_non_probe_stage(self):
        with self.assertRaises(ValueError):
            Stage.Chuck.to_probe_selector()


class TestPowerMeterUnit(unittest.TestCase):
    def test_to_string(self):
        self.assertEqual(PowerMeterUnit.mWatt.to_string(), "mWatt")
        self.assertEqual(PowerMeterUnit.dBm.to_string(), "dBm")


class TestFiberType(unittest.TestCase):
    def test_lensed_array_to_string(self):
        self.assertEqual(FiberType.LensedArray.to_string(), "LensedArray")


if __name__ == "__main__":
    unittest.main()
