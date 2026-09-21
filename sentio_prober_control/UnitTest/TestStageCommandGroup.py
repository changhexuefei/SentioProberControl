import unittest
from unittest.mock import MagicMock
from sentio_prober_control.Communication.CommunicatorTcpIp import CommunicatorTcpIp
from sentio_prober_control.Sentio.Compatibility import CompatibilityLevel
from sentio_prober_control.Sentio.Enumerations import UvwAxis
from sentio_prober_control.Sentio.ProberSentio import SentioProber


class TestStageCommandGroup(unittest.TestCase):
    """Stage command groups mirror the remote command sections probe:{top|bottom}:{position}, chuck and scope."""

    def setUp(self):
        self.mock_comm = MagicMock(spec=CommunicatorTcpIp)
        self.prober = SentioProber(self.mock_comm, CompatibilityLevel.Sentio_26_2)
        self.mock_comm.reset_mock()

    def test_move_uvw(self):
        self.mock_comm.read_line.return_value = "0,0,12.5"
        pos = self.prober.probe.top.east.move_uvw(UvwAxis.U, 12.5)
        self.mock_comm.send.assert_called_once_with("probe:top:east:move_uvw U,12.5")
        self.assertEqual(pos, 12.5)

    def test_move_uvw_bottom(self):
        self.mock_comm.read_line.return_value = "0,0,-3.0"
        pos = self.prober.probe.bottom.west.move_uvw(UvwAxis.W, -3)
        self.mock_comm.send.assert_called_once_with("probe:bottom:west:move_uvw W,-3")
        self.assertEqual(pos, -3.0)

    def test_get_uvw(self):
        self.mock_comm.read_line.return_value = "0,0,0.75"
        pos = self.prober.probe.east.get_uvw(UvwAxis.V)
        self.mock_comm.send.assert_called_once_with("probe:top:east:get_uvw V")
        self.assertEqual(pos, 0.75)


if __name__ == "__main__":
    unittest.main()
