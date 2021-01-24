#Bestandsnaam: erres.py
#Auteur: Murk Dalstra
#Versie:0.0
#Datum: 02-05-2020
#
#Omschrijving
#Dit python script verzorgt het inlezen van de knoppen van de erres 
#radio en het omzetten naar commando's voor Volumio.
#De volgende knoppen bevinden zich op de radio
#
#1. Aan - uit schakelaar gecombineerd met de volume regeling
#   De aan/uit schakelaar is verbonden met pin 14
#   Het Volumio commando dat gekoppeld is aan de aan/uit schakelaar is
#   'STOP' en 'VOLUME = 0%'
#   Het volume wordt ingelezen op pin XX
#
#2. Bandkeuze schakelaar
#   Deze schakelaar kent 3 standen deze is verbonden met pin 17, 27 en 22
#
#3. Toonhoogte schakelaar
#   Deze schakelaar kent 2 standen deze is verbonden met pin 12 en 16
#
#4. Volume knop
#   Deze knop is een potmeter en is verbonden met pin 13 en 26
#
#5. Afstemmings knop
#   Deze knop is een potmeter en is verbonden met pin 5 en 6 
#

import RPi.GPIO as GPIO
import time
import mpd
import math
import subprocess
from socketIO_client import SocketIO, LoggingNamespace

# Configure the Pi to use the BCM (Broadcom) pin names, rather than the pin pos$
GPIO.setmode(GPIO.BOARD)

global status, connected, apiHost, apiPort, station

apiHost = 'localhost'
apiPort = '3000'
connected = False
status = 'pause'

while connected == False:
    connected = True
    try:
        socketIO = SocketIO(apiHost, apiPort)
    except Exception as e:
        connected = False
    if connected == False:
        print "Couldn't connect. Retrying"
        time.sleep(5)
print("Connected")

# empty the capacitor ready to start filling it up
def discharge(a_pin, b_pin):
    GPIO.setup(a_pin, GPIO.IN)
    GPIO.setup(b_pin, GPIO.OUT)
    GPIO.output(b_pin, False)
    time.sleep(0.01)
    
# return the time taken (uS) for the voltage on the capacitor to count as HIGH
# than means around 1.65V
def charge_time(a_pin, b_pin):
    GPIO.setup(b_pin, GPIO.IN)
    GPIO.setup(a_pin, GPIO.OUT)
    GPIO.output(a_pin, True)
    t1 = time.time()
    while not GPIO.input(b_pin):
        pass
    t2 = time.time()
    return (t2 - t1) * 1000000

# Take an analog reading as the time taken to charge after first discharging th$
def analog_read(a_pin, b_pin):
    discharge(a_pin, b_pin)
    t = charge_time(a_pin, b_pin)
    discharge(a_pin, b_pin)
    return t
    
# To reduce errors, do it n times and take the average.
def read_resistance(a_pin, b_pin):
    n = 20
    total = 0
    for i in range(1, n):
        total = total + analog_read(a_pin, b_pin)
    t = total / float(n)
    T = t * 0.632 * 3.3
    r = (T / C) - R1
    return r

# catch button changes
def button_pressed(channel):
    if channel == 8:
        if GPIO.input(channel) == True:
	        print 'Radio aanzetten'
	        socketIO.emit('play')
        else:
            print 'Radio uitzetten'
            socketIO.emit('pause')
    elif channel == 11:
        if GPIO.input(channel) == True:
	        print 'NPO Radio1'
	        #socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/radio1-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
    elif channel == 13:
        if GPIO.input(channel) == True:
	        print 'NPO Radio2'
	        #socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/radio2-bb-mp3','title': 'NPO Radio2','service': 'webradio'})
    elif channel == 15:
        if GPIO.input(channel) == True:
            print 'NPO 3FM'
            #socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/3fm-bb-mp3','title': 'NPO 3FM','service': 'webradio'})
    elif channel == 32:
        if GPIO.input(channel) == True:
            print 'Radio'
    elif channel == 36:
        if GPIO.input(channel) == True:
            print 'Spotify'
    else:
	    print "unknown button", channel

def setup_channel(channel):
    try: 
	    print "register %d" %channel
	    GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	    GPIO.add_event_detect(channel, GPIO.RISING, callback = button_pressed, bouncetime = 500)
	    print 'success'
    except (ValueError, RuntimeError) as e:
	    print 'ERROR:', e

for x in [8, 11, 13, 15, 32, 36]:
    setup_channel(x)

# VASTLEGGEN KNOPPEN EN SCHAKELAARS
# global onOffPin, onOffSwitchState, prevOnOffSwitchState
# global switch1_1Pin, switch1_1State, prevswitch1_1State
# global switch1_2Pin, switch1_2State, prevswitch1_2State
# global switch2_1Pin, switch2_1State, prevswitch2_1State
# global switch2_2Pin, switch2_2State, prevswitch2_2State
# global switch2_3Pin, switch2_3State, prevswitch2_3State

# onOffPin = 8
# onOffSwitchState = False
# prevOnOffSwitchState = False
# GPIO.setup(onOffPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# #, pull_up_down=GPIO.PUD_UP
# switch1_1Pin = 32
# switch1_1State = False
# prevswitch1_1State = False
# GPIO.setup(switch1_1Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# switch1_2Pin = 36
# switch1_2State = False
# prevswitch1_2State = False
# GPIO.setup(switch1_2Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# switch2_1Pin = 11
# switch2_1State = False
# prevswitch2_1State = False
# GPIO.setup(switch2_1Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# switch2_2Pin = 13
# switch2_2State = False
# prevswitch2_2State = False
# GPIO.setup(switch2_2Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# switch2_3Pin = 15
# switch2_3State = False
# prevswitch2_3State = False
# GPIO.setup(switch2_3Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Condensator en weerstand waarde voor berekening potmeter weerstand tbv volume en afstemming
C = 0.33 # uF
R1 = 1000 # Ohms

# Pin a charges the capacitor through a fixed 1k resistor and the thermistor in$
# pin b discharges the capacitor through a fixed 1k resistor 
volume_a_pin = 33
volume_b_pin = 37
tune_a_pin = 31
tune_b_pin = 29

def on_push_state(*args):
        #print('state', args)
        status = args[0]['status'].encode('ascii', 'ignore')
        artist = args[0]['artist'].encode('ascii', 'ignore')
        print("Player status: " + status)
        print("Radiostation: " + artist)

socketIO.on('pushState', on_push_state)

# get initial state
socketIO.emit('getState', '', on_push_state)

station = ''

try:
    while True:

        #IN- EN UITSCHAKELEN RADIO
        # onOffSwitchState = GPIO.input(onOffPin)
        # if onOffSwitchState == True and prevOnOffSwitchState == False:
        #     print("De radio uitzetten")
        # if onOffSwitchState == False and prevOnOffSwitchState == True:
        #     print("De radio aanzetten")
        # switch1_1State = GPIO.input(switch1_1Pin)
        # if switch1_1State == True and prevswitch1_1State == False:
        #     print("Schakelaar 1 pos 1 UIT")
        # if switch1_1State == False and prevswitch1_1State == True:
        #     print("Schakelaar 1 pos 1 AAN")
        # switch1_2State = GPIO.input(switch1_2Pin)
        # if switch1_2State == True and prevswitch1_2State == False:
        #     print("Schakelaar 1 pos 2 UIT")
        # if switch1_2State == False and prevswitch1_2State == True:
        #     print("Schakelaar 1 pos 2 AAN")
        # switch2_1State = GPIO.input(switch2_1Pin)
        # if switch2_1State == True and prevswitch2_1State == False:
        #     print("Schakelaar 2 pos 1 UIT")
        # if switch2_1State == False and prevswitch2_1State == True:
        #     print("Schakelaar 2 pos 1 AAN")
        # switch2_2State = GPIO.input(switch2_2Pin)
        # if switch2_2State == True and prevswitch2_2State == False:
        #     print("Schakelaar 2 pos 2 UIT")
        # if switch2_2State == False and prevswitch2_2State == True:
        #     print("Schakelaar 2 pos 2 AAN")
        # switch2_3State = GPIO.input(switch2_3Pin)
        # if switch2_3State == True and prevswitch2_3State == False:
        #     print("Schakelaar 2 pos 3 UIT")
        # if switch2_3State == False and prevswitch2_3State == True:
        #     print("Schakelaar 2 pos 3 AAN")
            
        # prevOnOffSwitchState = onOffSwitchState
        # prevswitch1_1State = switch1_1State
        # prevswitch1_2State = switch1_2State
        # prevswitch2_1State = switch2_1State
        # prevswitch2_2State = switch2_2State
        # prevswitch2_3State = switch2_3State

        #AFSTEMMEN RADIO
        print "ik ben hier"
        tuneDial = round(100 * ((read_resistance(tune_a_pin, tune_b_pin) + 160) / 8000.0))
        print("Afstemming: " + str(tuneDial))
        if tuneDial > -10 and tuneDial < 17.5:
            if station <> 'NPO Radio1':
                socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/radio1-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
                print("Afstemmen op: NPO Radio1")
                station = 'NPO Radio1'
        if tuneDial > 20.0 and tuneDial < 25.0:
            socketIO.emit('pause')
        if tuneDial > 27.5 and tuneDial < 45.0:
            if station <> 'NPO Radio2':
                socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/radio2-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
                print("Afstemmen op: NPO Radio2")
                station = 'NPO Radio2'
        if tuneDial > 47.5 and tuneDial < 52.5:
            socketIO.emit('pause')
        if tuneDial > 55.0 and tuneDial < 72.5:
            if station <> 'NPO 3FM':    
                socketIO.emit('replaceAndPlay', {'uri': 'http://icecast.omroep.nl/3fm-bb-mp3','title': 'NPO Radio1','service': 'webradio'})
                print("Afstemmen op: NPO 3FM")
                station = 'NPO 3FM'
        if tuneDial > 75.0 and tuneDial < 80:
            socketIO.emit('pause')
        if tuneDial > 85.0 and tuneDial < 100:
            if station <> 'Omrop Fryslan':    
                socketIO.emit('replaceAndPlay', {'uri': 'https://d3pvma9xb2775h.cloudfront.net/icecast/omropfryslan/radio.mp3','title': 'Omrop Fryslan','service': 'webradio'})
                print("Afstemmen op: Omrop Fryslan")
                station = 'Omrop Fryslan'
        
        #socketIO.wait()
        
        #Lees volumeknop
        volumeDial = int(round(read_resistance(volume_a_pin, volume_b_pin)))
        volumioVolume = round(2.5*((1100 - (volumeDial + 200))/50))
        #print("Volume knop: " + str(volumeDial))
        print("Volume nivo: " + str(volumioVolume))
        socketIO.emit('volume', volumioVolume)
        
        #if volumeDial > 60:
        #    client.setvol(0)
        #    client.stop()
        #if volumeDial < 58 and volumeDial > 10:
        #    client.setvol(58-volumeDial)
        #    client.play()
    
        socketIO.wait(1)
        time.sleep(1.0)
except Exception as e:
    print(e)
finally:  
    print("Cleaning up")
    GPIO.cleanup()
 
