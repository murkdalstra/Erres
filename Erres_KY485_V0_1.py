# Import necessary libraries
import RPi.GPIO as GPIO
import time, datetime
import math
import subprocess
import sys
import spidev
#import mcp3008
from socketIO_client import SocketIO, LoggingNamespace

# Variable declaration
global knop_pinout, knop_status, LED_pin
global playerstatus, connected, apiHost, apiPort, station
global volumeDial, tuneDial, volumioVolume, zenderGroep

# START - INITIALIZATION

spi = spidev.SpiDev()
spi.open(0,0)

# Configure the Pi to use the BCM (Broadcom) pin names, rather than the pin pos$
GPIO.setmode(GPIO.BOARD)

knop_pinout = [8, 32, 36, 13, 11, 15]
knop_status = [1, 1, 1, 1, 1, 1]
old_knop_status = [1, 1, 1, 1, 1, 1]
LED_pin = 10

print("Initialisatie GPIOs")
for x in knop_pinout:
            GPIO.setup(x, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print("Kanaal " + str(x) + ": " +  str(GPIO.input(x)))

# Set pin for LED
#GPIO.setup(LED_pin, GPIO.OUT)

# Configure the socket connection and connect
apiHost = 'localhost'
apiPort = '3000'
connected = False
playerstatus = 'pause'
station = ''

while connected == False:
    connected = True
    try:
        socketIO = SocketIO(apiHost, apiPort)
    except Exception as e:
        connected = False
    if connected == False:
        print("Verbinding mislukt. Nieuwe poging ...")
        time.sleep(5)
print("Verbonden")

# Configure the read out of analog inputs
# Condensator en weerstand waarde voor berekening potmeter weerstand tbv volume en afstemming
C = 0.33 # uF
R1 = 1000 # Ohms

# Pin a charges the capacitor through a fixed 1k resistor and the thermistor in$
# pin b discharges the capacitor through a fixed 1k resistor 
volume_a_pin = 33
volume_b_pin = 37
tune_a_pin = 31
tune_b_pin = 29

# END - INITIALIZATION

# START - SUBPROCESS DEFINITION

# Read spi voor het uitlezen van het volume en de bandkeuze
def read_spi(channel):
    spidata = spi.xfer2([1,(8+channel)<<4,0])
    return ((spidata[1] & 3) << 8) + spidata[2]

# verandering van knop 1 afhandelen
# knop 1: AAN / UIT
def knop_1(newstate):
    if newstate == 0:
        socketIO.emit('play')
        print(str(datetime.datetime.now()) + " Radio aan")    
    else:
        socketIO.emit('stop')
        socketIO.emit('volume', 0)
        print(str(datetime.datetime.now()) + " Radio uit")    

# verandering van knop 2 afhandelen
# knop 2: Radio / Spotify mode
def knop_2(newstate):
    if newstate == 1:
        print(str(datetime.datetime.now()) + " Radio mode")
        socketIO.emit('unmute')
    elif newstate == 2:
        print(str(datetime.datetime.now()) + " Spotify mode")
        socketIO.emit('mute')
    else:
        print(str(datetime.datetime.now()) + " Stand knop 2 onbekend")

# verandering van knop 3 afhandelen
# knop 3 - Zenderkeuze
def knop_3(newstate):
    if newstate == 1:
        print(str(datetime.datetime.now()) + " Zendergroep 1")
        zenderGroep = 1
        #socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/radio1-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
    elif newstate == 2:
        print(str(datetime.datetime.now()) + " Zendergroep 2")
        zenderGroep = 2
        #socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/radio2-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
    elif newstate == 3:
        print(str(datetime.datetime.now()) + " Zendergroep 3")
        zenderGroep = 3
        #socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/3fm-bb-mp3','title': 'NPO Radio1','service': 'webradio'})       
    else:
        print(str(datetime.datetime.now()) + " Stand knop 3 onbekend")
        zenderGroep = 0
    
    return zenderGroep
        
# knop 4 - Volume
def knop_4(radio_aan):
    volumeDial = read_spi(0)
    volume = int(50*volumeDial/1024)
    print("Volume: " + str(volumeDial) + " " + str(volume))
    
    if (volume <= 0 or radio_aan == 1):
        volume = 0
    elif volume > 50:
        volume = 50
        
    socketIO.emit('volume', volume)
           
    return volume

# knop 5 - Afstemming
def knop_5(station, zendergroep):
    # Lees afstemmingsknop
    tuneDial = read_spi(1)
    tuning = int(100 * (tuneDial - 80 ) / 360)
    print("Tuning: " + str(tuneDial) + " " + str(tuning))
    
    if tuning < 0:
        tuning = 0
    elif tuning > 100:
        tuning = 100
                
    # Tuning voor Zendergroep == 1
    if tuning > 0 and tuning < 22 and zenderGroep == 1:
        if station != "NPO Radio1":
            socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/radio1-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
            print("Afstemmen op: NPO Radio1")
            station = 'NPO Radio1'
    if tuning > 28 and tuning < 48 and zenderGroep == 1:
        if station != 'NPO Radio2':
            socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/radio2-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
            print("Afstemmen op: NPO Radio2")
            station = 'NPO Radio2'
    if tuning > 54 and tuning < 74 and zenderGroep == 1:
        if station != 'NPO 3FM':    
            socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/3fm-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
            print("Afstemmen op: NPO 3FM")
            station = 'NPO 3FM'
    if tuning > 80 and tuning < 100 and zenderGroep == 1:
        if station != 'Omrop Fryslan':    
            socketIO.emit('replaceAndPlay', {'uri': 'https://d3pvma9xb2775h.cloudfront.net/icecast/omropfryslan/radio.mp3','title': 'Omrop Fryslan','service': 'webradio'})
            print("Afstemmen op: Omrop Fryslan")
            station = 'Omrop Fryslan'
    return station

def log_exception(msg):
    f = open('Erres_Exception.log','a')
    f.write(str(datetime.datetime.now()) + " " + str(msg) + chr(13))
    f.close()

def on_push_state(*args):
        status = args[0]['status'].encode('ascii', 'ignore')
        mute = args[0]['mute']
         
socketIO.on('pushState', on_push_state)

# get initial state
socketIO.emit('getState', '', on_push_state)

# END - SUBPROCESS DEFINITION

# START - PROGRAM LOOP

try:
    station = 'NPO Radio1'
    socketIO.emit('stop')
    while True:
        # Ieder cyclus de knopstatus inlezen
        # Oude status onthouden om verandering te bepalen
                
        y = 0
        for x in knop_pinout:
            old_knop_status[y] = knop_status[y]
            knop_status[y] = GPIO.input(x)
            #print("Pin " + str(x) + ": " + str(knop_status[y]) + "," + str(old_knop_status[y]))
            y = y + 1
        
        # Knop 1 - AAN / UIT
        if (knop_status[0] != old_knop_status[0]):
            if knop_status[0] == 0:
                knop_1(0)       # AAN
            else:
                knop_1(1)       # UIT
        
        # Knop 2 - Radio / Spotify keuze
        if (not knop_status[1] == old_knop_status[1]) or (not knop_status[2] == old_knop_status[2]):
            if knop_status[1] == 0:
                knop_2(1)
            elif knop_status[2] == 0:
                knop_2(2)
            else:
                knop_2(0)
                
        # Knop 3 - Zenderkeuze
        if knop_status[3] != old_knop_status[3] or knop_status[4] != old_knop_status[4] or knop_status[5] != old_knop_status[5]:
            if knop_status[3] == 0:
                zenderGroep = knop_3(1)
            elif knop_status[4] == 0:
                zenderGroep = knop_3(2)
            elif knop_status[5] == 0:
                zenderGroep = knop_3(3)
            else:
                zenderGroep = knop_3(0)
        
        # Knop 4 - Volume
        volumioVolume = knop_4(knop_status[0])
        #print("Waarde volume = {}".format(volumioVolume))
        #print(str(read_spi(0)) + " " + str(knop_status[0]))
        
        # Knop 5 - Afstemming
        station = knop_5(station, zenderGroep)

        socketIO.wait(1)
        time.sleep(1)
except Exception as e:
    log_exception(e)
    print(e)
except KeyboardInterrupt:
    log_exception("Gestopt door gebruiker")
    raise
finally:  
    print("Cleaning up GPIO")
    GPIO.cleanup()