#!/usr/bin/python3
# from original gpio_buttons.py

from __future__ import print_function, absolute_import
import sys
import datetime
import os
import sqlite3

# additional threading module for timer tick
import RPi.GPIO as GPIO
import time
import threading, subprocess


def LogGPIO(msg):
	with open("/var/log/gpio_buttons.log","a") as file:
		file.write(msg)

class ActButton:
	def __init__(self, bounce=0.08, dbl_time=0.5, long_time=1.5, short_act="", double_act="", long_act=""):
		#self.gpio = gpio_oin
		self.short_act = short_act		# short press act ex) mpc toggle
		self.double_act = double_act	# double press ex) /var/www/vol.sh -mute
		self.long_act = long_act		# long press ex) /var/local/www/commandw/restart.sh poweroff
		self.state = 1 					# initial button state, 0:press, 1:release
		self.last_time = 0				# last rising event time
		self.count = 0					# button press count
		self.bounce = bounce			# bounce time for prevent chattering
		self.dbl_time = dbl_time		# double press check time
		self.long_time = long_time		# long press check time

class NewButton:
	def __init__(self):
		self.buttons = {}
		self.timer_tick()		# start butoon check loop

	def button_event(self,channel):
		curr_time = time.time()
		diff_time = curr_time - self.buttons[channel].last_time

		# debounce
		if diff_time<self.buttons[channel].bounce: return	# too short term
		btn = GPIO.input(channel)
		if self.buttons[channel].state == btn: return		# same button state is chatering

		self.buttons[channel].state = btn
		LogGPIO(str(self.buttons[channel].state)+","+str(diff_time)+"\n")
		self.buttons[channel].last_time = curr_time;		# update last event time

		# button pressed
		if self.buttons[channel].state==0:
			if diff_time>self.buttons[channel].dbl_time:	# out of time for check double press
				self.buttons[channel].count = 1
			else:
				self.buttons[channel].count += 1			# counting button press

	def button_check(self,channel):
		# no event
		if self.buttons[channel].count==0: return 0

		diff_time = time.time() - self.buttons[channel].last_time

		# processing after released only
		if self.buttons[channel].state: # released
			if diff_time>self.buttons[channel].dbl_time:
				if diff_time>self.buttons[channel].long_time:
					ret = 100 # long press
				else:
					ret = self.buttons[channel].count
				self.buttons[channel].count = 0
				return ret
			else: # wait more event
				return 0
		else: # pressed
			if diff_time>self.buttons[channel].long_time: # spent long press time
				self.buttons[channel].count = 0
				return 100
			else:
				return 0

	def timer_tick(self):
		for key,val in self.buttons.items():
			ret = self.button_check(key)		# key is gpio number
			if ret!=0: LogGPIO("timer_tick:"+str(ret)+"\n")

			if ret==100: # long press
				out = subprocess.run(val.long_act,shell=True,capture_output=True,encoding="utf-8")
				LogGPIO("long:"+val.long_act+","+out.stdout+"\n")
			else:
				if ret==1:
					out = subprocess.run(val.short_act,shell=True,capture_output=True,encoding="utf-8")
					LogGPIO("short:"+val.short_act+","+out.stdout+"\n")
				elif ret!=0:
					out = subprocess.run(val.double_act,shell=True,capture_output=True,encoding="utf-8")
					LogGPIO("double:"+val.double_act+","+out.stdout+"\n")

		threading.Timer(0.05,self.timer_tick).start()

	def add_gpio(self, gpio=0, bounce=0.05, dbl_time=0.5, long_time=1.5, short_act="", double_act="", long_act=""):
		if gpio in self.buttons: # gpio used
			LogGPIO("already used gpio:"+str(gpio))
			return

		btn = ActButton(bounce, dbl_time, long_time, short_act, double_act, long_act)
		self.buttons[gpio] = btn

		GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.add_event_detect(gpio,GPIO.BOTH,callback=self.button_event)

	def remove_gpio(self, gpio):
		if not gpio in self.buttons:
			LogGPIO("No used gpio:"+str(gpio))
			return

		GPIO.remove_event_detect(gpio)




#######################################################
#
# MAIN : /var/www/daemon/gpio_buttons.py
# file permission have to set for execute(0755)
#
#######################################################
gpio_btn = NewButton()

# copy from original gpio_nuttons.py
# Use SoC pin numbering
GPIO.setmode(GPIO.BCM)

# Get sleep time arg
if len(sys.argv) > 1:
	sleep_time = int(sys.argv[1])
else:
	sleep_time = 1

# Get the configuration
db = sqlite3.connect('/var/local/www/db/moode-sqlite3.db')
db.row_factory = sqlite3.Row
db.text_factory = str
cursor = db.cursor()

# Get bounce_time
cursor.execute("SELECT value FROM cfg_gpio WHERE param='bounce_time'")
row = cursor.fetchone()
bounce_time = int(row['value'])

# Configure the pins
# modified code for short, long and double press button
cursor.execute("SELECT * FROM cfg_gpio")
for row in cursor:
	if row['enabled'] == '1':
		sw_pin = int(row['pin'])
		sw_cmd = row['command'].split(',')
		sw_cmd = [x.strip() for x in sw_cmd]

		# V10
		if row['pin'] in ('2','3'): # Pins 2,3 have fixed pull-up resistors
			GPIO.setup(int(row['pin']), GPIO.IN)
		else:
			GPIO.setup(int(row['pin']), GPIO.IN, pull_up_down=int(row['pull']))
            
		while len(sw_cmd)<3: sw_cmd.append("")
		LogGPIO("set gpio: "+str(sw_pin)+":"+str(sw_cmd)+"\n")
		gpio_btn.add_gpio(sw_pin,bounce=bounce_time/1000,short_act=sw_cmd[0],double_act=sw_cmd[1],long_act=sw_cmd[2])

try:
	while True:
		time.sleep(sleep_time)
finally:
	GPIO.cleanup()
