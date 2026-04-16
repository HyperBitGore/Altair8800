from asyncio import sleep
import time
import sys

args = {arg.lower() for arg in sys.argv[1:]}
raspberry_pi = 'pi' in args or '--pi' in args

if raspberry_pi:
    import RPi.GPIO as GPIO
    from gpiozero import LED

class Device:
    value = 0

    def __init__ (self, pins):
        self.pins = pins
        if raspberry_pi:
            self.leds = [LED(pin) for pin in pins]
            print(f"Initialized LEDs on pins {pins}")
            print(f"LED objects: {self.leds}")
        else:
            self.leds = pins
    
    def read (self):
        return self.value
    
    def write (self, value):
        self.value = value
        if raspberry_pi:
            for i, led in enumerate(self.leds):
                if (value >> i) & 0x01:
                    led.on()
                else:
                    led.off()
        else:
            print(f"Device write: {value} to pins {self.pins}")
            for i, pin in enumerate(self.leds):
                print(f"Pin {pin} set to {(value >> i) & 0x01}")
    
    def test_leds (self):
        if raspberry_pi:
            for led in self.leds:
                print(f"Testing LED on pin {led.pin}")
                led.on()
            time.sleep(2)
            for led in self.leds:
                led.off()
        else:
            print(f"Testing LEDs on pins {self.pins}")