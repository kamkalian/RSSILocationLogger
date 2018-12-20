#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  1 12:09:14 2018

@author: akurm
"""


# main.py
import time

# import ubinascii
from wlan import Wlan
from display import Display
from gps import Gps


gc.collect()


def main():
	
	# Bootsplash anzeigen
	# und 1sek warten. Wichtig: in dieser Zeit hat man die Möglichkeit über serial ein neues Programm hochzuladen
	# Beim ESP32 ist das nicht mehr wichtig, da dieser zwei serial Schnittstellen hat.
	display = Display()
	display.println("RSSI")
	display.println("Location")
	display.println("Logger")
	display.println("")
	display.print_dot()
	time.sleep(1)
	
	# Systeme konfigurieren
	try:
		# display.println("===CONF START==")
		# display.println("scan wlan")
		# Wlan Objekt erstellen, dass selbständig einen scan macht und das stärkste Freifunk zurück gibt.
		display.print_dot()
		wlan = Wlan("Freifunk")
		display.println(wlan.connect())

		# display.println("connect to:")
		# display.println(ubinascii.hexlify(wlan.ff_list[0][1])+str(wlan.ff_list[0][3]))
		while not wlan.isconnected():
			display.print_dot()
			time.sleep(0.5)
		
		gps = Gps()
		
		s = 0.1

		# display.println("init uart 9600")
		display.print_dot()
		uart = Uart(2, 9600)
		time.sleep(s)
		
		# display.println("set baud 115200")
		display.print_dot()
		uart.send_command(b'PMTK251,115200')
		time.sleep(s)
		
		# display.println("init UART 115200")
		display.print_dot()
		uart = Uart(2, 115200)
		time.sleep(s)
		
		# display.println("set 2Hz")
		display.print_dot()
		uart.send_command(b'PMTK220,500')
		time.sleep(s)
		
		# display.println("set RMC, GGA")
		display.print_dot()
		uart.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,00')
		time.sleep(s)
		
		# display.println("===CONF END===")
		
	except Exception as ex:
		display.println("ERR: %s" % repr(ex))
		time.sleep(3)

	# Dauerschleife starten
	while True:
		try:
			
			line = uart.readline()
			# display.println(str(line))
			gps.refresh(line)
			quality = False
			if(int(gps.sats)>7) and (gps.is_fix) and (float(gps.hdop)<2):
				quality = True
			
			
			if not(wlan.isconnected()):
				display.println("")
				display.println("lost wlan :(")
				display.println("try to reconnect...")
				wlan.reconnect()
			# else:
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
