from math import floor

from machine import ADC, PWM, Pin


class BidirectionalLED:
    def __init__(self, pin_1: int, pin_2: int) -> None:
        self.pin_1 = PWM(Pin(pin_1, Pin.OUT), duty_u16=0)
        self.pin_2 = PWM(Pin(pin_2, Pin.OUT), duty_u16=0)
        self._green = True

    def duty(self, val: int | None = None) -> int | None:
        args = (val,) if val is not None else ()
        if self._green:
            return self.pin_1.duty(*args)
        else:
            return self.pin_2.duty(*args)

    def green(self) -> None:
        if not self._green:
            val = self.pin_2.duty()
            self.pin_2.duty(0)
            self.pin_1.duty(val)
            self._green = True

    def red(self) -> None:
        if self._green:
            val = self.pin_1.duty()
            self.pin_1.duty(0)
            self.pin_2.duty(val)
            self._green = False


class Knob:
    def __init__(self, pin: int) -> None:
        self._adc = ADC(pin, atten=ADC.ATTN_0DB)
        self.max = 995_450
        self.min = 75_000
        self.range = self.max - self.min

    def read(self) -> float:
        return sum(self._adc.read_uv() for _ in range(100)) / 100

    def pct(self) -> float:
        return min(1, max(0, (self.read() - self.min) / self.range))


class Rgb:
    def __init__(self, r: int, g: int, b: int) -> None:
        self.r = PWM(Pin(r, Pin.OUT), duty_u16=65_535)
        self.g = PWM(Pin(g, Pin.OUT), duty_u16=65_535)
        self.b = PWM(Pin(b, Pin.OUT), duty_u16=65_535)

    def eight_bit_colour(self, r: int, g: int, b: int) -> None:
        self.r.duty(1023 - int(r * 1023 / 255))
        self.g.duty(1023 - int(g * 1023 / 255))
        self.b.duty(1023 - int(b * 1023 / 255))


_1_HR_DUTY = 65535 / 12
_1_MIN_DUTY = 65535 / (12 * 60)


class Meter:
    def __init__(self, pin: int) -> None:
        self.pwm = PWM(Pin(pin, Pin.OUT), duty_u16=0)
        self.pm = False
        self.max = 64500
        self.min = 0
        self.range = self.max - self.min
        self._1_HR_DUTY = self.range / 12
        self._1_MIN_DUTY = self.range / (12 * 60)

        self.cal = [
            0,  # 0 / 12
            5_000,  # 1
            10_300,  # 2
            15_600,  # 3
            19_200,  # 4
            27_872,  # 5
            31_400,  # 6
            37_624,  # 7
            41_600,  # 8
            47_500,  # 9
            52_300,  # 10
            58_000,  # 11
            self.max,  # 12
        ]

    def set_time(self, hour: int, min: int):
        if hour == 12:
            hour = 0
        start = self.cal[hour]
        span = self.cal[hour + 1] - start
        duty = start + (min * span / 60)
        self.pwm.duty_u16(round(duty))

    def read_time(self) -> tuple[bool, int, int]:
        duty = self.pwm.duty_u16()
        pct = (duty - self.min) / self.range
        hour = floor(pct * 12)
        start = self.cal[hour]
        min_duty = duty - start
        span = self.cal[hour + 1] - start
        min = round(min_duty * 60 / span)
        if hour == 0:
            hour = 12
        return (self.pm, hour, min)


RGB = Rgb(27, 26, 12)

METER = Meter(13)
LED_1 = BidirectionalLED(22, 23)
LED_2 = BidirectionalLED(33, 25)


GREEN_BTN = Pin(36, Pin.IN)
RED_BTN = Pin(35, Pin.IN)

LEFT_SWITCH = Pin(39, Pin.IN)
RIGHT_SWITCH = Pin(34, Pin.IN)

KNOB = Knob(32)


def hue_to_rgb(h):
    # credit to Mr. GPT
    v = 200  # max brightness; lower = further from white

    sector = h // 60
    f = (h % 60) * 255 // 60

    q = v - (v * f // 255)
    t = v - (v * (255 - f) // 255)

    if sector == 0:
        return v, t, 0
    elif sector == 1:
        return q, v, 0
    elif sector == 2:
        return 0, v, t
    elif sector == 3:
        return 0, q, v
    elif sector == 4:
        return t, 0, v
    else:
        return v, 0, q


def rainbow(delay_ms: int):
    import time

    hue = 0
    for _ in range(100):
        RGB.eight_bit_colour(*hue_to_rgb(hue))
        hue = hue + 1 % 360
        time.sleep_ms(delay_ms)
