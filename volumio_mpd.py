import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(4,GPIO.IN)
buttonPinNext 	= 4
GPIO.setup(buttonPinNext,GPIO.IN)
import mpd
import time

global TEST_MPD_HOST, TEST_MPD_PORT, TEST_MPD_PASSWORD
TEST_MPD_HOST     = "localhost"
TEST_MPD_PORT     = "6600"
TEST_MPD_PASSWORD = "volumio"   # password for Volumio / MPD

# Connect with MPD
client = mpd.MPDClient()
connected = False
while connected == False:
        connected = True
        try:
             client.connect(TEST_MPD_HOST, TEST_MPD_PORT)
        except SocketError as e:
             connected = False
        if connected == False:
                print "Couldn't connect. Retrying"
                time.sleep(5)
print("Connected")

while True:
   if (GPIO.input(buttonPinNext)):   # Play the next song in this play list.
      print "Next track in play list"
      client.next()
      client.ping()
      time.sleep(1)