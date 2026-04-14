from os import name
import threading


class Altair:
    a = 0
    b = 0
    c = 0
    d = 0
    e = 0
    h = 0
    l = 0
    sp = 0
    pc = 0
    stats = 0 # first bit is carry flag, second bit is aux carry flag, third bit is sign flag, fourth bit is zero flag, fifth bit is parity flag
    # creates array with 256 zeros
    memory = [0] * 65536
    interrupt = False
    devices = {}
    execution_thread = None
    execution_thread_lock = threading.Lock()
    execution_thread_stop_event = threading.Event()
    execution_thread_interrupt_event = threading.Event()

    # command instructions
    def input (self):
        print('IN')
        self.pc += 1
        # get the device no. from the next byte in memory
        device_no = self.memory[self.pc]
        if (device_no in self.devices):
            value = self.devices[device_no].read()
            self.a = value & 0xFF
        else:
            print(f"Device {device_no} not found")
        self.pc += 1
    def output (self):
        print('OUT')
        self.pc += 1
        # get the device no. from the next byte in memory
        device_no = self.memory[self.pc]
        self.pc += 1
        value = self.a
        if (device_no in self.devices):
            self.devices[device_no].write(value)
        else:
            print(f"Device {device_no} not found")

    # interrupt instructions

    def ei (self):
        self.interrupt = True
        self.pc += 1
    def di(self):
        self.interrupt = False
        self.pc += 1
    def hlt (self):
        print('HLT')
        self.pc += 1

    
    
    # carry bit instructions
        # complement carry
    def cmc (self):
        self.stats ^= 0b1
        self.pc += 1
        # set carry
    def stc (self):
        self.stats |= 0b1
        self.pc += 1
    # no operation
    def nop (self):
        print('NOP')
        self.pc += 1

    # single register instructions
    def inr_b (self):
        print('INR B')
        self.b += 1
        if self.b > 0xFF:
            self.b = 0
        self.pc += 1
    def dcr_b (self):
        print('DCR B')
        self.b -= 1
        if self.b < 0:
            self.b = 0xFF
        self.pc += 1
    def inr_c (self):
        print('INR C')
        self.c += 1
        if self.c > 0xFF:
            self.c = 0
        self.pc += 1
    def dcr_c (self):
        print('DCR C')
        self.c -= 1
        if self.c < 0:
            self.c = 0xFF
        self.pc += 1
    def inr_d (self):
        print('INR D')
        self.d += 1
        if self.d > 0xFF:
            self.d = 0
        self.pc += 1
    def dcr_d (self):
        print('DCR D')
        self.d -= 1
        if self.d < 0:
            self.d = 0xFF
        self.pc += 1
    def inr_e (self):
        print('INR E')
        self.e += 1
        if self.e > 0xFF:
            self.e = 0
        self.pc += 1
    def dcr_e (self):
        print('DCR E')
        self.e -= 1
        if self.e < 0:
            self.e = 0xFF
        self.pc += 1
    def inr_h (self):
        print('INR H')
        self.h += 1
        if self.h > 0xFF:
            self.h = 0
        self.pc += 1
    def dcr_h (self):
        print('DCR H')
        self.h -= 1
        if self.h < 0:
            self.h = 0xFF
        self.pc += 1
    def inr_l (self):
        print('INR L')
        self.l += 1
        if self.l > 0xFF:
            self.l = 0
        self.pc += 1
    def dcr_l (self):
        print('DCR L')
        self.l -= 1
        if self.l < 0:
            self.l = 0xFF
        self.pc += 1
    def inr_a (self):
        print('INR A')
        self.a += 1
        if self.a > 0xFF:
            self.a = 0
        self.pc += 1
    def dcr_a (self):
        print('DCR A')
        self.a -= 1
        if self.a < 0:
            self.a = 0xFF
        self.pc += 1
    def inr_m (self):
        print('INR M')
        address = (self.h << 8) | self.l
        self.memory[address] += 1
        if self.memory[address] > 0xFF:
            self.memory[address] = 0
        self.pc += 1
    def dcr_m (self):
        print('DCR M')
        address = (self.h << 8) | self.l
        self.memory[address] -= 1
        if self.memory[address] < 0:
            self.memory[address] = 0xFF
        self.pc += 1
    def cma (self):
        print('CMA')
        self.a = ~self.a
        self.pc += 1
    def daa (self):
        print('DAA')
        #if the lower 4 bits of A are greater than 9 or if the aux carry flag is set, add 6 to A
        if (self.a & 0x0F > 9 | (self.stats & 0b10) != 0):
            self.a += 6
        #if the upper 4 bits of A are greater than 9 or if the carry flag is set, add 6 to A
        if (self.a >> 4) > 9 | (self.stats & 0b1) != 0:
            self.a += 0x60
        if self.a > 0xFF:
            self.a = 0
        self.pc += 1
    
    # register pair instructions


    # immediate data instructions
    def mvi_b (self):
        print('MVI B')
        self.pc += 1
        self.b = self.memory[self.pc]
        self.pc += 1
    def mvi_c (self):
        print('MVI C')
        self.pc += 1
        self.c = self.memory[self.pc]
        self.pc += 1
    def mvi_d (self):
        print('MVI D')
        self.pc += 1
        self.d = self.memory[self.pc]
        self.pc += 1
    def mvi_e (self):
        print('MVI E')
        self.pc += 1
        self.e = self.memory[self.pc]
        self.pc += 1
    def mvi_h (self):
        print('MVI H')
        self.pc += 1
        self.h = self.memory[self.pc]
        self.pc += 1
    def mvi_l (self):
        print('MVI L')
        self.pc += 1
        self.l = self.memory[self.pc]
        self.pc += 1
    def mvi_a (self):
        print('MVI A')
        self.pc += 1
        self.a = self.memory[self.pc]
        self.pc += 1
    def mvi_m (self):
        print('MVI M')
        self.pc += 1
        address = (self.h << 8) | self.l
        self.memory[address] = self.memory[self.pc]
        self.pc += 1

    # rotate accumulator instructions
    def rrc (self):
        print('RRC')
        self.stats = (self.stats & 0b11111110) | (self.a & 0x01) # set carry flag to the value of the bit that was rotated out
        self.a = ((self.a >> 1) | ((self.a & 0x01) << 7)) & 0xFF
        self.pc += 1
    def rlc (self):
        print('RLC')
        self.stats = (self.stats & 0b11111110) | ((self.a >> 7) & 0x01) # set carry flag to the value of the bit that was rotated out
        self.a = ((self.a << 1) | ((self.a >> 7) & 0x01)) & 0xFF
        self.pc += 1
    def ral (self):
        print('RAL')
        carry = self.stats & 0b1
        self.stats = (self.stats & 0b11111110) | ((self.a >> 7) & 0x01) # set carry flag to the value of the bit that was rotated out
        self.a = ((self.a << 1) | carry) & 0xFF
        self.pc += 1
    def rar (self):
        print('RAR')
        carry = self.stats & 0b1
        self.stats = (self.stats & 0b11111110) | (self.a & 0x01) # set carry flag to the value of the bit that was rotated out
        self.a = ((self.a >> 1) | (carry << 7)) & 0xFF
        self.pc += 1
    
    # data transfer instructions
    def mov (self, dest, src):
        print(f'MOV {dest}, {src}')
        value = getattr(self, src)       
        setattr(self, dest, value)
        self.pc += 1
    def mov_m (self, dest):
        print(f'MOV {dest}, M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        setattr(self, dest, value)
        self.pc += 1
    def mov_m2 (self, src):
        print(f'MOV M, {src}')
        address = (self.h << 8) | self.l
        value = getattr(self, src)
        self.memory[address] = value
        self.pc += 1

    #jumps/calls/returns
    def jmp (self):
        print('JMP')
        self.pc += 1
        low = self.memory[self.pc]
        self.pc += 1
        high = self.memory[self.pc]
        self.pc += 1
        address = (high << 8) | low
        self.pc = address

    def jnc (self):
        print('JNC')
        self.pc += 1
        low = self.memory[self.pc]
        self.pc += 1
        high = self.memory[self.pc]
        self.pc += 1
        address = (high << 8) | low
        if (self.stats & 0b1) == 0:
            self.pc = address

    # buttons/switches
    instructions = {
        # command instructions
        0b11011011: { 'name': 'in',
            'func': input,
            'cycle': 3,
            'byte_count': 2
        },
        0b11010011: { 'name': 'out',
            'func': output,
            'cycle': 3,
            'byte_count': 2
        },
        # interrupt instructions
        0b11111011: { 'name': 'ei',
            'func': ei,
            'cycle': 1,
            'byte_count': 1
        },
        0b11110011: { 'name': 'di',
            'func': di,
            'cycle': 1,
            'byte_count': 1
        },
        0b01110110: { 'name': 'hlt',
            'func': hlt,
            'cycle': 1,
            'byte_count': 1
        },
        # carry bit instructions
        0b00111111: { 'name': 'cmc',
            'func': cmc,
            'cycle': 1,
            'byte_count': 1
        },
        0b00110111: { 'name': 'stc',
            'func': stc,
            'cycle': 1,
            'byte_count': 1
        },
        # nop
        0x00: { 'name': 'nop',
            'func': nop,
            'cycle': 1,
            'byte_count': 1
            
        },
        # single register instructions
        0b00000100: { 'name': 'inr b',
            'func': inr_b,
            'cycle': 3,
            'byte_count': 1
        },
        0b00000101: { 'name': 'dcr b',
            'func': dcr_b,
            'cycle': 3,
            'byte_count': 1
        },
        0b00001100: { 'name': 'inr c',
            'func': inr_c,
            'cycle': 3,
            'byte_count': 1
        },
        0b00001101: { 'name': 'dcr c',
            'func': dcr_c,
            'cycle': 3,
            'byte_count': 1
        },
        0b00010100: { 'name': 'inr d',
            'func': inr_d,
            'cycle': 3,
            'byte_count': 1
        },
        0b00010101: { 'name': 'dcr d',
            'func': dcr_d,
            'cycle': 3,
            'byte_count': 1
        },
        0b00011100: { 'name': 'inr e',
            'func': inr_e,
            'cycle': 3,
            'byte_count': 1
        },
        0b00011101: { 'name': 'dcr e',
            'func': dcr_e,
            'cycle': 3,
            'byte_count': 1
        },
        0b00100100: { 'name': 'inr h',
            'func': inr_h,
            'cycle': 3,
            'byte_count': 1
        },
        0b00100101: { 'name': 'dcr h',
            'func': dcr_h,
            'cycle': 3,
            'byte_count': 1
        },
        0b00101100: { 'name': 'inr l',
            'func': inr_l,
            'cycle': 3,
            'byte_count': 1
        },
        0b00101101: { 'name': 'dcr l',
            'func': dcr_l,
            'cycle': 3,
            'byte_count': 1
        },
        0b00111100: { 'name': 'inr a',
            'func': inr_a,
            'cycle': 3,
            'byte_count': 1
        },
        0b00111101: { 'name': 'dcr a',
            'func': dcr_a,
            'cycle': 3,
            'byte_count': 1
        },
        0b00110100: { 'name': 'inr m',
            'func': inr_m,
            'cycle': 3,
            'byte_count': 1
        },
        0b00110101: { 'name': 'dcr m',
            'func': dcr_m,
            'cycle': 3,
            'byte_count': 1
        },
        0b00101111: { 'name': 'cma',
            'func': cma,
            'cycle': 1,
            'byte_count': 1
                     },
        0b00100111: { 'name': 'daa',
            'func': daa,
            'cycle': 1,
            'byte_count': 1
        },
        # immediate data instructions
        0b00000110: { 'name': 'mvi b',
            'func': mvi_b,
            'cycle': 3,
            'byte_count': 2
        },
        0b00001110: { 'name': 'mvi c',
            'func': mvi_c,
            'cycle': 3,
            'byte_count': 2
        },
        0b00010110: { 'name': 'mvi d',
            'func': mvi_d,
            'cycle': 3,
            'byte_count': 2
        },
        0b00011110: { 'name': 'mvi e',
            'func': mvi_e,
            'cycle': 3,
            'byte_count': 2
        },
        0b00100110: { 'name': 'mvi h',
            'func': mvi_h,
            'cycle': 3,
            'byte_count': 2
        },
        0b00101110: { 'name': 'mvi l',
            'func': mvi_l,
            'cycle': 3,
            'byte_count': 2
        },
        0b00111110: { 'name': 'mvi a',
            'func': mvi_a,
            'cycle': 3,
            'byte_count': 2
        },
        0b00110110: { 'name': 'mvi m',
            'func': mvi_m,
            'cycle': 3,
            'byte_count': 2
        },
        # rotate accumulator instructions
        0b00001111: { 'name': 'rrc',
            'func': rrc,
            'cycle': 1,
            'byte_count': 1
        },
        0b00000111: { 'name': 'rlc',
            'func': rlc,
            'cycle': 1,
            'byte_count': 1
        },
        0b00010111: { 'name': 'ral',
            'func': ral,
            'cycle': 1,
            'byte_count': 1
        },
        0b00011111: { 'name': 'rar',
            'func': rar,
            'cycle': 1,
            'byte_count': 1
        },
        # data transfer intsructions
        0b01000000: { 'name': 'mov b, b',
            'func': lambda self: self.mov('b', 'b'),
            'cycle': 1,
            'byte_count': 1
        },
        0b01000001: { 'name': 'mov b, c',
            'func': lambda self: self.mov('b', 'c'),
            'cycle': 1,
            'byte_count': 1
        },
        0b01000010: { 'name': 'mov b, d',
            'func': lambda self: self.mov('b', 'd'),
            'cycle': 1,
            'byte_count': 1
        },
        0b01000011: { 'name': 'mov b, e',
            'func': lambda self: self.mov('b', 'e'),
            'cycle': 1,
            'byte_count': 1
        },
        0b01000100: { 'name': 'mov b, h',
            'func': lambda self: self.mov('b', 'h'),
            'cycle': 1,
            'byte_count': 1
        },
        0b01000101: { 'name': 'mov b, l',
            'func': lambda self: self.mov('b', 'l'),
            'cycle': 1,
            'byte_count': 1
        },
        0b01000110: { 'name': 'mov b, m',
            'func': lambda self: self.mov_m('b'),
            'cycle': 2,
            'byte_count': 1
        },
        0b01000111: { 'name': 'mov b, a',
            'func': lambda self: self.mov('b', 'a'),
            'cycle': 1,
            'byte_count': 1
        },
        0b01111111: { 'name': 'mov a, a',
            'func': lambda self: self.mov('a', 'a'),
            'cycle': 1,
            'byte_count': 1
        },
        0b01111000: { 'name': 'mov a, b',
            'func': lambda self: self.mov('a', 'b'),
            'cycle': 1,
            'byte_count': 1
        },
        # jumps/calls/returns
        0b11000011: { 'name': 'jmp',
            'func': jmp,
            'cycle': 3,
            'byte_count': 3
        },
        0b11010010: { 'name': 'jnc',
            'func': jnc,
            'cycle': 3,
            'byte_count': 3
        }
    }

    def __init__ (self):
        print('Altair initialized')
        # todo, procedural generation of instructions



    def runProgram (self, binary):
        print('Running program')
        print(f"Binary data: {binary}")
        self.pc = 0
        for i in range(len(binary)):
            self.memory[i] = binary[i]
        
        while self.pc < len(binary):
            if self.execution_thread_stop_event.is_set():
                print("Execution thread stop event set, stopping execution.")
                break
            byte = self.memory[self.pc]
            instruction = self.instructions.get(byte, None)
            if instruction is not None:
                print(f"Executing instruction: {instruction}")
                func = instruction['func']
                func(self)
                if instruction['name'] == 'hlt':
                   print("HLT instruction encountered, stopping execution.") 
                   while self.execution_thread_interrupt_event.is_set() == False:
                       if self.execution_thread_stop_event.is_set():
                           print("Execution thread stop event set during HLT, stopping execution.")
                           break
                       pass
                   self.execution_thread_interrupt_event.clear()
                   print("Resuming execution after interrupt.")
            else:
                print(f"Unknown instruction: {byte}")
                self.pc += 1
        return 0

    def processInput (self, input_data):
        string = input_data['command']
        if (string == 'program'):
            print('Received program command')
            self.execution_thread = threading.Thread(target=self.runProgram, args=(input_data['data'],))
            self.execution_thread.start()
        elif (string == 'device_set'):
            print('Received device_set command')
            device_no = input_data['device_no']
            value = input_data['value']
            if device_no in self.devices:
                self.devices[device_no].write(value)
            else:
                print(f"Device {device_no} not found")
        elif (string == 'interrupt'):
            if self.interrupt == False:
                print('Interrupt received but interrupts are disabled, ignoring')
                return
            print('Received interrupt command')
            self.execution_thread_interrupt_event.set()
        elif (string == 'restart'):
            print('Received restart command')
            self.pc = 0
            if self.execution_thread is not None and self.execution_thread.is_alive():
                print("Waiting for current execution thread to finish...")
                self.execution_thread_stop_event.set()
                self.execution_thread.join()
                self.execution_thread_stop_event.clear()

    def bindDevice (self, device_no, device):
        self.devices[device_no] = device
        print(f"Device {device_no} bound to {device}")
