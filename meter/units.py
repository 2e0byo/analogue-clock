from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Self


@dataclass
class Mm:
    val: float

    def px(self) -> float:
        # SVGs are 96 DPI = 96 px per 25.4 mm
        return 96 * self.val / 25.4

    @classmethod
    def from_px(cls, val: float) -> Self:
        return cls(val * 25.4 / 96)


@dataclass
class Deg:
    val: float

    def rad(self) -> float:
        return self.val * pi / 180

    @classmethod
    def from_rad(cls, val: float) -> Self:
        return cls(180 * val / pi)

    def __sub__(self, other: Deg) -> Self:
        return type(self)(self.val - other.val)

    def __add__(self, other: Deg) -> Self:
        return type(self)(self.val + other.val)
