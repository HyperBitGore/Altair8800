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
    memory = [0] * 256

    def nop (self):
        print('NOP')
        self.pc += 1

    # buttons/switches
    instructions = {
        '\x00': 'nop',
        # single register instructions

    }
    instruction_functions = {
        'nop': nop,
        # single register instructions
        
    }


    def runProgram (self, binary):

        return 0

    def processInput (self, string):
        print(string)
        print ('Processing input: ' + string)
        print (string == 'flip0')
        if (string == 'flip0'):
            print('Flip0')
            print('Flip 0 Processed')
        
