from abc import ABC, abstractmethod
from typing import Type, Union

from metrics_dataclasses import TimesXY
from physics import Speed2Points, Slope2Points, Acceleration
from point_types import ExitOrEntryType, ExitType

"""
When calculating angle, speed, etc. using only the last 2 points 
causes huge errors at low mouse speeds, 
due to pixels being chessboard-like boxes.
A better solution would be (linear) fitting of more than 2 points.
"""


class _SinglePointHandler(ABC):
    """
    Points right before browser exit:
        P1 -> P2 -> P3 (exit point; or "critical").

    Points right after browser entry:
        P1 (entry point; or "critical") -> P2 -> P3.
    """
    # Currently up to two extra points are needed from a critical point
    MAX_EXTRA_INDEX = 2

    def __init__(self, crit_index: int, mouse_txy: TimesXY):
        self.x_list = mouse_txy.x
        self.y_list = mouse_txy.y
        self.t_list = mouse_txy.time
        self.crit_index = crit_index
        self.max_index = len(self.x_list) - 1
        self.index_too_small = self._index_too_small()
        self.index_too_large = self._index_too_large()

    def _index_too_small(self):
        return self.crit_index - self.MAX_EXTRA_INDEX < 0

    def _index_too_large(self):
        return self.crit_index + self.MAX_EXTRA_INDEX > self.max_index

    def index_in_txy(self, t_critical):
        return self.t_list.index(t_critical)

    def p_i(self, extra_index):
        index = self.crit_index + extra_index
        return self.x_list[index], self.y_list[index]

    def t_i(self, extra_index):
        index = self.crit_index + extra_index
        return self.t_list[index]

    @property
    @abstractmethod
    def p3(self):
        pass

    @property
    @abstractmethod
    def p2(self):
        pass

    @property
    @abstractmethod
    def p1(self):
        pass

    @property
    @abstractmethod
    def t1(self):
        pass

    @property
    @abstractmethod
    def t2(self):
        pass

    @property
    @abstractmethod
    def t3(self):
        pass


class ExitHandler(_SinglePointHandler):
    @property
    def p3(self):
        return self.p_i(extra_index=0)

    @property
    def p2(self):
        return self.p_i(extra_index=-1)

    @property
    def p1(self):
        return self.p_i(extra_index=-2)

    @property
    def t3(self):
        return self.t_i(extra_index=0)

    @property
    def t2(self):
        return self.t_i(extra_index=-1)

    @property
    def t1(self):
        return self.t_i(extra_index=-2)

    @property
    def critical_angle(self):
        if self.index_too_small:
            return None
        return Slope2Points(p1=self.p2, p2=self.p3).angle

    @property
    def critical_speed(self):
        if self.index_too_small:
            return None
        return Speed2Points(p1=self.p2, p2=self.p3,
                            t1=self.t2, t2=self.t3).speed

    @property
    def critical_acceleration(self):
        if self.index_too_small:
            return None
        return Acceleration(p1=self.p1, p2=self.p2, p3=self.p3,
                            t1=self.t1, t2=self.t2, t3=self.t3).acceleration


class EntryHandler(_SinglePointHandler):
    @property
    def p3(self):
        return self.p_i(extra_index=2)

    @property
    def p2(self):
        return self.p_i(extra_index=1)

    @property
    def p1(self):
        """First entry point"""
        return self.p_i(extra_index=0)

    @property
    def t3(self):
        return self.t_i(extra_index=2)

    @property
    def t2(self):
        return self.t_i(extra_index=1)

    @property
    def t1(self):
        return self.t_i(extra_index=0)

    @property
    def critical_angle(self):
        """Return approximate angle when exiting browser."""
        if self.index_too_large:
            return None
        return Slope2Points(p1=self.p1, p2=self.p2).angle

    @property
    def critical_speed(self):
        if self.index_too_large:
            return None
        return Speed2Points(p1=self.p1, p2=self.p2,
                            t1=self.t1, t2=self.t2).speed

    @property
    def critical_acceleration(self):
        if self.index_too_large:
            return None
        return Acceleration(
            p1=self.p1, p2=self.p2, p3=self.p3,
            t1=self.t1, t2=self.t2, t3=self.t3).acceleration


class Metrics:
    def __init__(self, mouse_txy: TimesXY, crit_type: Type[ExitOrEntryType], crit_indices):
        self.crit_indices = crit_indices
        self.crit_type = crit_type
        self.mouse_txy = mouse_txy
        self.point_handler: Type[Union[ExitHandler, EntryHandler]] = self._point_handler()

    def _point_handler(self):
        if self.crit_type == ExitType:
            return ExitHandler
        else:
            return EntryHandler

    def critical_angles(self):
        angles = []
        for i in self.crit_indices:
            handler = self.point_handler(crit_index=i, mouse_txy=self.mouse_txy)
            angle = handler.critical_angle
            if angle:
                angles.append(angle)
        return angles

    def critical_speeds(self):
        speeds = []
        for i in self.crit_indices:
            handler = self.point_handler(crit_index=i, mouse_txy=self.mouse_txy)
            speed = handler.critical_speed
            speeds.append(speed)
        return speeds

    def critical_accelerations(self):
        accelerations = []
        for i in self.crit_indices:
            handler = self.point_handler(crit_index=i, mouse_txy=self.mouse_txy)
            acceleration = handler.critical_acceleration
            accelerations.append(acceleration)
        return accelerations
