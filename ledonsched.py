#!/usr/bin/python3
#
# Per community standards, this script is copy-pasted from stackoverflow
#
#
import schedule
import time
import log
import logging
logger = log.setup_custom_logger('ledonsched')
logger.info("Started Led-On-Sched")
from datetime import datetime
import urllib.request
import untangle
import signal
import RPi.GPIO as GPIO
import sys

# TODO: Start at night
# TODO: Day length statz 
#time.sleep(60)
jobs = -1
def clean(*args):
	GPIO.cleanup()
	logger.info("Graceful death /w GPIO cleanup")
	sys.exit(0)

def sunrise():
	sun(False)

def sunset():
	sun(True)

def sun(seth):
	if seth:
		logger.debug("it's sunset")
		GPIO.output(21,GPIO.LOW)
	else:
		logger.debug("it's sunrise")
		GPIO.output(21,GPIO.HIGH)
	global jobs
	jobs = jobs -1
	if jobs == 0: 
		schedule.CancelJob
		checksun()


def checksun():
	now = datetime.now()
	logger.info("Checking for sun")
	with urllib.request.urlopen('http://www.yr.no/stad/Norway/Akershus/B%C3%A6rum/Rykkinn/varsel.xml') as response: #Such PII leak
		xml = untangle.parse(response.read().decode("utf-8"))
		logger.debug("Downloaded yr, {} bytes".format(len(xml)))
		rice = xml.weatherdata.sun['rise'][11:19] # 2017-01-01T00:00:00
		seth = xml.weatherdata.sun['set'][11:19]
		logger.debug("Got sunrise at {} and sunset at {}".format(rice, seth))
		risetime = now.replace(hour=int(rice[:2]),minute=int(rice[3:5]),second=int(rice[6:]),microsecond=0)
		settime = now.replace(hour=int(seth[:2]),minute=int(seth[3:5]),second=int(seth[6:]),microsecond=0)
		schedule.every().day.at(seth[:5]).do(sunset)
		logger.info("Scheduled sunset for " + str(seth[:5]))
		schedule.every().day.at(rice[:5]).do(sunrise)
		logger.info("Scheduled sunrise for " + str(rice[:5]))
		global jobs
		if jobs == -1 and now > settime: # after next sunset, turn on lightz
			sun(True)
			logger.info("It's ufter durk alrudy")
		jobs = 2

def main():
	logger.debug("Registering signals")
	signal.signal(signal.SIGINT, clean)
	signal.signal(signal.SIGTERM, clean)
	logger.debug("GPIO setup")
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(21,GPIO.OUT)
	logger.debug("GPIO test")
	GPIO.output(21,GPIO.LOW)
	time.sleep(1)
	GPIO.output(21,GPIO.HIGH)
	logger.debug("Setup done")
	checksun()
	while 1:
		schedule.run_pending()
		time.sleep(1)
if __name__ == '__main__':
	main()

