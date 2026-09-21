from typing import Optional, Tuple

from sentio_prober_control.Sentio.Enumerations import FiberType, PowerMeterUnit, ProbePosition, Stage, UvwAxis
from sentio_prober_control.Sentio.Response import Response
from sentio_prober_control.Sentio.CommandGroups.CommandGroupBase import CommandGroupBase


class SiPHPositionerCommandGroup(CommandGroupBase):
    """Commands of a single SiPH positioner.

    This command group mirrors the SENTIO remote command section
    `siph:{top|bottom}:{position}:...` which is available for SENTIO 25.2 and newer.
    You are not meant to instantiate this class directly. Access it via the
    [SentioProber.siph](SiPHCommandGroup.md) command group:

    - `prober.siph.top.east`, `prober.siph.top.west`, ... for top positioners
    - `prober.siph.bottom.east`, `prober.siph.bottom.west` for bottom positioners
    - `prober.siph.east`, `prober.siph.west`, ... as shortcut for the top positioners

    Example:

    ```py
    from sentio_prober_control.Sentio.ProberSentio import SentioProber

    prober = SentioProber.create_prober("tcpip", "127.0.0.1:35555")
    cap = prober.siph.top.east.get_cap_sensor()
    prober.siph.bottom.west.set_hover(50)
    ```
    """

    def __init__(self, prober: 'SentioProber', stage: Stage, position: ProbePosition, selector: str) -> None: # type: ignore
        super().__init__(prober)

        self.__stage = stage
        self.__position = position
        self.__selector = selector


    @property
    def stage(self) -> Stage:
        """The probe stage (TopProbe or BottomProbe) this positioner belongs to."""
        return self.__stage


    @property
    def position(self) -> ProbePosition:
        """The position of this positioner."""
        return self.__position


    def coupling(self, axis: UvwAxis) -> None:
        """Start fiber coupling on the given UVW axis.

        Wraps the remote command `siph:{stage}:{position}:coupling`.

        Args:
            axis: The UVW axis to couple on.
        """
        self.comm.send(f"{self.__selector}:coupling {axis.to_string()}")
        Response.check_resp(self.comm.read_line())


    def enable_distance_sensor(self, enable: bool) -> None:
        """Enable or disable the hover distance search with the cap sensor.

        Wraps the remote command `siph:{stage}:{position}:enable_distance_sensor`.

        Args:
            enable: True to enable the distance sensor, False to disable it.
        """
        self.comm.send(f"{self.__selector}:enable_distance_sensor {enable}")
        Response.check_resp(self.comm.read_line())


    def fiber_power_reading(self, unit: Optional[PowerMeterUnit] = None, wavelength: Optional[int] = None) -> float:
        """Move to the power measurement site and read the optical power.

        Wraps the remote command `siph:{stage}:{position}:fiber_power_reading`.

        Args:
            unit: The unit of the returned value. If omitted the current power meter unit is used.
            wavelength: The wavelength in nanometer. Requires unit to be set.

        Returns:
            The measured power in the requested unit.
        """
        if wavelength is not None and unit is None:
            raise ValueError("A wavelength can only be given together with a unit.")

        args = []
        if unit is not None:
            args.append(unit.to_string())
        if wavelength is not None:
            args.append(str(wavelength))

        cmd = f"{self.__selector}:fiber_power_reading"
        if args:
            cmd += " " + ",".join(args)

        self.comm.send(cmd)
        resp = Response.check_resp(self.comm.read_line())
        return float(resp.message())


    def fine_alignment(self) -> None:
        """Run a fine alignment search for this positioner only.

        Wraps the remote command `siph:{stage}:{position}:fine_alignment`.
        """
        self.comm.send(f"{self.__selector}:fine_alignment")
        Response.check_resp(self.comm.read_line())


    def get_alignment(self, fiber_type: Optional[FiberType] = None) -> Tuple[bool, ...]:
        """Get the enable state of the fast alignment search types.

        Wraps the remote command `siph:{stage}:{position}:get_alignment`.

        Args:
            fiber_type: The fiber type to query. If omitted the fiber type configured
                for the positioner is used.

        Returns:
            One flag per search type in the order Coarse, Fine, Gradient and, depending
            on the fiber type, Rotary Gradient and/or Focal Gradient.
        """
        cmd = f"{self.__selector}:get_alignment"
        if fiber_type is not None:
            cmd += f" {fiber_type.to_string()}"

        self.comm.send(cmd)
        resp = Response.check_resp(self.comm.read_line())
        return tuple(tok.strip().lower() == "true" for tok in resp.message().split(","))


    def get_cap_sensor(self) -> float:
        """Get the capacitance sensor value.

        Wraps the remote command `siph:{stage}:{position}:get_cap_sensor`.

        Returns:
            The cap sensor value.
        """
        self.comm.send(f"{self.__selector}:get_cap_sensor")
        resp = Response.check_resp(self.comm.read_line())
        return float(resp.message())


    def get_fiber_length(self) -> float:
        """Get the fiber length.

        Wraps the remote command `siph:{stage}:{position}:get_fiber_length`.

        Returns:
            The fiber length in micrometer.
        """
        self.comm.send(f"{self.__selector}:get_fiber_length")
        resp = Response.check_resp(self.comm.read_line())
        return float(resp.message())


    def get_nanocube_xy(self) -> Tuple[float, float]:
        """Get the current NanoCube XY position.

        Wraps the remote command `siph:{stage}:{position}:get_nanocube_xy`.

        Returns:
            The current X and Y position in micrometer.
        """
        self.comm.send(f"{self.__selector}:get_nanocube_xy")
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1])


    def get_nanocube_z(self) -> float:
        """Get the current NanoCube Z position.

        Wraps the remote command `siph:{stage}:{position}:get_nanocube_z`.

        Returns:
            The current Z position in micrometer.
        """
        self.comm.send(f"{self.__selector}:get_nanocube_z")
        resp = Response.check_resp(self.comm.read_line())
        return float(resp.message())


    def move_nanocube_xy(self, x: float, y: float) -> Tuple[float, float]:
        """Move the NanoCube to an XY position.

        Wraps the remote command `siph:{stage}:{position}:move_nanocube_xy`.
        The movement range is limited to 0 to 100 micrometer.

        Args:
            x: The target X position in micrometer.
            y: The target Y position in micrometer.

        Returns:
            The X and Y position after the move in micrometer.
        """
        if not (0 <= x <= 100 and 0 <= y <= 100):
            raise ValueError("X and Y values must be between 0 and 100 micrometer.")

        self.comm.send(f"{self.__selector}:move_nanocube_xy {x},{y}")
        resp = Response.check_resp(self.comm.read_line())
        tok = resp.message().split(",")
        return float(tok[0]), float(tok[1])


    def move_nanocube_z(self, z: float) -> float:
        """Move the NanoCube to a Z position.

        Wraps the remote command `siph:{stage}:{position}:move_nanocube_z`.

        Args:
            z: The target Z position in micrometer.

        Returns:
            The Z position after the move in micrometer.
        """
        self.comm.send(f"{self.__selector}:move_nanocube_z {z}")
        resp = Response.check_resp(self.comm.read_line())
        return float(resp.message())


    def move_origin(self) -> None:
        """Move the positioner to its origin position.

        Wraps the remote command `siph:{stage}:{position}:move_origin`.
        The NanoCube XY moves back to 50 micrometer and the UVW axes move back to
        the position set during hover height training.
        """
        self.comm.send(f"{self.__selector}:move_origin")
        Response.check_resp(self.comm.read_line())


    def pivot_point(self) -> None:
        """Run the pivot point calibration.

        Wraps the remote command `siph:{stage}:{position}:pivot_point`.
        """
        self.comm.send(f"{self.__selector}:pivot_point")
        Response.check_resp(self.comm.read_line())


    def set_alignment(self,
                      fiber_type: FiberType,
                      coarse: bool,
                      fine: bool,
                      gradient: bool,
                      rotary_gradient: Optional[bool] = None,
                      focal_gradient: Optional[bool] = None) -> None:
        """Enable or disable the fast alignment search types.

        Wraps the remote command `siph:{stage}:{position}:set_alignment`. SENTIO
        expects one flag per search type supported by the fiber type: Coarse, Fine and
        Gradient for all types, Rotary Gradient for Array and LensedArray fibers and
        Focal Gradient for Lensed and LensedArray fibers.

        Args:
            fiber_type: The fiber type the settings apply to.
            coarse: Enable the coarse search.
            fine: Enable the fine search.
            gradient: Enable the gradient search.
            rotary_gradient: Enable the rotary gradient search (Array, LensedArray).
            focal_gradient: Enable the focal gradient search (Lensed, LensedArray).
        """
        flags = [coarse, fine, gradient]
        flags += [flag for flag in (rotary_gradient, focal_gradient) if flag is not None]

        args = ",".join([fiber_type.to_string()] + [str(flag) for flag in flags])
        self.comm.send(f"{self.__selector}:set_alignment {args}")
        Response.check_resp(self.comm.read_line())


    def set_hover(self, gap: float) -> None:
        """Set the hover gap.

        Wraps the remote command `siph:{stage}:{position}:set_hover`.

        Args:
            gap: The hover gap in micrometer.
        """
        self.comm.send(f"{self.__selector}:set_hover {gap}")
        Response.check_resp(self.comm.read_line())


    def set_origin(self) -> None:
        """Set the current position as the origin position.

        Wraps the remote command `siph:{stage}:{position}:set_origin`.
        """
        self.comm.send(f"{self.__selector}:set_origin")
        Response.check_resp(self.comm.read_line())


    def set_pivot_point(self, rotary_angle_1: float, rotary_angle_2: float, leveling_angle: float, repeats: int) -> None:
        """Set the parameters of the pivot point calibration.

        Wraps the remote command `siph:{stage}:{position}:set_pivot_point`.

        Args:
            rotary_angle_1: The first rotary angle in degree.
            rotary_angle_2: The second rotary angle in degree.
            leveling_angle: The leveling angle in degree.
            repeats: The number of repetitions.
        """
        self.comm.send(f"{self.__selector}:set_pivot_point {rotary_angle_1},{rotary_angle_2},{leveling_angle},{repeats}")
        Response.check_resp(self.comm.read_line())
