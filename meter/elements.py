import math
from dataclasses import dataclass
from math import pi
from typing import Literal, Self

from .coordinate import Point, Polar
from .units import Deg


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
    rotate: Deg | None = None
    anchor: str = "left"

    @classmethod
    def simple(cls, point: Point, text: str, **kwargs) -> Self:
        return cls(text=text, point=point, **kwargs)

    def render(self, canvas_height: float) -> str:
        pt = self.point.to_graphics_point(canvas_height)
        rotate = (
            f'transform="rotate({self.rotate.val} {pt.x()} {pt.y()})"'
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
    rotate: Deg | None = None
    scale: float | None = None

    def render(self, canvas_height: float) -> str:
        transforms = []
        if pt := self.translate:
            pt = pt.to_graphics_point(canvas_height)
            transforms.append(f"translate({pt.x()} {pt.y()})")
        if self.rotate:
            transforms.append(f"rotate({self.rotate.val})")
        if self.scale:
            transforms.append(f"scale({self.scale})")
        transform = f'transform="{" ".join(transforms)}"' if transforms else ""

        return f"""\
<{self.type}
  id="{self.id}"
  {transform} {self.tags or ""} >
  {self.content or ""}
</{self.type}>
        """


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


CLOCKWISE = 1
ANTI_CLOCKWISE = 0


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
