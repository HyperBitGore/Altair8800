#!/usr/bin/python3

import json
import sys

#from gpiozero import LED
from time import sleep
#import RPi.GPIO as GPIO
import socket
from altair_vm import Altair

HOST = '127.0.0.1'	# the listening IP
PORT = 3461	            # the listening port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print ('Socket created')

# Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print ('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

print ('Socket bind complete')

# Start listening on socket, the size of queue is 10
s.listen(10)
print ('Socket now listening')

# now keep talking with the client
# wait to accept a connection- blocking call
# it will wait/hang until a connection request is coming
conn, addr = s.accept()
print ('Connected with ' + addr[0] + ':' + str(addr[1]))	
# GPIO.cleanup()
# led = LED(4)
altr = Altair()
while True:
    data = conn.recv(1024)
    if not data: 
        sys.exit()
    decoded = json.loads(data.decode('utf-8'))
    altr.processInput(decoded)
    print ('Received: ' + str(decoded))
    # led.on()
    sleep(1)
    # led.off()
    sleep(1)

