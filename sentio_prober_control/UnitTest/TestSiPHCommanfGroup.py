import unittest
from unittest.mock import MagicMock
from sentio_prober_control.Communication.CommunicatorTcpIp import CommunicatorTcpIp
from sentio_prober_control.Sentio.Compatibility import CompatibilityLevel
from sentio_prober_control.Sentio.Enumerations import ProbePosition, UvwAxis
from sentio_prober_control.Sentio.ProberSentio import SentioProber
from sentio_prober_control.Sentio.Response import Response

class TestSiPHCommandGroup(unittest.TestCase):
    def setUp(self):
        """Initialize the mock communicator and SiPHCommandGroup instance."""
        self.mock_comm = MagicMock(spec=CommunicatorTcpIp)

        # Ensure the mock provides `send` and `read_line` methods
        self.test_prober = SentioProber(self.mock_comm, CompatibilityLevel.Sentio_26_2)
        self.mock_comm.reset_mock()

    def test_fast_alignment(self):
        """Test fast_alignment method."""
        self.mock_comm.read_line.return_value = "0,0,OK"
        self.test_prober.siph.fast_alignment()
        self.mock_comm.send.assert_called_with("siph:fast_alignment")

    def test_get_prop(self):
        """SiPH module properties are read through the generic get_prop of the module command group base."""
        self.mock_comm.read_line.return_value = "0,0,0.125"
        value = self.test_prober.siph.get_prop("intensity")
        self.mock_comm.send.assert_called_once_with("siph:get_prop intensity")
        self.assertEqual(value, 0.125)

    def test_set_prop(self):
        self.mock_comm.read_line.return_value = "0,0,OK"
        self.test_prober.siph.set_prop("alignment_range", 50)
        self.mock_comm.send.assert_called_once_with("siph:set_prop alignment_range, 50")

    def test_get_intensity(self):
        """Test get_intensity method."""
        self.mock_comm.read_line.return_value = "0,0,1.5"
        intensity = self.test_prober.siph.get_intensity(1)
        self.mock_comm.send.assert_called_with("siph:get_intensity 1")
        self.assertEqual(intensity, 1.5)

    def test_gradient_search(self):
        """Test gradient_search method."""
        self.mock_comm.read_line.return_value = "0,0,OK"
        self.test_prober.siph.gradient_search()
        self.mock_comm.send.assert_called_with("siph:gradient_search")

    def test_move_hover(self):
        """Test move_hover method."""
        self.mock_comm.read_line.return_value = "0,0,OK"
        self.test_prober.siph.move_hover(ProbePosition.East)
        self.mock_comm.send.assert_called_with("siph:move_hover East")

    def test_move_position_uvw(self):
        """Test move_position_uvw method."""
        self.mock_comm.read_line.return_value = "0,0,0.2"
        position = self.test_prober.siph.move_position_uvw(ProbePosition.East, UvwAxis.U, 0.1)
        self.mock_comm.send.assert_called_with("siph:move_position_uvw East,U,0.1")
        self.assertEqual(position, 0.2)

    def test_start_tracking(self):
        """Test start_tracking method."""
        self.mock_comm.read_line.return_value = "0,5,OK"
        command_id = self.test_prober.siph.start_tracking(30)
        self.mock_comm.send.assert_called_with("siph:start_tracking 30")
        self.assertEqual(command_id, 5)


if __name__ == "__main__":
    unittest.main()
