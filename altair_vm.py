from os import name


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
    stats = 0
    # creates array with 256 zeros
    memory = [0] * 65636

    # command instructions
    def input (self):
        print('IN')
        self.pc += 1
        # get the device no. from the next byte in memory
        device_no = self.memory[self.pc]
        self.pc += 1
    def output (self):
        print('OUT')
        self.pc += 1
        # get the device no. from the next byte in memory
        device_no = self.memory[self.pc]
        self.pc += 1

    # single byte instructions
    def nop (self):
        print('NOP')
        self.pc += 1
    def inr_b (self):
        print('INR B')
        self.b += 1
        self.pc += 1
    def dcr_b (self):
        print('DCR B')
        self.b -= 1
        self.pc += 1
    def inr_c (self):
        print('INR C')
        self.c += 1
        self.pc += 1
    def dcr_c (self):
        print('DCR C')
        self.c -= 1
        self.pc += 1
    def inr_d (self):
        print('INR D')
        self.d += 1
        self.pc += 1
    def dcr_d (self):
        print('DCR D')
        self.d -= 1
        self.pc += 1
    def inr_e (self):
        print('INR E')
        self.e += 1
        self.pc += 1
    def dcr_e (self):
        print('DCR E')
        self.e -= 1
        self.pc += 1
    def inr_h (self):
        print('INR H')
        self.h += 1
        self.pc += 1
    def dcr_h (self):
        print('DCR H')
        self.h -= 1
        self.pc += 1
    def inr_l (self):
        print('INR L')
        self.l += 1
        self.pc += 1
    def dcr_l (self):
        print('DCR L')
        self.l -= 1
        self.pc += 1
    def inr_a (self):
        print('INR A')
        self.a += 1
        self.pc += 1
    def dcr_a (self):
        print('DCR A')
        self.a -= 1
        self.pc += 1
    def inr_m (self):
        print('INR M')
        address = (self.h << 8) | self.l
        self.memory[address] += 1
        self.pc += 1
    def dcr_m (self):
        print('DCR M')
        address = (self.h << 8) | self.l
        self.memory[address] -= 1
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



    def runProgram (self, binary):
        print('Running program')
        print(f"Binary data: {binary}")
        self.pc = 0
        for i in range(len(binary)):
            self.memory[i] = binary[i]
        
        while self.pc < len(binary):
            byte = self.memory[self.pc]
            instruction = self.instructions.get(byte, None)
            if instruction is not None:
                print(f"Executing instruction: {instruction}")
                func = instruction['func']
                func(self)
            else:
                print(f"Unknown instruction: {byte}")
                self.pc += 1
        return 0

    def processInput (self, input_data):
        string = input_data['command']
        if (string == 'program'):
            print('Received program command')
            self.runProgram(input_data['data'])
        
