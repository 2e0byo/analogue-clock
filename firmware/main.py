import time

import pins


def notify():
    for _ in range(2):
        pins.LED_1[0].on()
        pins.LED_2[0].on()
        pins.G.off()

        time.sleep(0.2)

        pins.LED_1[0].off()
        pins.LED_2[0].off()
        pins.G.on()

        time.sleep(0.2)


if pins.GREEN_BTN() == 0 or pins.RED_BTN() == 0:
    import wifi

    wifi.do_broadcast()

    import webrepl

    webrepl.start()
    notify()

else:
    print("do stuff here")
