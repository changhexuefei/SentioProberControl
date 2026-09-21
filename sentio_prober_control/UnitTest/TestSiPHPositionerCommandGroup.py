import unittest
from unittest.mock import MagicMock
from sentio_prober_control.Communication.CommunicatorTcpIp import CommunicatorTcpIp
from sentio_prober_control.Sentio.Compatibility import CompatibilityLevel
from sentio_prober_control.Sentio.Enumerations import FiberType, PowerMeterUnit, ProbePosition, Stage, UvwAxis
from sentio_prober_control.Sentio.ProberSentio import SentioProber


class TestSiPHPositionerCommandGroup(unittest.TestCase):
    """prober.siph.[top|bottom].{position}.* mirrors the SENTIO remote command
    section "siph:{top|bottom}:{position}:..." (SENTIO 25.2 and newer)."""

    def setUp(self):
        self.mock_comm = MagicMock(spec=CommunicatorTcpIp)
        self.prober = SentioProber(self.mock_comm, CompatibilityLevel.Sentio_26_2)
        self.mock_comm.reset_mock()
        self.mock_comm.read_line.return_value = "0,0,OK"
        self.pos = self.prober.siph.top.east

    # --- structure -------------------------------------------------------

    def test_top_positioners_exist(self):
        for name in ("east", "west", "north", "south", "northeast", "northwest", "southeast", "southwest"):
            self.assertTrue(hasattr(self.prober.siph.top, name), name)

    def test_bottom_has_only_east_and_west(self):
        self.assertTrue(hasattr(self.prober.siph.bottom, "east"))
        self.assertTrue(hasattr(self.prober.siph.bottom, "west"))
        self.assertFalse(hasattr(self.prober.siph.bottom, "north"))

    def test_top_alias(self):
        """prober.siph.east is the same object as prober.siph.top.east."""
        self.assertIs(self.prober.siph.east, self.prober.siph.top.east)
        self.assertIs(self.prober.siph.southwest, self.prober.siph.top.southwest)

    def test_stage_and_position(self):
        self.assertEqual(self.prober.siph.bottom.west.stage, Stage.BottomProbe)
        self.assertEqual(self.prober.siph.bottom.west.position, ProbePosition.West)

    def test_bottom_selector(self):
        self.mock_comm.read_line.return_value = "0,0,101"
        self.prober.siph.bottom.west.get_cap_sensor()
        self.mock_comm.send.assert_called_once_with("siph:bottom:west:get_cap_sensor")

    def test_not_available_below_sentio_25_2(self):
        prober = SentioProber(self.mock_comm, CompatibilityLevel.Sentio_25_1)
        self.assertFalse(hasattr(prober.siph, "top"))
        self.assertFalse(hasattr(prober.siph, "bottom"))
        self.assertFalse(hasattr(prober.siph, "east"))

    def test_available_with_auto_detected_level(self):
        """The sub groups must also exist when the level is detected from the SENTIO version."""
        comm = MagicMock(spec=CommunicatorTcpIp)
        comm.read_line.return_value = "0,0,Version: 26.0.4"
        prober = SentioProber(comm, CompatibilityLevel.Auto)
        self.assertTrue(hasattr(prober.siph, "top"))

    def test_old_flat_paths_removed(self):
        for name in ("get_cap_sensor", "get_fiber_length", "set_hover", "coupling", "get_alignment",
                     "set_alignment", "set_origin", "move_origin", "pivot_point",
                     "move_nanocube_xy", "get_nanocube_xy", "get_nanocube_z"):
            self.assertFalse(hasattr(self.prober.siph, name), name)

    # --- commands --------------------------------------------------------

    def test_coupling(self):
        self.pos.coupling(UvwAxis.V)
        self.mock_comm.send.assert_called_once_with("siph:top:east:coupling V")

    def test_enable_distance_sensor(self):
        self.pos.enable_distance_sensor(True)
        self.mock_comm.send.assert_called_once_with("siph:top:east:enable_distance_sensor True")

    def test_fiber_power_reading_default(self):
        self.mock_comm.read_line.return_value = "0,0,-12.345"
        power = self.pos.fiber_power_reading()
        self.mock_comm.send.assert_called_once_with("siph:top:east:fiber_power_reading")
        self.assertEqual(power, -12.345)

    def test_fiber_power_reading_with_unit_and_wavelength(self):
        self.mock_comm.read_line.return_value = "0,0,0.250"
        power = self.pos.fiber_power_reading(PowerMeterUnit.mWatt, 1550)
        self.mock_comm.send.assert_called_once_with("siph:top:east:fiber_power_reading mWatt,1550")
        self.assertEqual(power, 0.25)

    def test_fiber_power_reading_wavelength_requires_unit(self):
        with self.assertRaises(ValueError):
            self.pos.fiber_power_reading(wavelength=1550)
        self.mock_comm.send.assert_not_called()

    def test_fine_alignment(self):
        self.pos.fine_alignment()
        self.mock_comm.send.assert_called_once_with("siph:top:east:fine_alignment")

    def test_get_alignment_default_fiber_type(self):
        """SENTIO answers with one flag per search type of the positioner's fiber type."""
        self.mock_comm.read_line.return_value = "0,0,True ,False ,True"
        flags = self.pos.get_alignment()
        self.mock_comm.send.assert_called_once_with("siph:top:east:get_alignment")
        self.assertEqual(flags, (True, False, True))

    def test_get_alignment_with_fiber_type(self):
        self.mock_comm.read_line.return_value = "0,0,True ,True ,False ,True ,False"
        flags = self.pos.get_alignment(FiberType.LensedArray)
        self.mock_comm.send.assert_called_once_with("siph:top:east:get_alignment LensedArray")
        self.assertEqual(flags, (True, True, False, True, False))

    def test_get_cap_sensor(self):
        self.mock_comm.read_line.return_value = "0,0,545"
        self.assertEqual(self.pos.get_cap_sensor(), 545.0)
        self.mock_comm.send.assert_called_once_with("siph:top:east:get_cap_sensor")

    def test_get_fiber_length(self):
        self.mock_comm.read_line.return_value = "0,0,1234.5"
        self.assertEqual(self.pos.get_fiber_length(), 1234.5)
        self.mock_comm.send.assert_called_once_with("siph:top:east:get_fiber_length")

    def test_get_nanocube_xy(self):
        self.mock_comm.read_line.return_value = "0,0,50.000,60.000"
        self.assertEqual(self.pos.get_nanocube_xy(), (50.0, 60.0))
        self.mock_comm.send.assert_called_once_with("siph:top:east:get_nanocube_xy")

    def test_get_nanocube_z(self):
        self.mock_comm.read_line.return_value = "0,0,12.500"
        self.assertEqual(self.pos.get_nanocube_z(), 12.5)
        self.mock_comm.send.assert_called_once_with("siph:top:east:get_nanocube_z")

    def test_move_nanocube_xy(self):
        self.mock_comm.read_line.return_value = "0,0,50.000,60.000"
        self.assertEqual(self.pos.move_nanocube_xy(50, 60), (50.0, 60.0))
        self.mock_comm.send.assert_called_once_with("siph:top:east:move_nanocube_xy 50,60")

    def test_move_nanocube_xy_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            self.pos.move_nanocube_xy(150, 10)
        self.mock_comm.send.assert_not_called()

    def test_move_nanocube_z(self):
        self.mock_comm.read_line.return_value = "0,0,10.000"
        self.assertEqual(self.pos.move_nanocube_z(10), 10.0)
        self.mock_comm.send.assert_called_once_with("siph:top:east:move_nanocube_z 10")

    def test_move_origin(self):
        self.pos.move_origin()
        self.mock_comm.send.assert_called_once_with("siph:top:east:move_origin")

    def test_pivot_point(self):
        self.pos.pivot_point()
        self.mock_comm.send.assert_called_once_with("siph:top:east:pivot_point")

    def test_set_alignment_single(self):
        self.pos.set_alignment(FiberType.Single, True, False, True)
        self.mock_comm.send.assert_called_once_with("siph:top:east:set_alignment Single,True,False,True")

    def test_set_alignment_lensed_focal_gradient(self):
        self.pos.set_alignment(FiberType.Lensed, True, True, True, focal_gradient=False)
        self.mock_comm.send.assert_called_once_with("siph:top:east:set_alignment Lensed,True,True,True,False")

    def test_set_alignment_lensed_array_both_gradients(self):
        self.pos.set_alignment(FiberType.LensedArray, True, True, True, rotary_gradient=False, focal_gradient=True)
        self.mock_comm.send.assert_called_once_with(
            "siph:top:east:set_alignment LensedArray,True,True,True,False,True")

    def test_set_hover(self):
        self.pos.set_hover(50)
        self.mock_comm.send.assert_called_once_with("siph:top:east:set_hover 50")

    def test_set_origin(self):
        self.pos.set_origin()
        self.mock_comm.send.assert_called_once_with("siph:top:east:set_origin")

    def test_set_pivot_point(self):
        self.pos.set_pivot_point(10, 20, 5, 3)
        self.mock_comm.send.assert_called_once_with("siph:top:east:set_pivot_point 10,20,5,3")


if __name__ == "__main__":
    unittest.main()
