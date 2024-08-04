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

# Calibration Constants
constant_DO = 0.0145
pH_mid = 1150 # mV
pH_low = 1700 # mV
pH_high = 900 # mV


# Setup socket connection
HOST = "192.168.56.1"  # 137.1 The server's hostname or IP address
PORT = 631  # The port used by the server

# System setup for temp sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Set up input pins
# One-wire interface inputs (use GPIO pin numbering)
GPIO.setup(1,GPIO.IN,pull_up_down=GPIO.PUD_UP) # GPIO pin 1 - Temperature

# ADC inputs
chan_DO = AnalogIn(ads, ADS.P1) # ADC pin 1 - Dissolved Oxygen
chan_pH = AnalogIn(ads, ADS.P2) # ADC pin 2 - pH
chan_ORP = AnalogIn(ads, ADS.P3) # ADC pin 3 - Oxidation Reduction Potential 


# Temperature functions
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    try:
        lines = read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_c, temp_f
    except:
        print("Error in read_temp()")
        return 85, 185


# Establish socket used for TCP connections
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Set timeout for all TCP operations to 3 seconds
s.settimeout(3)

connected = False
messageID = 0

# Print data header
print("{:>5}\t{:>5}\t{:>5}\t{:>5}\t{:>5}".format('Runtime','pH','Temp','DO','ORP_Voltage'))
start_time_ns = time.clock_gettime_ns(time.CLOCK_REALTIME)
try:
    while True:
        # Reset TCP connection every five cycles
        if messageID % 5 == 0:
            # Close connection if already connected
            if connected:
                s.close()
                print("Resetting connection.")
                connected = False
            else:
                print("No connection detected.")
                
            
            # Try to connect over TCP, timeout after 3 seconds
            try:
                print("Attempting to connect...")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((HOST, PORT))
                connected = True
                print("Success.")
            except:
                print("Failed.")

                
        runtime_ns = time.clock_gettime_ns(time.CLOCK_REALTIME) - start_time_ns
        runtime_s = float(runtime_ns) * pow(10, -9)

        pH_voltage_mV = chan_pH.voltage * 1000;
        if (pH_voltage_mV > pH_mid):
            pH = 7.0 - 3.0 / (pH_low - pH_mid) * (pH_voltage_mV - pH_mid)
        else:
            pH = 7.0 - 3.0 / (pH_low - pH_mid) * (pH_voltage_mV - pH_mid);

        temp = read_temp()[1] # Read temperature sensor

        DO = (chan_DO.voltage / constant_DO) * 100 # Calibrated DO formula from AS DO board datasheet

        ORP_V = chan_ORP.voltage - 1.5 # ORP = voltage - 1500mV from AS ORP board datasheet
        ORP = ORP_V * 1000 # Convert from V to mV

        # bound DO ceiling at 100%, and floor at 0%
        if DO > 100:
            DO = 100
        elif DO < 0:
            DO = 0

        # bound pH floor and ceiling from 0->15
        if pH > 15:
            pH = 15
        elif pH < 0:
            pH = 0

        data = [runtime_s, pH, temp, DO, ORP]
        data_str = "{:.2f}s\t{:.2f}\t{:.2f}F\t{:.2f}%\t{:.2f}mV".format(*data)

        print(data_str)

        if connected:
            try:
                s.sendall(str(data).encode())
            except:
                print("Connection lost, data not sent.")
                connected = False
        messageID = messageID + 1
        time.sleep(0.5)

except KeyboardInterrupt:
    print("CTRL+C Pressed, Exiting.")
    pass
