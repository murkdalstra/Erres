#!/usr/bin/python
 
import spidev
import time

#Define Variables
delay = 0.5
ldr_channel = 0

#Create SPI
spi = spidev.SpiDev()
spi.open(0, 0)
 
def readadc(adcnum):
    # read SPI data from the MCP3004, 4 channels in total
    if adcnum > 3 or adcnum < 0:
        return -1
    r = spi.xfer2([1, 8 + adcnum << 4, 0])
    data = ((r[1] & 3) << 8) + r[2]
    return data
    
 
while True:
    ldr_value = readadc(ldr_channel)
    print("---------------------------------------")
    print("LDR Value 0: %d" % ldr_value)
    ldr_value = readadc(ldr_channel+1)
    print("---------------------------------------")
    print("LDR Value 1: %d" % ldr_value)
    time.sleep(delay)