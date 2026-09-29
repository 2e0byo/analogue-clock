from secret import SSID, WIFI_PASS


def do_connect():
    import machine
    import network

    wlan = network.WLAN()
    wlan.active(True)
    if not wlan.isconnected():
        print("connecting to network...")
        wlan.connect(SSID, WIFI_PASS)
        while not wlan.isconnected():
            machine.idle()
    print("network config:", wlan.ipconfig("addr4"))


def do_broadcast():
    import network

    ap = network.WLAN(network.WLAN.IF_AP)
    ap.config(ssid="analogue-clock")
    ap.config(max_clients=10)
    ap.active(True)
