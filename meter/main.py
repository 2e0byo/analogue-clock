import math
from collections.abc import Callable
from functools import partial
from itertools import chain
from math import pi

from .coordinate import Point, Polar
from .elements import (
    Arc,
    ArrowHeadConfig,
    Band,
    Canvas,
    Defs,
    Line,
    Raw,
    Text,
    TextPath,
)
from .units import Deg, Mm

type Renderer = Callable[[float], str]


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
    rotate=Deg.from_rad(start.theta / 2) - Deg(7),
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
    return Text(
        text=str(val),
        point=point,
        anchor="middle",
        rotate=Deg.from_rad(angle_from_vertical),
        **kwargs,
    )


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
    *chain.from_iterable(ticks(x) for x in range(12)),
    major_tick(start=start.rotate(12 * step)),
    ## text
    number(12, 0 * step, opacity=0.5),
    number(3, 3 * step),
    number(6, 6 * step),
    number(9, 9 * step),
    number(12, 12 * step),
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
        Mm(93).px(),
    ),
]


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


if __name__ == "__main__":
    print(render())
