#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time

TRIG = 11
ECHO = 12

ObstaclePin = 13

DHTPIN = 15

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    
    GPIO.setup(ObstaclePin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		

def distance():
    GPIO.output(TRIG, 0)
    time.sleep(0.000002)

    GPIO.output(TRIG, 1)
    time.sleep(0.00001)
    GPIO.output(TRIG, 0)

    while GPIO.input(ECHO) == 0:
        a = 0
    time1 = time.time()
    while GPIO.input(ECHO) == 1:
        a = 1
    time2 = time.time()

    during = time2 - time1
    return during * 340 / 2 * 100
    

def read_dht11_dat():
	GPIO.setup(DHTPIN, GPIO.OUT)
	GPIO.output(DHTPIN, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(DHTPIN, GPIO.LOW)
	time.sleep(0.02)
	GPIO.setup(DHTPIN, GPIO.IN, GPIO.PUD_UP)

	unchanged_count = 0
	last = -1
	data = []
	while True:
		current = GPIO.input(DHTPIN)
		data.append(current)
		if last != current:
			unchanged_count = 0
			last = current
		else:
			unchanged_count += 1
			if unchanged_count > MAX_UNCHANGE_COUNT:
				break

	state = STATE_INIT_PULL_DOWN

	lengths = []
	current_length = 0

	for current in data:
		current_length += 1

		if state == STATE_INIT_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_INIT_PULL_UP
			else:
				continue
		if state == STATE_INIT_PULL_UP:
			if current == GPIO.HIGH:
				state = STATE_DATA_FIRST_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_FIRST_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_DATA_PULL_UP
			else:
				continue
		if state == STATE_DATA_PULL_UP:
			if current == GPIO.HIGH:
				current_length = 0
				state = STATE_DATA_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_PULL_DOWN:
			if current == GPIO.LOW:
				lengths.append(current_length)
				state = STATE_DATA_PULL_UP
			else:
				continue
	if len(lengths) != 40:
		#print ("Data not good, skip")
		return False

	shortest_pull_up = min(lengths)
	longest_pull_up = max(lengths)
	halfway = (longest_pull_up + shortest_pull_up) / 2
	bits = []
	the_bytes = []
	byte = 0

	for length in lengths:
		bit = 0
		if length > halfway:
			bit = 1
		bits.append(bit)
	#print ("bits: %s, length: %d" % (bits, len(bits)))
	for i in range(0, len(bits)):
		byte = byte << 1
		if (bits[i]):
			byte = byte | 1
		else:
			byte = byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0
	#print (the_bytes)
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		#print ("Data not good, skip")
		return False

	return the_bytes[0], the_bytes[2]

def loop():
	
	totalBugs = 0
	
	while True:
		result = read_dht11_dat()
		dis = distance()
		bugAtEntrance = 0
		bugAtExit = 0
		time.sleep(0.3)

		while (0 == GPIO.input(ObstaclePin) and dis >= 18):
			dis = distance()
			bugAtEntrance = 1
			result = read_dht11_dat()
			time.sleep(0.1)
			
		while (0 == GPIO.input(ObstaclePin) and dis < 18 and bugAtEntrance == 1 and bugAtExit == 0):
			dis = distance()
			totalBugs = totalBugs + 1
			bugAtEntrance = 0
			print ("Bug Entered , Total Bugs: ", totalBugs)
			
			result = read_dht11_dat()
			if result:
				humidity, temperature = result
				print ("humidity: %s %%,  Temperature: %s C`" % (humidity, temperature))
				print ("\n")
			time.sleep(0.1)
						
		while (1 == GPIO.input(ObstaclePin) and dis < 18):
			dis = distance()
			bugAtExit = 1
			result = read_dht11_dat()
			time.sleep(0.1)
						
		while (0 == GPIO.input(ObstaclePin) and dis < 18 and bugAtEntrance == 0 and bugAtExit == 1):
			dis = distance()
			if(totalBugs != 0):
				totalBugs = totalBugs - 1
			print ("Bug Left, Total Bugs: ", totalBugs)
			
			result = read_dht11_dat()
			if result:
				humidity, temperature = result
				print ("humidity: %s %%,  Temperature: %s C`" % (humidity, temperature))
				print ("\n")
				
			bugAtExit = 0
			time.sleep(0.1)
					
		while(bugAtEntrance == 1 and bugAtExit == 1):
			bugAtExit = 0
			bugAtEntrance = 0
			result = read_dht11_dat()
			time.sleep(0.1)
	
        
def destroy():
    GPIO.cleanup()

if __name__ == "__main__":
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
