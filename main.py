#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  1 12:09:14 2018

@author: akurm
"""

# main.py
import machine, time, framebuf, network, ubinascii
import ssd1306

gc.collect()


class Symbol:
	# Mit Symbol kann man kleine 20x20 Bitmaps laden
	def __init__(self, file):
		with open(file, 'rb') as f:
			f.readline()
			f.readline()
			f.readline()
			data = bytearray(f.read())
		self.fbuf = framebuf.FrameBuffer(data, 20, 20, framebuf.MONO_HLSB)


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
		if(self.pos>self._width):
			self.oled.scroll(0, -8)
			self.oled.fill_rect(0, self._height-8, self._width, 8, 0)  # clear last line
			self.pos = 0
		self.oled.text('.', self.pos, self._height-8)
		self.pos += 5
		self.oled.show()

	def println(self, msg: str):
		self.oled.scroll(0, -8)
		self.oled.fill_rect(0, self._height-8, self._width, 8, 0)  # clear last line
		self.oled.text(msg, 0, self._height-8)
		self.oled.show()
	
	def print_info(self, gps, quality, wlan):
		self.oled.fill(0)
		#self.oled.text("gprmc:"+str(gps.is_gprmc_ok), 0,0)
		#self.oled.text("fix:"+str(gps.is_fix()), 0,10)
		if(gps.is_gprmc_ok) or (gps.is_gpgga_ok):
			self.oled.blit(self.gps_board_true.fbuf,0, 0)
		else:
			self.oled.blit(self.gps_board_false.fbuf,0, 0)
		if(gps.is_fix):
			self.oled.blit(self.fix_true.fbuf,25, 0)
			time = str(gps.time)
			self.oled.text("time:"+time[:2]+":"+time[2:4]+":"+time[4:6], 0,41)
			self.oled.text("hdop:"+str(gps.hdop), 0,33)
			self.oled.text("lat:"+str(gps.lat), 0,49)
			self.oled.text("lon:"+str(gps.lon), 0,57)
		else:
			self.oled.blit(self.fix_false.fbuf,25, 0)
# =============================================================================
# 			self.oled.text("hdop: -", 0,33)
# 			self.oled.text("time: -", 0,41)
# 			self.oled.text("lat: -", 0,49)
# 			self.oled.text("lon: -", 0,57)
# =============================================================================

		if(quality):
			self.oled.blit(self.quality.fbuf,107, 0)
			
		self.oled.text("sat:"+str(gps.sats), 0,25)
		
		#if(wlan.isconnected()):
			#self.oled.blit(self.ff_true.fbuf,50, 0)
			#self.oled.text("rssi:"+str(wlan.get_rssi()), 64,25)
		#else:
			#self.oled.blit(self.ff_false.fbuf,50, 0)
		
		self.hline(22, 0, 128)
		
		self.oled.show()
		
	def hline(self, y, x, x1):
		for i in range(x,x1):
			self.oled.pixel(i,y,1)
		

class Uart:
	
	def __init__(self,port, baud):
		self.uart = machine.UART(port, baud)
		self.uart.init(baud, bits=8, parity=None, stop=1)

	def next(self):
		ret = self.uart.read(1)#.decode()
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


class Gps():
		
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
		
		if(str(line).startswith("b'$GPRMC")):
			if(len(str(line).split(','))==13):
				self.gprmc = str(line).split(',')
				if(self.gprmc[2]=="A"):
					self.is_fix = True
				self.time = self.gprmc[1]
				self.lat = self.gprmc[3]
				self.lon = self.gprmc[5]
				self.is_gprmc_ok = True
				self.fail_counter = 0
				
		if(str(line).startswith("b'$GPGGA")):
			if(len(str(line).split(','))==15):
				self.gpgga = str(line).split(',')
				self.sats = int(self.gpgga[7])
				self.hdop = self.gpgga[8]
				if(self.hdop==""):
					self.hdop = 0
				self.q = self.gpgga[6]
				self.is_gpgga_ok = True
				self.fail_counter = 0
				
		if(self.fail_counter>10):
			self.is_fix = False
			self.sats = 0
			self.hdop = 0
			self.q = 0
			self.time = 0
			self.lat = 0
			self.lon = 0
			

class Wlan():
	
	def __init__(self, ssid):
		self.ssid = ssid
		self.wlan = network.WLAN(network.STA_IF)
		self.wlan.active(True)
		self.scan()
	
	def scan(self):
		self.ff_list = []
		ff_tmp_list = []
		ap_list = self.wlan.scan()
		
		for ap in ap_list:
			if(ap[0].decode()==self.ssid):
				ff_tmp_list.append(ap)
		#sorted(ff_list, key=lambda x: x[3])
		self.ff_list = sorted(ff_tmp_list, key=lambda x: -x[3])

	def connect(self):
		self.wlan.connect(self.ssid, None, bssid=self.ff_list[0][1])
		
	def reconnect(self):
		self.scan()
		self.connect()
	
	def isconnected(self):
		return self.wlan.isconnected()
	
	def get_rssi(self):
		return self.wlan.status('rssi')
			
def main():
	
	# Bootsplash anzeigen
	# und 1sek warten. Wichtig: in dieser Zeit hat man die Möglichkeit über serial ein neues Programm hochzuladen
	display = Display()
	display.println("RSSI")
	display.println("Location")
	display.println("Logger")
	display.println("")
	display.print_dot()
	time.sleep(1)
	
	# Systeme konfigurieren
	try:
		#display.println("===CONF START==")
		#display.println("scan wlan")
		display.print_dot()
		wlan = Wlan("Freifunk")
		wlan.connect()

		#display.println("connect to:")
		#display.println(ubinascii.hexlify(wlan.ff_list[0][1])+str(wlan.ff_list[0][3]))
		while not wlan.isconnected():
			display.print_dot()
			time.sleep(0.5)
		
		gps = Gps()
		
		s = 0.1

		#display.println("init uart 9600")
		display.print_dot()
		uart = Uart(2, 9600)
		time.sleep(s)
		
		#display.println("set baud 115200")
		display.print_dot()
		uart.send_command(b'PMTK251,115200')
		time.sleep(s)
		
		#display.println("init UART 115200")
		display.print_dot()
		uart = Uart(2, 115200)
		time.sleep(s)
		
		#display.println("set 2Hz")
		display.print_dot()
		uart.send_command(b'PMTK220,500')
		time.sleep(s)
		
		#display.println("set RMC, GGA")
		display.print_dot()
		uart.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,00')
		time.sleep(s)
		
		#display.println("===CONF END===")
		
	except Exception as ex:
		display.println("ERR: %s" % repr(ex))
		time.sleep(3)

	# Dauerschleife starten
	while True:
		try:
			
			line = uart.readline()
			#display.println(str(line))
			gps.refresh(line)
			quality = False
			if(int(gps.sats)>7) and (gps.is_fix) and (float(gps.hdop)<2):
				quality = True
			
			
			if not(wlan.isconnected()):
				display.println("")
				display.println("lost wlan :(")
				display.println("try to reconnect...")
				wlan.reconnect()
			#else:
			display.print_info(gps, quality, wlan)
			time.sleep(0.1)
			
		except Exception as ex:
			display.println("ERR: %s" % repr(ex))
			for e in ex.args:
				display.println("%s" % e)
				time.sleep(0.5)
			time.sleep(3)

		except:
			display.println("ERR!")
			time.sleep(3)
	

if __name__ == "__main__":
	main()
