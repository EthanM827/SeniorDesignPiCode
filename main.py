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


#Setup socket connection

HOST = "192.168.56.1"  # 137.1 The server's hostname or IP address
PORT = 631  # The port used by the server



#system setup for temp sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

#Setup GPIO numbering NOT BOARD
GPIO.setup(1,GPIO.IN,pull_up_down=GPIO.PUD_UP)
# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Create single-ended input on channel 0
chan_turb = AnalogIn(ads, ADS.P1) #Turbidity
chan_pH = AnalogIn(ads, ADS.P2)

# Create differential input between channel 0 and 1
#chan = AnalogIn(ads, ADS.P0, ADS.P1)






def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
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










print("{:>5}\t{:>5}\t{:>5}\t{:>5}\t{:>5}".format('voltage_pH','pH','voltage_Turb','Turb','Temp'))
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
messageID = 0
expectedACK = 0
while True:
    expectedACK = messageID
    turb = 1
    ph = (-5.56548 * chan_pH.voltage) +15.509
    print("\t{:>5.2f}\t{:>5.2f}\t{:>5.2f}\t{:>5.2f}\t{:>5.2f}".format(chan_pH.voltage,ph,chan_turb.voltage,turb,read_temp()[1]))
    #s.connect((HOST, PORT))
    #data = [chan_pH.voltage,ph,chan_turb.voltage,turb,read_temp()[1]]
    data = [messageID, ph,chan_turb.voltage,read_temp()[1]]
    encoded_data = str(data).encode()
    s.sendall(encoded_data)

    ack = s.recv(1024)
    count = 0
    timeoutLength = 5 # time in seconds to wait before assuming connection has been lost
    while(ack != encoded_data and count < timeoutLength):
        print("test\n")
        count = count + 1
        time.sleep(1)
        ack = s.recv(1024)

    if (ack != expectedACK):
        print("Connection timed out.")

    messageID = messageID + 1

