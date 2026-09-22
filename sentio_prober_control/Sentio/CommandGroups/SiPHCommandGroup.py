from sentio_prober_control.Sentio.Compatibility import Compatibility, CompatibilityLevel
from sentio_prober_control.Sentio.Enumerations import ProbePosition, UvwAxis, Stage
from sentio_prober_control.Sentio.CommandGroups.SiPHPositionerCommandGroup import SiPHPositionerCommandGroup
from sentio_prober_control.Sentio.Response import Response
from sentio_prober_control.Sentio.CommandGroups.ModuleCommandGroupBase import ModuleCommandGroupBase


class SiPHCommandGroup(ModuleCommandGroupBase):
    """This command group contains functions for working with SiPH applications.
    You are not meant to instantiate this class directly. Access it via the siph attribute
    of the [SentioProber](SentioProber.md) class.

    Commands that address a single SiPH positioner mirror the remote command structure
    `siph:{top|bottom}:{position}:...` and are available through the
    [SiPHPositionerCommandGroup](SiPHPositionerCommandGroup.md) sub groups listed below
    (SENTIO 25.2 and newer). The `top` part is optional as in the remote command.

    Attributes:
        top.east (SiPHPositionerCommandGroup): Top east positioner. Also available as siph.east.
        top.west (SiPHPositionerCommandGroup): Top west positioner. Also available as siph.west.
        top.north (SiPHPositionerCommandGroup): Top north positioner. Also available as siph.north.
        top.south (SiPHPositionerCommandGroup): Top south positioner. Also available as siph.south.
        top.northeast (SiPHPositionerCommandGroup): Top northeast positioner. Also available as siph.northeast.
        top.northwest (SiPHPositionerCommandGroup): Top northwest positioner. Also available as siph.northwest.
        top.southeast (SiPHPositionerCommandGroup): Top southeast positioner. Also available as siph.southeast.
        top.southwest (SiPHPositionerCommandGroup): Top southwest positioner. Also available as siph.southwest.
        bottom.east (SiPHPositionerCommandGroup): Bottom east positioner.
        bottom.west (SiPHPositionerCommandGroup): Bottom west positioner.

    Example:

    ```py
    from sentio_prober_control.Sentio.ProberSentio import SentioProber

    prober = SentioProber.create_prober("tcpip", "127.0.0.1:35555")
    cap_east = prober.siph.east.get_cap_sensor()            # same as prober.siph.top.east
    cap_west = prober.siph.bottom.west.get_cap_sensor()
    prober.siph.fast_alignment()
    ```
    """

    class _TopPositioners:
        """Access to the top SiPH positioners (siph:top:{position}:...)."""
        def __init__(self, prober: 'SentioProber') -> None: # type: ignore
            def make(position: ProbePosition) -> SiPHPositionerCommandGroup:
                return SiPHPositionerCommandGroup(prober, Stage.TopProbe, position, f"siph:top:{position.to_string().lower()}")

            self.east: SiPHPositionerCommandGroup = make(ProbePosition.East)
            self.west: SiPHPositionerCommandGroup = make(ProbePosition.West)
            self.north: SiPHPositionerCommandGroup = make(ProbePosition.North)
            self.south: SiPHPositionerCommandGroup = make(ProbePosition.South)
            self.northeast: SiPHPositionerCommandGroup = make(ProbePosition.NorthEast)
            self.northwest: SiPHPositionerCommandGroup = make(ProbePosition.NorthWest)
            self.southeast: SiPHPositionerCommandGroup = make(ProbePosition.SouthEast)
            self.southwest: SiPHPositionerCommandGroup = make(ProbePosition.SouthWest)

    class _BottomPositioners:
        """Access to the bottom SiPH positioners (siph:bottom:{position}:...). SENTIO
        provides bottom SiPH positioners for the east and west position only."""
        def __init__(self, prober: 'SentioProber') -> None: # type: ignore
            def make(position: ProbePosition) -> SiPHPositionerCommandGroup:
                return SiPHPositionerCommandGroup(prober, Stage.BottomProbe, position, f"siph:bottom:{position.to_string().lower()}")

            self.east: SiPHPositionerCommandGroup = make(ProbePosition.East)
            self.west: SiPHPositionerCommandGroup = make(ProbePosition.West)


    def __init__(self, prober : 'SentioProber') -> None: # type: ignore
        super().__init__(prober, "siph")

        # Per positioner command groups; the remote commands behind them exist since SENTIO 25.2
        if Compatibility.level >= CompatibilityLevel.Sentio_25_2:
            self.top = self._TopPositioners(prober)
            self.bottom = self._BottomPositioners(prober)

            # Top positioners are also available without the "top" part, as in the remote command
            self.east = self.top.east
            self.west = self.top.west
            self.north = self.top.north
            self.south = self.top.south
            self.northeast = self.top.northeast
            self.northwest = self.top.northwest
            self.southeast = self.top.southeast
            self.southwest = self.top.southwest


    def fast_alignment(self) -> None:
        """Perform fast fiber alignment."""
        self.comm.send("siph:fast_alignment")
        Response.check_resp(self.comm.read_line())


    def get_intensity(self, channel : int = 1) -> float:
        """Get the current intensity value.

         Args:
            channel: The channel to return the intensite of. One-Based index, must be either 1 or 2.
        """

        self.comm.send(f"siph:get_intensity {channel}")
        resp = Response.check_resp(self.comm.read_line())
        return float(resp.message())


    def gradient_search(self) -> None:
        """Execute SiPh gradient search.

           Returns:
                None
        """

        self.comm.send("siph:gradient_search")
        Response.check_resp(self.comm.read_line())


    def move_hover(self, probe: ProbePosition) -> None:
        """Move SiPh probe to hover height.

        Args:
            probe: The probe on which the SiPh probe is mounted.
        """

        self.comm.send(f"siph:move_hover {probe.to_string()}")
        Response.check_resp(self.comm.read_line())


    def move_separation(self, probe: ProbePosition) -> None:
        """Move SiPh probe to separation height.

        Args:
            probe: The probe on which the SiPh probe is mounted.

        Returns:
            None
        """

        self.comm.send(f"siph:move_separation {probe.to_string()}")
        Response.check_resp(self.comm.read_line())


    def move_position_uvw(self, probe: ProbePosition, axis: UvwAxis, degree: float) -> float:
        """Move the SiPH positioner target axis with a relative degree.

        !!! danger "Deprecated since Sentio 25.2<br/>            This function is obsolete and will be removed in a future release. It only addresses top positioners.             Use [`probe.[top|bottom].{east|west|north|south|northeast|northwest|southeast|southwest}.move_uvw()`](StageCommandGroup.md#sentio_prober_control.Sentio.CommandGroups.StageCommandGroup.StageCommandGroup.move_uvw) instead."

        Args:
            probe: The positioner ID to move (East or West).
            axis: The axis to move (U, V, or W).
            degree: The relative degree to move.

        Returns:
            The current position of the axis after movement.
        """
        self.comm.send(f"siph:move_position_uvw {probe.to_string()},{axis.to_string()},{degree}")
        resp = Response.check_resp(self.comm.read_line())

        return float(resp.message())


    def set_pivot_point(self, rotary_angle_1: float, rotary_angle_2: float, leveling_angle: float, repeats: int) -> None:
        """Set the parameters for the pivot point function.

        Args:
            rotary_angle_1: The first rotary angle.
            rotary_angle_2: The second rotary angle.
            leveling_angle: The leveling angle.
            repeats: The number of repetitions.

        Returns:
            A Response object containing the command execution status.
        """
        self.comm.send(f"siph:set_pivot_point {rotary_angle_1},{rotary_angle_2},{leveling_angle},{repeats}")
        Response.check_resp(self.comm.read_line())


    def download_graph_data(self, file_path: str, file_name: str) -> None:
        """Download the graph data and save it to the specified location.

        Args:
            file_path: The directory path where the graph data will be saved.
            file_name: The name of the file to save the graph data.

        Returns:
            A Response object containing the command execution status.
        """
        Compatibility.assert_min(CompatibilityLevel.Sentio_25_2)

        self.comm.send(f"siph:download_graph_data {file_path}, {file_name}")
        Response.check_resp(self.comm.read_line())


    def start_tracking(self, timeout: int = 60) -> int:
        """Start the SiPH positioner gradient tracking search asynchronously.

        Args:
            timeout: Timeout value in seconds (range: 1~600). Default is 60 sec.

        Returns:
            The asynchronous command ID, which can be used to check status or abort.
        """
        self.comm.send(f"siph:start_tracking {timeout}")
        resp = Response.check_resp(self.comm.read_line())

        # Extract asynchronous command ID from response
        command_id = int(resp.cmd_id())
        return command_id


