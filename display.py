import ssd1306
import framebuf
import machine


class Display:

    def __init__(self, width=128, height=64, scl=22, sda=23):
        self.pos = 0
        self._width = width
        self._height = height
        self.oled = ssd1306.SSD1306_I2C(self._width, self._height, machine.I2C(-1, machine.Pin(scl), machine.Pin(sda)), 0x3c)
        self.clear()
        # Symbole erstellen
        self.fix_true = Symbol('fix_true.pbm')
        self.fix_false = Symbol('fix_false.pbm')
        self.gps_board_true = Symbol('gps_board_true.pbm')
        self.gps_board_false = Symbol('gps_board_false.pbm')
        self.quality = Symbol('quality.pbm')
        self.ff_true = Symbol('ff_true.pbm')
        self.ff_false = Symbol('ff_false.pbm')

    def clear(self):
        self.oled.fill(0)
        self.oled.show()

    def print_dot(self):
        if self.pos > self._width:
            self.oled.scroll(0, -8)
            self.oled.fill_rect(0, self._height -8, self._width, 8, 0)  # clear last line
            self.pos = 0
        self.oled.text('.', self.pos, self._height -8)
        self.pos += 5
        self.oled.show()

    def println(self, msg: str):
        self.oled.scroll(0, -8)
        self.oled.fill_rect(0, self._height -8, self._width, 8, 0)  # clear last line
        self.oled.text(msg, 0, self._height -8)
        self.oled.show()

    def print_info(self, gps, quality, wlan):
        self.oled.fill(0)
        # self.oled.text("gprmc:"+str(gps.is_gprmc_ok), 0,0)
        # self.oled.text("fix:"+str(gps.is_fix()), 0,10)
        if(gps.is_gprmc_ok) or (gps.is_gpgga_ok):
            self.oled.blit(self.gps_board_true.fbuf ,0, 0)
        else:
            self.oled.blit(self.gps_board_false.fbuf ,0, 0)
        if(gps.is_fix):
            self.oled.blit(self.fix_true.fbuf ,25, 0)
            time = str(gps.time)
            self.oled.text("time: " +time[:2 ] +": " +time[2:4 ] +": " +time[4:6], 0 ,41)
            self.oled.text("hdop: " +str(gps.hdop), 0 ,33)
            self.oled.text("lat: " +str(gps.lat), 0 ,49)
            self.oled.text("lon: " +str(gps.lon), 0 ,57)
        else:
            self.oled.blit(self.fix_false.fbuf ,25, 0)
        # =============================================================================
        # 			self.oled.text("hdop: -", 0,33)
        # 			self.oled.text("time: -", 0,41)
        # 			self.oled.text("lat: -", 0,49)
        # 			self.oled.text("lon: -", 0,57)
        # =============================================================================

        if(quality):
            self.oled.blit(self.quality.fbuf, 107, 0)

        self.oled.text("sat: " + str(gps.sats), 0, 25)

        if(wlan.isconnected()):
            self.oled.blit(self.ff_true.fbuf, 50, 0)
            self.oled.text("rssi: " + str(wlan.get_rssi()), 64, 25)
        else:
            self.oled.blit(self.ff_false.fbuf, 50, 0)

        self.hline(22, 0, 128)

        self.oled.show()

    def hline(self, y, x, x1):
        for i in range(x, x1):
            self.oled.pixel(i, y, 1)


class Symbol:
    # Mit Symbol kann man kleine 20x20 Bitmaps laden
    def __init__(self, file):
        with open(file, 'rb') as f:
            f.readline()
            f.readline()
            f.readline()
            data = bytearray(f.read())
        self.fbuf = framebuf.FrameBuffer(data, 20, 20, framebuf.MONO_HLSB)