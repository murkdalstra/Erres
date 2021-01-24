#!/usr/bin/python

# Simple example of reading the MCP3008 analog input channels and printing them all out.

import time
from gpiozero import MCP3004

print('Reading MCP3004 values, press Ctrl-C to quit...')
print('| {0:>5} | {1:>5} | {2:>5} | {3:>5} |'.format(*range(4)))
print('-' * 32)

# Main program loop.
try:
    while True:
# Read all the ADC channel values in a list.
        values = [0]*4
        for i in range(4):
# The read_adc function will get the value of the specified channel (0-7).
            values[i] = MCP3004(channel = i)
            print("Kanaal " + str(i) + ":" + str(MCP3004(channel = i).value))
# Print the ADC values.
            #print('| {0:4.3f} | {1:4.3f} | {2:4.3f} | {3:4.3f} |'.format(*values))
# Pause for 3 seconds.
        time.sleep(3)

except KeyboardInterrupt:
    print('\nProgram terminated by keyboard interrupt: Ctrl-C')
