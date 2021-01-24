import time
from gpiozero import MCP3004

while True:
    pot1 = MCP3004(0)
    print("pot1: "+ str(pot1.value))
    pot2 = MCP3004(1)
    print("pot2: "+ str(pot2.value))
    time.sleep(1)