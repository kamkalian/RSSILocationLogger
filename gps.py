import machine


class Gps:

    def __init__(self):
        self.fail_counter = 0
        self.is_gprmc_ok = False
        self.is_gpgga_ok = False
        self.is_fix = False
        self.sats = 0
        self.hdop = 0
        self.q = 0
        self.time = 0
        self.lat = 0
        self.lon = 0

    def refresh(self, line):
        self.fail_counter += 1
        self.is_gprmc_ok = False
        self.is_gpgga_ok = False

        if str(line).startswith("b'$GPRMC"):
            if (len(str(line).split(',')) == 13):
                self.gprmc = str(line).split(',')
                if (self.gprmc[2] == "A"):
                    self.is_fix = True
                self.time = self.gprmc[1]
                self.lat = self.gprmc[3]
                self.lon = self.gprmc[5]
                self.is_gprmc_ok = True
                self.fail_counter = 0

        if str(line).startswith("b'$GPGGA"):
            if (len(str(line).split(',')) == 15):
                self.gpgga = str(line).split(',')
                self.sats = int(self.gpgga[7])
                self.hdop = self.gpgga[8]
                if (self.hdop == ""):
                    self.hdop = 0
                self.q = self.gpgga[6]
                self.is_gpgga_ok = True
                self.fail_counter = 0

        if self.fail_counter > 10:
            self.is_fix = False
            self.sats = 0
            self.hdop = 0
            self.q = 0
            self.time = 0
            self.lat = 0
            self.lon = 0


class Uart:

    def __init__(self, port, baud):
        self.uart = machine.UART(port, baud)
        self.uart.init(baud, bits=8, parity=None, stop=1)

    def next(self):
        ret = self.uart.read(1)  # .decode()
        return b'\x00' if ret is None else ret

    def readline(self):
        d = self.uart.readline()
        return d

    def send_command(self, command):
        self.uart.write(b'$')
        self.uart.write(command)
        checksum = 0
        for char in command:
            checksum ^= char
        self.uart.write(b'*')
        self.uart.write(bytes('{:02x}'.format(checksum).upper(), "ascii"))
        self.uart.write(b'\r\n')