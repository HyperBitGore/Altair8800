from gpiozero import LED
import RPi.GPIO as GPIO

class Device:
    value = 0

    def __init__ (self, pins):
        self.pins = pins
        self.leds = [LED(pin) for pin in pins]
    
    def read (self):
        return self.value
    
    def write (self, value):
        self.value = value
        for i, led in enumerate(self.leds):
            if (value >> i) & 0x01:
                led.on()
            else:
                led.off()