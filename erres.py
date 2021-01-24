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

# Condensator en weerstand waarde voor berekening potmeter weerstand tbv volume en afstemming
C = 0.33 # uF
R1 = 1000 # Ohms

# Pin a charges the capacitor through a fixed 1k resistor and the thermistor in$
# pin b discharges the capacitor through a fixed 1k resistor 
volume_a_pin = 13
volume_b_pin = 26
tune_a_pin = 6
tune_b_pin = 5

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

# Configure the Pi to use the BCM (Broadcom) pin names, rather than the pin pos$
GPIO.setmode(GPIO.BCM)

global onOffPin, onOffSwitchState, prevOnOffSwitchState
global switch1_1Pin, switch1_1State, prevswitch1_1State
global switch1_2Pin, switch1_2State, prevswitch1_2State
global switch2_1Pin, switch2_1State, prevswitch2_1State
global switch2_2Pin, switch2_2State, prevswitch2_2State
global switch2_3Pin, switch2_3State, prevswitch2_3State
global songInfo, songName, songTitle, prevSongName, prevSongTitle

onOffPin = 14
onOffSwitchState = False
prevOnOffSwitchState = False
GPIO.setup(onOffPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

switch1_1Pin = 12
switch1_1State = False
prevswitch1_1State = False
GPIO.setup(switch1_1Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

switch1_2Pin = 16
switch1_2State = False
prevswitch1_2State = False
GPIO.setup(switch1_2Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

switch2_1Pin = 22
switch2_1State = False
prevswitch2_1State = False
GPIO.setup(switch2_1Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

switch2_2Pin = 17
switch2_2State = False
prevswitch2_2State = False
GPIO.setup(switch2_2Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

switch2_3Pin = 27
switch2_3State = False
prevswitch2_3State = False
GPIO.setup(switch2_3Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

prevSongName = ""
prevSongTitle = ""


# Set parameters for communication with Volumio 
global mpdHost, mpdPort, mpdPassword, tuneDial, volumeDial
mpdHost      = "localhost"
mpdPort      = "6600"
mpdPassword  = "volumio"   # password for Volumio / MPD

NPORadio1 = { 'uri': 'http://icecast.omroep.nl/radio1-bb-mp3', 
            'title': 'NPO Radio 1', 
            'service': 'webradio', 
            'name': 'NPO Radio 1', 
            'albumart': '/albumart',
            'samplerate': '',
            'bitdepth': '',
            'channels': 0,
            'trackType': 'webradio' }
NPORadio2 = { 'uri': 'http://icecast.omroep.nl/radio2-bb-mp3', 
            'title': 'NPO Radio 2', 
            'service': 'webradio', 
            'name': 'NPO Radio 2', 
            'albumart': '/albumart',
            'samplerate': '',
            'bitdepth': '',
            'channels': 0,
            'trackType' : 'webradio' }
NPORadio3 = { 'uri': 'http://icecast.omroep.nl/3fm-bb-mp3', 
            'title': 'NPO 3FM', 
            'service': 'webradio', 
            'name': 'NPO 3FM', 
            'albumart': '/albumart',
            'samplerate' : '',
            'bitdepth': '',
            'channels': 0,
            'trackType': 'webradio' }

# Connect with MPD
client = mpd.MPDClient()
client.timeout = 10
client.idletimeout = None
connected = False

#if MPD_PASSWORD:
#    client.password(mpdPassword)

while connected == False:
        connected = True
        try:
             client.connect(mpdHost, mpdPort)
        except Exception as e:
             connected = False
        if connected == False:
                print "Couldn't connect. Retrying"
                time.sleep(5)
print("Connected")

try:
    client.clear()
    while True:
        status = client.status()
        onOffSwitchState = GPIO.input(onOffPin)
        if onOffSwitchState == True and prevOnOffSwitchState == False:
            client.pause()
            client.ping()
            print("De radio is uitgeschakeld")
        if onOffSwitchState == False and prevOnOffSwitchState == True:
            client.play()
            client.ping()
            print("De radio is ingeschakeld")
        switch1_1State = GPIO.input(switch1_1Pin)
        if switch1_1State == True and prevswitch1_1State == False:
            print("Schakelaar 1 pos 1 UIT")
        if switch1_1State == False and prevswitch1_1State == True:
            print("Schakelaar 1 pos 1 AAN")
        switch1_2State = GPIO.input(switch1_2Pin)
        if switch1_2State == True and prevswitch1_2State == False:
            print("Schakelaar 1 pos 2 UIT")
        if switch1_2State == False and prevswitch1_2State == True:
            print("Schakelaar 1 pos 2 AAN")
        switch2_1State = GPIO.input(switch2_1Pin)
        if switch2_1State == True and prevswitch2_1State == False:
            print("Schakelaar 2 pos 1 UIT")
        if switch2_1State == False and prevswitch2_1State == True:
            print("Schakelaar 2 pos 1 AAN")
        switch2_2State = GPIO.input(switch2_2Pin)
        if switch2_2State == True and prevswitch2_2State == False:
            print("Schakelaar 2 pos 2 UIT")
        if switch2_2State == False and prevswitch2_2State == True:
            print("Schakelaar 2 pos 2 AAN")
        switch2_3State = GPIO.input(switch2_3Pin)
        if switch2_3State == True and prevswitch2_3State == False:
            print("Schakelaar 2 pos 3 UIT")
        if switch2_3State == False and prevswitch2_3State == True:
            print("Schakelaar 2 pos 3 AAN")

        prevOnOffSwitchState = onOffSwitchState
        prevswitch1_1State = switch1_1State
        prevswitch1_2State = switch1_2State
        prevswitch2_1State = switch2_1State
        prevswitch2_2State = switch2_2State
        prevswitch2_3State = switch2_3State
        
    #Update station en song informatie
        tuneDial = round(100 * ((read_resistance(tune_a_pin, tune_b_pin) + 160) / 8000.0))
        print(tuneDial)
        #print(client.playlist())
        if tuneDial > -10 and tuneDial < 17.5:
            if len(client.playlist()) == 0:
                client.add('http://icecast.omroep.nl/radio1-bb-mp3')
                client.play()
                print("NPORadio1")
        if tuneDial > 20.0 and tuneDial < 25.0:
            if len(client.playlist()) <> 0:
                client.clear()
                print("Lijst opruimen")
                client.stop()
        if tuneDial > 27.5 and tuneDial < 45.0:
            if len(client.playlist()) == 0:
                client.add('http://icecast.omroep.nl/radio2-bb-mp3')
                client.play()
                print("NPORadio2")
        if tuneDial > 47.5 and tuneDial < 52.5:
            if len(client.playlist()) <> 0:
                client.clear()
                print("Lijst opruimen")
                client.stop()
        if tuneDial > 55.0 and tuneDial < 72.5:
            if len(client.playlist()) == 0:
                client.add('http://icecast.omroep.nl/3fm-bb-mp3')
                client.play()
                print("NPO 3FM")
        if tuneDial > 75.0 and tuneDial < 80:
            if len(client.playlist()) <> 0:
                client.clear()
                print("Lijst opruimen")
                client.stop()
        if tuneDial > 85.0 and tuneDial < 100:
            if len(client.playlist()) == 0:
                client.add('https://d3pvma9xb2775h.cloudfront.net/icecast/omropfryslan/radio.mp3')
                client.play()
                print("Omrop Fryslan")
    #    songName = songInfo["name"]
    #    songTitle = songInfo["title"]
    #    if songName <> prevSongName or songTitle <> prevSongTitle:
    #        print(songName)
    #        print(songTitle)
    #        prevSongName = songName
    #        prevSongTitle = songTitle
        volumeDial = int(round(read_resistance(volume_a_pin, volume_b_pin)))
        print("Volume " + str(volumeDial))
        #if volumeDial > 60:
        #    client.setvol(0)
        #    client.stop()
        #if volumeDial < 58 and volumeDial > 10:
        #    client.setvol(58-volumeDial)
        #    client.play()
    #   client.setvol(int(round(read_resistance(volume_a_pin, volume_b_pin)/10000.0)))
    #   print("Afstemming" + str(read_resistance(tune_a_pin, tune_b_pin)))
        time.sleep(0.5)
except Exception as e:
    print(e)
finally:  
    print("Cleaning up")
    GPIO.cleanup()
 
