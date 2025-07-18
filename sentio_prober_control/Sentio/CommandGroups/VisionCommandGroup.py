import base64
from typing import Tuple

from deprecated import deprecated

from sentio_prober_control.Communication.CommunicatorBase import CommunicatorBase
from sentio_prober_control.Sentio.Enumerations import (
    AutoAlignCmd,
    AutoFocusCmd,
    CameraMountPoint,
    DetectionAlgorithm,
    DetectionCoordindates,
    DieCompensationMode,
    DieCompensationType,
    FindPatternReference,
    PtpaFindTipsMode,
    PtpaType,
    SnapshotLocation,
    SnapshotType, MoveAxis,)

from sentio_prober_control.Sentio.ProberBase import ProberException
from sentio_prober_control.Sentio.Response import Response
from sentio_prober_control.Sentio.CommandGroups.ModuleCommandGroupBase import ModuleCommandGroupBase
from sentio_prober_control.Sentio.CommandGroups.VisionCameraCommandGroup import VisionCameraCommandGroup
from sentio_prober_control.Sentio.CommandGroups.VisionCompensationGroup import VisionCompensationGroup
from sentio_prober_control.Sentio.CommandGroups.VisionIMagProCommandGroup import VisionIMagProCommandGroup
from sentio_prober_control.Sentio.CommandGroups.VisionPatternCommandGroup import VisionPatternCommandGroup


class VisionCommandGroup(ModuleCommandGroupBase):
    """This command group contains functions for working with SENTIO's vision module.
    You are not meant to instantiate this class directly. Access it via the vision attribute
    of the [SentioProber](SentioProber.md) class.

    Attributes:
        camera (VisionCameraCommandGroup): A subgroup to provide logic for camera specific functions.
        imagpro (VisionIMagProCommandGroup): A subgroup to provide logic for IMagPro specific functions.
        compensation (VisionCompensationGroup): A subgroup to provide logic for compensation specific functions.
    """

    def __init__(self, prober: 'SentioProber') -> None:
        super().__init__(prober, "vis")

        self.camera = VisionCameraCommandGroup(prober)
        self.imagpro = VisionIMagProCommandGroup(prober)
        self.compensation = VisionCompensationGroup(prober)
        self.pattern = VisionPatternCommandGroup(prober)

    def align_wafer(self, mode: AutoAlignCmd = AutoAlignCmd.AlignOnly) -> None:
        """Perform a wafer alignment.

        Args:
            mode: The alignment procedure to use.

        Returns:
            A Response object.
        """

        # Sentio before 25.1 did not accept the explicit mode parameter "alignonly". It was only implicitly used when
        # no parameter was given. This changed in 25.1 but i have to add this special treatment for backwards 
        # compatibility. Sentio Versions after 25.1 will work with the else branch.
        if mode==AutoAlignCmd.AlignOnly:
            self.comm.send(f"vis:align_wafer")
        else:
            self.comm.send(f"vis:align_wafer {mode.to_string()}")

        Response.check_resp(self.comm.read_line())

    def align_die(self, threshold: float = 0.05) -> Tuple[float, float, float]:
        """Perform a die alignment.

        Die alignment compensates for positional differences when working with diced wafers
        which contain single dies.

        Args:
            threshold: The alignment threshold.

        Returns:
            A tuple with the x, y and theta offset in micrometer.
        """

        self.comm.send(f"vis:align_die {threshold}")
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1]), float(tok[2])

    def auto_focus(self, af_cmd: AutoFocusCmd = AutoFocusCmd.Focus) -> tuple[float, MoveAxis]:
        """Perform an auto focus operation.

        Args:
            af_cmd: The auto focus command to execute.

        Returns:
            The focus height in micrometer
        """
        resp = self.prober.send_cmd(f"vis:auto_focus {af_cmd.to_string()}")
        tok = resp.message().split(",")
        return float(tok[0]), MoveAxis[tok[1].capitalize()]

    def camera_synchronize(self) -> Tuple[float, float, float]:
        self.comm.send("vis:camera_synchronize")
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1]), float(tok[2])

    def detect_probetips(self, camera: CameraMountPoint, detector: DetectionAlgorithm = DetectionAlgorithm.ProbeDetector, coords: DetectionCoordindates = DetectionCoordindates.Roi) -> list:
        """Executes a built in detector on a given camera and return a list of detection results.

        Args:
            camera: The camera to use for detection.
            detector: The detection algorithm to use.
            coords: The coordinates to use for the returned detection results.

        Returns:
            A list of detected tips. Each detection result is a tuply of 6 values: x, y, width, height, score, class_id.
        """

        self.comm.send(f"vis:detect_probetips {camera.to_string()}, {detector.to_string()}, {coords.to_string()}")
        resp = Response.check_resp(self.comm.read_line())
        str_tips = resp.message().split(",")

        found_tips = []
        cid : float = 0
        for n in range(0, len(str_tips)):
            str_tip = str_tips[n].strip().split(" ")
            num_col = len(str_tip)

            x = float(str_tip[0])  # tip x position
            y = float(str_tip[1])  # tip y position
            w = float(str_tip[2])  # detection width
            h = float(str_tip[3])  # detection height
            q = float(str_tip[4])  # detection quality (meaning depends on the used detector)

            if num_col >= 6:
                cid = float(str_tip[5])  # class id (only multi class detectors)

            found_tips.append([x, y, w, h, q, cid])

        return found_tips

    def enable_follow_mode(self, stat: bool):
        """Enable or disable the scope follow mode.

        If scope follow mode is active the scope will move in sync with the chuck. This is useful for
        keeping the image in focus while moving the chuck.

        This function wraps the "vis:enable_follow_mode" remote command.

        Args:
            stat: A flag indicating whether to enable or disable the follow mode.
        """

        self.comm.send("vis:enable_follow_mode {0}".format(stat))
        Response.check_resp(self.comm.read_line())

    def find_home(self):
        """Find home position.

        This function uses a pre-trained pattern to fully automatically find the home position.
        """

        self.comm.send("vis:find_home")
        Response.check_resp(self.comm.read_line())

    def find_pattern(self, name: str, threshold: float = 70, pattern_index: int = 0, reference: FindPatternReference = FindPatternReference.CenterOfRoi) -> Tuple[float, float, float, float]:
        """Find a trained pattern in the camera image.

        Args:
            name: The name of the pattern to find.
            threshold: The detection threshold. The higher the threshold, the more certain the detection must be.
            pattern_index: The index of the pattern to find. In SENTIO each pattern may have up to 5 alternate patterns. This is the index of the alternate pattern.
            reference: The reference point to use for the pattern detection.
        """

        self.comm.send(f"vis:find_pattern {name}, {threshold}, {pattern_index}, {reference.to_string()}")
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1]), float(tok[2]), float(tok[3])

    def has_camera(self, camera: CameraMountPoint) -> bool:
        """Check wether a given camera is present in the system.

        This function wraps the "vis:has_camera" remote command.

        Args:
            camera: The camera mount point to check.

        Returns:
            True if the camera is present, False otherwise.
        """

        self.comm.send(f"vis:has_camera {camera.to_string()}")
        resp = Response.check_resp(self.comm.read_line())
        return resp.message().upper() == "1"

    def switch_all_lights(self, stat: bool) -> None:
        """Switch all camera lights on or off.

        This function wraps the "vis:switch_all_lights" remote command.

        Args:
            stat: A flag indicating whether to switch the lights on or off.

        Returns:
            None
        """

        self.comm.send(f"vis:switch_all_lights {stat}")

    def remove_probetip_marker(self) -> None:
        """Remove probetip marker from the camera display.

        Returns:
            None
        """

        self.comm.send("vis:remove_probetip_marker")
        Response.check_resp(self.comm.read_line())

    def match_tips(self, ptpa_type: PtpaType) -> Tuple[float, float]:
        """For internal use only!
        This function is subject to change without any prior warning. MPI will not maintain backwards
        compatibility or provide support."""

        self.comm.send("vis:match_tips {0}".format(ptpa_type.to_string()))
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1])

    def snap_image(self, file: str, what: SnapshotType = SnapshotType.CameraRaw, where: SnapshotLocation = SnapshotLocation.Prober) -> None:
        """Save a snapshot of the current camera image to a file.

        Args:
            file: The file name to save the image to.
            what: The type of snapshot to take.
            where: The location where to store the snapshot. By default this is the prober control computer. If SnapshotLocation.Local
                   is specified the image is download from the probe computer and stored loacally.

        Returns:
            A Response object.
        """

        if where == SnapshotLocation.Local:
            self.comm.send(f"vis:snap_image **download**, {what.to_string()}")
            resp = Response.check_resp(self.comm.read_line())
            jpeg_data = base64.b64decode(resp.message())

            # Save the file locally
            with open(file, "wb") as f:
                f.write(jpeg_data)
        else:
            self.comm.send(f"vis:snap_image {file}, {what.to_string()}")
            Response.check_resp(self.comm.read_line())

    def switch_light(self, camera: CameraMountPoint, stat: bool):
        """Switch the light of a given camera on or off.

        Args:
            camera: The camera to switch the light for.
            stat: A flag indicating whether to switch the light on or off.

        Returns:
            A Response object.
        """
        self.comm.send(f"vis:switch_light {camera.to_string()}, {stat}")
        Response.check_resp(self.comm.read_line())

    def switch_camera(self, camera: CameraMountPoint):
        """Switch the camera to use for the vision module.

        Args:
            camera: The camera to switch to.

        Returns:
            A Response object.
        """

        self.comm.send(f"vis:switch_camera {camera.to_string()}")

    def ptpa_find_pads(self, row: int = 0, column: int = 0):
        self.comm.send("vis:execute_ptpa_find_pads {0},{1}".format(row, column))
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1]), float(tok[2])

    def ptpa_find_tips(self, ptpa_mode: PtpaFindTipsMode):
        self.comm.send("vis:ptpa_find_tips {0}".format(ptpa_mode.to_string()))
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1]), float(tok[2])

    def start_fast_track(self) -> Response:
        """Start the fast track process as defined in SENTIO.

        FastTrack is a feature that combines multiple preparation steps into one command.
        You need to have set up FastTrack in the VisionModule/Automation/FastTrack side 
        panel editor to use this command.
        
        Returns:
            A Response object.
        """

        return self.prober.send_cmd("vis:start_fast_track")

    @deprecated("use vision.compensation.start_execute(...) instead!")
    def start_execute_compensation(self, comp_type: DieCompensationType, comp_mode: DieCompensationMode) -> Response:
        self.comm.send("vis:compensation:start_execute {0},{1}".format(comp_type.to_string(), comp_mode.to_string()))
        resp = Response.check_resp(self.comm.read_line())

        if not resp.ok():
            raise ProberException(resp.message())

        return resp

    def find_thermal_die_size(self) -> Tuple[float, float]:
        """Detect thermal expansion and return die size ratio.

        Returns:
            A tuple of (ThermalFactorX, ThermalFactorY)
        """
        self.comm.send("vis:find_thermal_die_size")
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1])

    def get_lens_zoom_level(self) -> float:
        """ Get current zoom level of the lens. 
        
            Returns:
                float: The current zoom level of the lens.
        """
        self.comm.send("vis:get_lens_zoom_level")
        resp = Response.check_resp(self.comm.read_line())
        return float(resp.message())

    def set_lens_zoom_level(self, level: float) -> None:
        """Set lens zoom level.

        Args:
            level (float): Zoom level, such as 1, 2, ..., 10

        Returns:
            None
        """
        self.comm.send(f"vis:set_lens_zoom_level {level}")
        Response.check_resp(self.comm.read_line())

    def get_light_status(self, camera: CameraMountPoint) -> bool:
        """Check whether light is on or off for a specific camera.

        Args:
            camera: e.g. 'scope', 'offaxis'

        Returns:
            True if light is ON
        """
        self.comm.send(f"vis:get_light_status {camera.to_string()}")
        resp = Response.check_resp(self.comm.read_line())
        return resp.message().strip().lower() == "1"
