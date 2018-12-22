import network
import ubinascii

class Wlan():

    def __init__(self, ssid):
        self.ssid = ssid
        self.ff_ap_bssid = ""

        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.scan()

    def scan(self):
        ff_list = []
        ff_tmp_list = []
        ap_list = self.wlan.scan()

        for ap in ap_list:
            if (ap[0].decode() == self.ssid):
                ff_tmp_list.append(ap)
        # sorted(ff_list, key=lambda x: x[3])
        ff_list = sorted(ff_tmp_list, key=lambda x: -x[3])
        # self.ff_ap_bssid = ubinascii.hexlify(ff_list[0][1])
        self.ff_ap_bssid = ff_list[0][1]

    def connect(self):
        self.wlan.connect(ssid=self.ssid, password=None, bssid=self.ff_ap_bssid)

    def reconnect(self):
        self.scan()
        self.connect()

    def isconnected(self):
        return self.wlan.isconnected()

    def get_rssi(self):
        return self.wlan.status('rssi')