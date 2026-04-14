#!/usr/bin/python3

# todo add switches

import json
import sys

from time import sleep

args = {arg.lower() for arg in sys.argv[1:]}
raspberry_pi = 'pi' in args or '--pi' in args
local = 'local' in args or '--local' in args

if raspberry_pi:
    import RPi.GPIO as GPIO
    from gpiozero import LED
else:
    GPIO = None
    LED = None
import socket
from altair_vm import Altair
from altair_device import Device

HOST = '199.17.161.139'	# the listening IP
LOCAL = '127.0.0.1'
PORT = 3461	            # the listening port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print ('Socket created')

# Bind socket to local host and port
try:
    if local:
        print(f"Binding to local address {LOCAL}:{PORT}")
        s.bind((LOCAL, PORT))
    else:
        print(f"Binding to remote address {HOST}:{PORT}")
        s.bind((HOST, PORT))
except socket.error as msg:
    print ('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

print ('Socket bind complete')

# Start listening on socket, the size of queue is 10
s.listen(10)
print ('Socket now listening')

conn, addr = s.accept()
print ('Connected with ' + addr[0] + ':' + str(addr[1]))	
if raspberry_pi:
    GPIO.cleanup()
altr = Altair()
output_device = Device([4, 17])
output_device.test_leds()
altr.bindDevice(16, output_device)

while True:
    data = conn.recv(1024)
    if not data: 
        sys.exit()
    decoded = json.loads(data.decode('utf-8'))
    print(f"Received data: {decoded}")
    altr.processInput(decoded)
    print ('Received: ' + str(decoded))

