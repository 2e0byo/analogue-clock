from itertools import chain
import math
from math import pi
from functools import partial
from types import NotImplementedType
from typing import Self, Callable, Any, overload, Literal
import cmath
from numbers import Complex
from dataclasses import dataclass
from pathlib import Path


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

    def __add__(self, other: Any) -> "Polar" | NotImplementedType:
        if not isinstance(other, Polar):
            return NotImplemented
        else:
            return Polar(self.r + other.r, self.theta + other.theta)


@dataclass(kw_only=True)
class Element:
    fill: str = "none"
    stroke: str = "black"
    stroke_width: float = 1.5
    opacity: float = 1
    style: str = "none"


@dataclass(kw_only=True)
class Text(Element):
    point: Point
    text: str
    font: str = "Arial"
    size: float = 30
    weight: float = 500
    # rotate: list[float] | None = None
    rotate: float | None = None
    anchor: str = "left"

    @classmethod
    def simple(cls, point: Point, text: str, **kwargs) -> Self:
        return cls(text=text, point=point, **kwargs)

    def render(self, canvas_height: float) -> str:
        pt = self.point.to_graphics_point(canvas_height)
        rotate = (
            f'transform="rotate({self.rotate} {pt.x()} {pt.y()})"'
            if self.rotate
            else ""
        )

        return f"""\
<text
 {rotate}
 font-weight="{self.weight}" fill="{self.stroke}" opacity="{self.opacity}" text-anchor="{self.anchor}"
 x="{pt.x()}" y="{pt.y()}" font-family="{self.font}" font-size="{self.size}" >{self.text}</text>
        """


@dataclass(kw_only=True)
class TextPath(Element):
    length: str | None = None
    text: str
    font: str = "Arial"
    size: float = 30
    weight: float = 500
    method: Literal["align", "stretch"] = "align"
    href: str
    length_adjust: Literal["spacing", "spacingAndGlyphs"] = "spacing"
    side: Literal["left", "right"] = "left"

    def render(self, canvas_height: float) -> str:
        length = f'textLength="{self.length}"' if self.length else ""
        return f"""\
<text {length}>
<textPath
 href="{self.href}" method="{self.method}" lengthAdjust="{self.length_adjust}"
 font-weight="{self.weight}" fill="{self.stroke}" opacity="{self.opacity}"
 font-family="{self.font}" font-size="{self.size}" side="{self.side}"
>
{self.text}
</textPath>
</text>
        """


class Defs:
    def __init__(self, *tags) -> None:
        self.tags = tags

    def render(self, canvas_height: float) -> str:
        return f"""\
<defs>
{"\n".join(tag.render(canvas_height) for tag in self.tags)}
</defs>
        """


@dataclass
class Raw:
    id: str
    content: str | None = None
    tags: str | None = None
    type: str = "g"
    translate: Point | None = None
    rotate: float | None = None

    def render(self, canvas_height: float) -> str:
        transforms = []
        if pt := self.translate:
            pt = pt.to_graphics_point(canvas_height)
            transforms.append(f"translate({pt.x()} {pt.y()})")
        if self.rotate:
            transforms.append(f"rotate({self.rotate})")
        transform = f'transform="{" ".join(transforms)}"' if transforms else ""

        return f"""\
<{self.type}
  id="{self.id}"
  {transform} {self.tags or ""} >
  {self.content or ""}
</{self.type}>
        """


type Renderer = Callable[[float], str]

CLOCKWISE = 1
ANTI_CLOCKWISE = 0


@dataclass
class ArrowHeadConfig:
    length: float
    width: float


@dataclass(kw_only=True)
class ArrowHead(Element):
    config: ArrowHeadConfig
    start: Point
    angle: float

    def render(self, canvas_height: float) -> str:
        base = Polar(-self.config.length, self.angle).relative_to(self.start)
        arrow_top = (
            Polar(self.config.width / 2, self.angle + (pi / 2))
            .relative_to(base)
            .to_graphics_point(canvas_height)
        )
        arrow_bottom = (
            Polar(self.config.width / 2, self.angle - (pi / 2))
            .relative_to(base)
            .to_graphics_point(canvas_height)
        )
        start = self.start.to_graphics_point(canvas_height)
        return f"""\
<path
    fill="{self.fill}"
    stroke="{self.stroke}"
    stroke-width="{self.stroke_width}"
    d="
       M {start.x()} {start.y()}
       L {arrow_top.x()} {arrow_top.y()}
       L {arrow_bottom.x()} {arrow_bottom.y()}
       Z
      "
/>
        """


@dataclass(kw_only=True)
class Arc(Element):
    id: str | None = None
    start: Polar
    end: Polar
    center: Point
    left_arrowhead: ArrowHeadConfig | None = None
    right_arrowhead: ArrowHeadConfig | None = None

    def angle(self) -> float:
        return self.end.theta - self.start.theta

    def flags(self) -> tuple[int, int]:
        start_above_origin = 0 < self.start.theta < pi
        end_above_origin = 0 < self.end.theta < pi
        match start_above_origin, end_above_origin:
            case True, True:
                large = 1 if abs(self.angle()) > math.pi else 0
                sweep = CLOCKWISE
            case True, False | False, True:
                large = 1
                sweep = 0
            case False, False:
                large = 1 if abs(self.angle()) > math.pi else 0
                sweep = 0
        return large, sweep

    def render(self, canvas_height: float) -> str:
        assert self.start.r == self.end.r
        # note assumes start is to the left of end
        start = self.start.relative_to(self.center).to_graphics_point(canvas_height)
        end = self.end.relative_to(self.center).to_graphics_point(canvas_height)
        large, sweep = self.flags()
        radius = self.start.r
        rotation = 0
        id = f'id="{self.id}"' if self.id else ""
        arrows = []
        if config := self.left_arrowhead:
            arrows.append(
                ArrowHead(
                    fill=self.stroke,
                    stroke="none",
                    start=self.start.relative_to(self.center),
                    angle=self.start.theta + pi / 2,
                    config=config,
                ).render(canvas_height)
            )
        if config := self.right_arrowhead:
            arrows.append(
                ArrowHead(
                    fill=self.stroke,
                    stroke="none",
                    start=self.end.relative_to(self.center),
                    angle=self.end.theta - pi / 2,
                    config=config,
                ).render(canvas_height)
            )

        return f"""\
<path
    {id}
    fill="{self.fill}"
    stroke="{self.stroke}"
    stroke-width="{self.stroke_width}"
    d = "
        M {start.x()} {start.y()}
        A {radius} {radius} {rotation} {large} {sweep} {end.x()} {end.y()}
    "
/>
{"\n".join(arrows)}
        """


@dataclass(kw_only=True)
class Band(Arc):
    height: float

    def render(self, canvas_height: float) -> str:
        start1 = self.start.relative_to(self.center).to_graphics_point(canvas_height)
        end1 = self.end.relative_to(self.center).to_graphics_point(canvas_height)
        start2 = (
            self.end.extend(self.height)
            .relative_to(self.center)
            .to_graphics_point(canvas_height)
        )
        end2 = (
            self.start.extend(self.height)
            .relative_to(self.center)
            .to_graphics_point(canvas_height)
        )
        large, sweep = self.flags()
        r1 = self.start.r
        r2 = r1 + self.height
        rotation = 0

        return f"""\
<path
    fill="{self.fill}"
    style="{self.style}"
    stroke="{self.stroke}"
    stroke-width="{self.stroke_width}"
    d = "
        M {start1.x()} {start1.y()}
        A {r1} {r1} {rotation} {large} {sweep} {end1.x()} {end1.y()}
        L {start2.x()} {start2.y()}
        A {r2} {r2} {rotation} {large} {1 - sweep} {end2.x()} {end2.y()}
        Z
    "
/>
        """


@dataclass(kw_only=True)
class Line(Element):
    start: Point
    end: Point

    def render(self, canvas_height: float) -> str:
        start = self.start.to_graphics_point(canvas_height)
        end = self.end.to_graphics_point(canvas_height)
        return f"""\
<g>
  <line x1="{start.x()}" y1="{start.y()}" x2="{end.x()}" y2="{end.y()}"
        stroke="{self.stroke}" stroke-width="{self.stroke_width}" />
</g>
        """

    @classmethod
    def on_radial(cls, origin: Point, start: Polar, length: float, **kwargs) -> Self:
        return cls(
            start=start.relative_to(origin),
            end=start.extend(length).relative_to(origin),
            **kwargs,
        )


def polarise_arc(width: float, rise: float) -> tuple[Polar, Polar]:
    """Given the width and rise of a chord, return the two ends as polar
    coordinates relative to the center."""

    half_width = width / 2
    a = (half_width**2 + rise**2) ** 0.5
    alpha = math.atan(half_width / rise)
    half_theta = pi - 2 * alpha

    half_a = a / 2
    r = half_a / math.cos(alpha)

    return Polar(r, pi - half_theta), Polar(r, half_theta)


@dataclass
class Mm:
    val: float

    def px(self) -> float:
        # SVGs are 96 DPI = 96 px per 25.4 mm
        return 96 * self.val / 25.4


def degrees(radians: float) -> float:
    return 360 * radians / 2 * pi


@dataclass
class Canvas:
    width: float
    height: float

    def render(self) -> str:
        return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{self.width}"
  height="{self.height}"
  viewBox="0 0 {self.width} {self.height}"
>
<rect width="{self.width}" height="{self.height}" fill="white"/>
        """


canvas = Canvas(round(Mm(235).px()), round(Mm(181).px()))

start, end = polarise_arc(Mm(165.1).px(), Mm(33.7).px())
top_offset = Mm(60).px()
meter_center = Point.new(canvas.width / 2, canvas.height - top_offset - start.r)
arc = Arc(start=start, end=end, center=meter_center)


mksun = partial(
    Raw,
    "sun",
    """
<circle cx="0" cy="0" r="10" fill="none" stroke="black" stroke-width="1.8"/>
<g stroke="black" stroke-width="1.5">
  <line x1="0" y1="-17" x2="0" y2="-25"/>
  <line x1="0" y1="17" x2="0" y2="25"/>
  <line x1="-17" y1="0" x2="-25" y2="0"/>
  <line x1="17" y1="0" x2="25" y2="0"/>
  <line x1="-12" y1="-12" x2="-18" y2="-18"/>
  <line x1="12" y1="-12" x2="18" y2="-18"/>
  <line x1="-12" y1="12" x2="-18" y2="18"/>
  <line x1="12" y1="12" x2="18" y2="18"/>
</g>
""",
)
mkmoon = partial(
    Raw,
    "moon",
    """
<path d="M 8,-16
         A 17,17 0 1 0 8,16
         A 12,17 0 0 1 8,-16 Z"
 fill="none" stroke="black" stroke-width="1.8"/>
    """,
    rotate=degrees(start.theta / 2) - 7,
)

flat = Polar(150, 0)
center = Point.new(300, 300)

minor_tick = partial(
    Line.on_radial, origin=meter_center, stroke_width=1, length=Mm(4).px()
)
major_tick = partial(
    Line.on_radial, origin=meter_center, stroke_width=1.5, length=Mm(6).px()
)
mini_tick = partial(
    Line.on_radial, origin=meter_center, stroke_width=1.5, length=Mm(2).px()
)
step = arc.angle() / 12


def ticks(hour: int) -> list[Line]:
    lines = []
    if hour % 3 == 0:
        lines.append(major_tick(start=start.rotate(step * hour)))
    else:
        lines.append(minor_tick(start=start.rotate(step * hour)))
    mini = partial(Line.on_radial, origin=meter_center, stroke_width=1.5)
    lines.extend(
        [
            mini(length=Mm(2).px(), start=start.rotate(step * (hour + 0.25))),
            mini(length=Mm(3).px(), start=start.rotate(step * (hour + 0.5))),
            mini(length=Mm(2).px(), start=start.rotate(step * (hour + 0.75))),
        ]
    )
    return lines


def number(val: int | str, rotation: float, **kwargs) -> Text:
    rise = Mm(15).px()
    point = start.extend(rise).rotate(rotation).relative_to(meter_center)
    angle_from_vertical = (pi / 2) - start.rotate(rotation).theta
    degrees = 180 * angle_from_vertical / pi
    return Text(text=str(val), point=point, anchor="middle", rotate=degrees, **kwargs)


img = [
    # defs
    Defs(
        Raw(
            id="bar-gradient",
            content="""
          <stop style="stop-color:#808080;stop-opacity:0.9;" offset="0.1" />
          <stop style="stop-color:#8f8f8f;stop-opacity:0.1;" offset="0.9" />
        """,
            type="linearGradient",
        ),
        Raw(
            id="bar-gradient-2",
            content="""
          <stop style="stop-color:#8f8f8f;stop-opacity:0.1;" offset="0.1" />
          <stop style="stop-color:#808080;stop-opacity:0.7;" offset="0.9" />
        """,
            type="linearGradient",
        ),
    ),
    arc,
    mkmoon(translate=start.extend(Mm(-15).px()).relative_to(meter_center)),
    mksun(translate=start.extend(Mm(34).px()).relative_to(meter_center)),
    ## ticks
    *chain.from_iterable(ticks(x) for x in range(0, 12)),
    major_tick(start=start.rotate(12 * step)),
    ## text
    number(12, 0 * step, opacity=0.5),
    number(3, 3 * step),
    number(6, 6 * step),
    number(9, 9 * step),
    number(12, 12 * step),
    #
    Band(
        start=start.extend(Mm(7).px()),
        end=start.extend(Mm(7).px()).rotate(8 * step),
        height=Mm(5).px(),
        center=meter_center,
        style="fill:url(#bar-gradient)",
        stroke="none",
    ),
    Band(
        start=start.extend(Mm(-5).px()).rotate(9.5 * step),
        end=end.extend(Mm(-5).px()),
        height=Mm(-5).px(),
        center=meter_center,
        style="fill:url(#bar-gradient-2)",
        stroke="none",
    ),
    #
    Arc(
        stroke="none",
        start=start.rotate(-step * 2),
        end=start,
        center=meter_center,
        id="pastLabel",
    ),
    TextPath(text="PAST", href="#pastLabel"),
    Arc(
        stroke="none",
        end=end.rotate(step * 3),
        start=end.rotate(step * 0.25),
        center=meter_center,
        id="futureLabel",
    ),
    TextPath(text="FUTURE", href="#futureLabel", side="left"),
    #
    Arc(
        start=start.extend(Mm(7.5).px()).rotate(1 * step),
        end=start.extend(Mm(7.5).px()).rotate(8 * step),
        center=meter_center,
        stroke="none",
        id="dayZzz",
    ),
    TextPath(text="ZZZZZ", href="#dayZzz", size=20, method="align", length="80"),
    Arc(
        start=start.extend(Mm(-9.5).px()).rotate(11 * step),
        end=end.extend(Mm(-9.5).px()),
        center=meter_center,
        stroke="none",
        id="nightZzz",
    ),
    TextPath(text="ZZZ", href="#nightZzz", size=20, method="align", length="50"),
    Arc(
        start=start.extend(Mm(-3).px()).rotate(-step * 2),
        end=start.extend(Mm(-3).px()).rotate(-step * 0.75),
        center=meter_center,
        stroke="black",
        left_arrowhead=ArrowHeadConfig(length=Mm(3).px(), width=Mm(2).px()),
    ),
    Arc(
        start=end.extend(Mm(-3).px()).rotate(step * 0.25),
        end=end.extend(Mm(-3).px()).rotate(step * 2.25),
        center=meter_center,
        stroke="black",
        right_arrowhead=ArrowHeadConfig(length=Mm(3).px(), width=Mm(2).px()),
    ),
    # fake hand for now
    Line.on_radial(
        meter_center,
        start.rotate(step * 0.1).extend(-Mm(90).px()),
        # Polar(Mm(30).px(), start.theta + 5.6 * step),
        Mm(93).px(),
    ),
]

# mksun(translate=flat.rotate(1 * pi / 5).relative_to(center)),
# mksun(translate=flat.rotate(2 * pi / 5).relative_to(center)),
# mksun(translate=flat.rotate(3 * pi / 5).relative_to(center)),
# mksun(translate=flat.rotate(4 * pi / 5).relative_to(center)),
# mksun(translate=flat.rotate(5 * pi / 5).relative_to(center)),
# mksun(translate=flat.rotate(6 * pi / 5).relative_to(center)),
# mksun(translate=flat.rotate(7 * pi / 5).relative_to(center)),
# mksun(translate=flat.rotate(8 * pi / 5).relative_to(center)),
# mksun(translate=flat.rotate(9 * pi / 5).relative_to(center)),

FOOTER = """\
</svg>
"""


def render() -> str:
    return "\n".join(
        [
            canvas.render(),
            *[x.render(canvas.height) for x in img],
            FOOTER,
        ]
    )


# TODO TEXTPATH


if __name__ == "__main__":
    print(render())
