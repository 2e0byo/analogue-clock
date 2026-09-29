from machine import ADC, Pin

R = Pin(27, Pin.OUT)
G = Pin(26, Pin.OUT)
B = Pin(12, Pin.OUT)
METER = Pin(13, Pin.OUT)
LED_1 = (Pin(22, Pin.OUT), Pin(23, Pin.OUT))
LED_2 = (Pin(33, Pin.OUT), Pin(25, Pin.OUT))

R.on()
G.on()
B.on()

GREEN_BTN = Pin(36, Pin.IN)
RED_BTN = Pin(35, Pin.IN)

LEFT_SWITCH = Pin(39, Pin.IN)
RIGHT_SWITCH = Pin(34, Pin.IN)

KNOB = ADC(32, atten=ADC.ATTN_0DB)
