from __future__ import annotations

import cmath
from dataclasses import dataclass
from types import NotImplementedType
from typing import Any, Self, overload


@dataclass
class Point:
    """A point in normal cartesian space with the origin at the bottom left."""

    inner: complex

    @classmethod
    def new(cls, x: float, y: float) -> Self:
        return cls(complex(x, y))

    def x(self) -> float:
        return self.inner.real

    def y(self) -> float:
        return self.inner.imag

    def __add__(self, other: Point) -> Point:
        return Point(self.inner + other.inner)

    def to_graphics_point(self, canvas_height: float) -> GraphicsPoint:
        return GraphicsPoint.new(self.x(), canvas_height - self.y())


@dataclass
class GraphicsPoint:
    """A point in graphics space, with the origin at the top left."""

    inner: complex

    @classmethod
    def new(cls, x: float, y: float) -> Self:
        return cls(complex(x, y))

    def x(self) -> float:
        return self.inner.real

    def y(self) -> float:
        return self.inner.imag

    def __add__(self, other: GraphicsPoint) -> GraphicsPoint:
        return GraphicsPoint(self.inner + other.inner)


@dataclass
class Polar:
    r: float
    theta: float

    def to_cartesian(self) -> Point:
        return Point(cmath.rect(self.r, self.theta))

    @classmethod
    def from_cartesian(cls, point: Point) -> Self:
        return cls(*cmath.polar(point.inner))

    def extend(self, incr: float) -> Self:
        return type(self)(self.r + incr, self.theta)

    def rotate(self, angle: float) -> Self:
        return type(self)(self.r, self.theta + angle)

    def relative_to(self, origin: Point) -> Point:
        return self.to_cartesian() + origin
        # return (Polar.from_cartesian(origin) + self).to_cartesian()

    @overload
    def __add__(self, other: Polar) -> Polar: ...

    @overload
    def __add__(self, other: Any) -> NotImplementedType: ...

    def __add__(self, other: Any) -> Polar | NotImplementedType:
        if not isinstance(other, Polar):
            return NotImplemented
        else:
            return Polar(self.r + other.r, self.theta + other.theta)
