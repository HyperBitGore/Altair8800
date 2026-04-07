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

    # buttons/switches
    instructions = {
        0x00: 'nop',
        # single register instructions
        0b00000100: 'inr b',
        0b00000101: 'dcr b',
        0b00001100: 'inr c',
        0b00001101: 'dcr c',
        0b00010100: 'inr d',
        0b00010101: 'dcr d',
        0b00011100: 'inr e',
        0b00011101: 'dcr e',
        0b00100100: 'inr h',
        0b00100101: 'dcr h',
        0b00101100: 'inr l',
        0b00101101: 'dcr l',
        0b00111100: 'inr a',
        0b00111101: 'dcr a',
    }
    instruction_functions = {
        'nop': nop,
        # single register instructions
        'inr b': inr_b,
        'dcr b': dcr_b,
        'inr c': inr_c,
        'dcr c': dcr_c,
        'inr d': inr_d,
        'dcr d': dcr_d,
        'inr e': inr_e,
        'dcr e': dcr_e,
        'inr h': inr_h,
        'dcr h': dcr_h,
        'inr l': inr_l,
        'dcr l': dcr_l,
        'inr a': inr_a,
        'dcr a': dcr_a,

    }


    def runProgram (self, binary):
        print('Running program')
        print(f"Binary data: {binary}")
        for byte in binary:
            instruction = self.instructions.get(byte, None)
            if instruction is not None:
                print(f"Executing instruction: {instruction}")
                func = self.instruction_functions[instruction]
                func(self)
            else:
                print(f"Unknown instruction: {byte}")
        return 0

    def processInput (self, input_data):
        string = input_data['command']
        if (string == 'program'):
            print('Received program command')
            self.runProgram(input_data['data'])
        
