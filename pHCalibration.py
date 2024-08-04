import time
import board
import busio
import RPi.GPIO as GPIO
import os
import glob
import socket
import sys
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import socket
from datetime import datetime

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Set up input pins
# One-wire interface inputs (use GPIO pin numbering)
GPIO.setup(1,GPIO.IN,pull_up_down=GPIO.PUD_UP) # GPIO pin 1 - Temperature

# ADC inputs
chan_pH = AnalogIn(ads, ADS.P2) # ADC pin 2 - pH

# Print data header
print("{:>5}\t".format('pH Voltage'))
try:
    while True:


        data = [chan_pH.voltage]
        data_str = "{:.2f}".format(*data)

        print(data_str)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("CTRL+C Pressed, Exiting.")
    pass
