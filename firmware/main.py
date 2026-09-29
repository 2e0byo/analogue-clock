import time

import pins


def notify():
    for _ in range(2):
        pins.LED_1.duty(1023)
        pins.LED_2.duty(1023)
        pins.RGB.eight_bit_colour(0, 200, 0)

        time.sleep(0.2)

        pins.LED_1.duty(0)
        pins.LED_2.duty(0)
        pins.RGB.eight_bit_colour(0, 0, 0)

        time.sleep(0.2)


if pins.GREEN_BTN() == 0 or pins.RED_BTN() == 0:
    import wifi

    wifi.do_broadcast()

    import webrepl

    webrepl.start()
    notify()

else:
    pm, h, m = False, 0, 0
    while True:
        start = time.ticks_ms()

        if pins.RED_BTN() == 0 and pins.GREEN_BTN() == 0:
            print("turning off light")
            pins.RGB.eight_bit_colour(0, 0, 0)

            while pins.RED_BTN() == 0 or pins.GREEN_BTN() == 0:
                time.sleep_ms(50)

            time.sleep_ms(100)

        elif pins.GREEN_BTN() == 0:
            print("setting time")
            while pins.GREEN_BTN() == 0:
                target = pins.KNOB.pct()
                pins.METER.pwm.duty(round(1023 * target))

            pm, h, m = pins.METER.read_time()
            print("set time", pm, h, m)

            time.sleep_ms(100)

        elif pins.RED_BTN() == 0:
            print("setting hue")
            while pins.RED_BTN() == 0:
                target = pins.KNOB.pct()
                pins.RGB.eight_bit_colour(*pins.hue_to_rgb(round(target * 360)))
            print("set hue")

            time.sleep_ms(100)

        else:  # run clock
            print("tick")
            if m == 59:
                h += 1
                m = 0
            else:
                m += 1
            if h == 12:
                h = 0

            pins.METER.set_time(h, m)

            diff_ms = time.ticks_diff(start, time.ticks_ms())
            remaining_ms = max(0, 60_000 - diff_ms)
            slept = 0
            while slept < remaining_ms:
                time.sleep_ms(5)
                if pins.RED_BTN() == 0 or pins.GREEN_BTN() == 0:
                    time.sleep_ms(50)
                    break
                slept += 5
