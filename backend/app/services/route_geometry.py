"""Map geometry for the demo routes (Bengaluru, approximate paths).

Coordinates are illustrative waypoints, not road-snapped paths; they are
enough to move a shuttle marker along a plausible line on a map.
"""

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


Point = tuple[float, float]  # (latitude, longitude)


@dataclass(frozen=True)
class RouteGeometry:
    depot: Point
    # Pickup stop first, destination last.
    path: list[Point]

    @property
    def pickup(self) -> Point:
        return self.path[0]

    @property
    def destination(self) -> Point:
        return self.path[-1]


_HOME = (12.9719, 77.6412)    # Indiranagar
_OFFICE = (13.0450, 77.6205)  # Manyata Tech Park
_DEPOT = (12.9583, 77.6487)   # HAL depot
_WAYPOINTS = [
    (12.9784, 77.6408),
    (12.9890, 77.6475),
    (13.0010, 77.6520),
    (13.0155, 77.6440),
    (13.0290, 77.6330),
    (13.0390, 77.6250),
]

_MORNING = RouteGeometry(depot=_DEPOT, path=[_HOME, *_WAYPOINTS, _OFFICE])
_EVENING = RouteGeometry(depot=_DEPOT, path=list(reversed(_MORNING.path)))


def geometry_for(pickup_location: str) -> RouteGeometry:
    return _MORNING if pickup_location == "Home" else _EVENING


def _distance(a: Point, b: Point) -> float:
    """Great-circle distance in kilometres."""

    lat1, lon1, lat2, lon2 = map(radians, (*a, *b))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def point_along(path: list[Point], fraction: float) -> Point:
    """The point `fraction` (0-1) of the way along a polyline, by distance."""

    fraction = min(max(fraction, 0.0), 1.0)
    legs = [_distance(a, b) for a, b in zip(path, path[1:])]
    target = sum(legs) * fraction

    for (a, b), length in zip(zip(path, path[1:]), legs):
        if target <= length and length > 0:
            t = target / length
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        target -= length

    return path[-1]
