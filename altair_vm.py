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

    def pcIncrement (self, value):
        self.pc += value
        self.pc &= 0xFFFF

    # command instructions
    def input (self):
        print('IN')
        self.pcIncrement(1)
        # get the device no. from the next byte in memory
        device_no = self.memory[self.pc]
        print(f"Input from device {device_no}")
        if (device_no in self.devices):
            value = self.devices[device_no].read()
            self.a = value & 0xFF
        else:
            print(f"Device {device_no} not found")
        self.pcIncrement(1)
    def output (self):
        print('OUT')
        self.pcIncrement(1)
        # get the device no. from the next byte in memory
        device_no = self.memory[self.pc]
        print(f"Output to device {device_no} with value {self.a}")
        self.pcIncrement(1)
        value = self.a
        if (device_no in self.devices):
            self.devices[device_no].write(value)
        else:
            print(f"Device {device_no} not found")

    # interrupt instructions

    def ei (self):
        self.interrupt = True
        self.pcIncrement(1)
    def di(self):
        self.interrupt = False
        self.pcIncrement(1)
    def hlt (self):
        print('HLT')
        self.pcIncrement(1)

    
    
    # carry bit instructions
        # complement carry
    def cmc (self):
        self.stats ^= 0b1
        self.pcIncrement(1)
        # set carry
    def stc (self):
        self.stats |= 0b1
        self.pcIncrement(1)
    # no operation
    def nop (self):
        print('NOP')
        self.pcIncrement(1)

    # single register instructions
    def inr (self, reg):
        print(f'INR {reg}')
        value = getattr(self, reg)
        value += 1
        if value > 0xFF:
            value = 0
        setattr(self, reg, value)
        self.pcIncrement(1)

    def inr_m (self):
        print('INR M')
        address = (self.h << 8) | self.l
        self.memory[address] += 1
        if self.memory[address] > 0xFF:
            self.memory[address] = 0
        self.pcIncrement(1)
    def dcr (self, reg):
        print(f'DCR {reg}')
        value = getattr(self, reg)
        value -= 1
        if value < 0:
            value = 0xFF
        setattr(self, reg, value)
        self.pcIncrement(1)

    def dcr_m (self):
        print('DCR M')
        address = (self.h << 8) | self.l
        self.memory[address] -= 1
        if self.memory[address] < 0:
            self.memory[address] = 0xFF
        self.pcIncrement(1)
    def cma (self):
        print('CMA')
        self.a = ~self.a
        self.pcIncrement(1)
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
        self.pcIncrement(1)
    
    # register pair instructions

    def push (self, rp):
        print(f'PUSH {rp}')
        if rp == 'bc':
            high = self.b
            low = self.c
        elif rp == 'de':
            high = self.d
            low = self.e
        elif rp == 'hl':
            high = self.h
            low = self.l
        elif rp == 'psw':
            high = self.stats
            low = self.a
        else:
            raise ValueError(f"Invalid register pair {rp}")
        self.memory[self.sp - 2] = low & 0xFF
        self.memory[self.sp - 1] = high & 0xFF
        print(f'PUSH {rp}: high={high}, low={low}')
        print(f'SP after PUSH {rp}: {self.sp - 2}')
        print(f'memory: {self.memory[self.sp - 2:self.sp]}')
        self.sp -= 2
        self.pcIncrement(1)

    def pop (self, rp):
        print(f'POP {rp}')
        if rp == 'bc':
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.c = low
            self.b = high
        elif rp == 'de':
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.e = low
            self.d = high
        elif rp == 'hl':
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.l = low
            self.h = high
        elif rp == 'psw':
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.a = low
            self.stats = high
        else:
            raise ValueError(f"Invalid register pair {rp}")
        print (f'Popped {rp}: high={high}, low={low}')
        self.sp += 2
        print(f'SP after POP {rp}: {self.sp}')
        print(f'memory: {self.memory[self.sp - 2:self.sp]}')
        self.pcIncrement(1)
    def dad (self, rp):
        print(f'DAD {rp}')
        if rp == 'bc':
            value = (self.b << 8) | self.c
        elif rp == 'de':
            value = (self.d << 8) | self.e
        elif rp == 'hl':
            value = (self.h << 8) | self.l
        else:
            raise ValueError(f"Invalid register pair {rp}")
        hl_value = (self.h << 8) | self.l
        result = hl_value + value
        if result > 0xFFFF:
            self.stats |= 0b1 # set carry flag
            result &= 0xFFFF
        else:
            self.stats &= 0b11111110 # clear carry flag
        self.h = (result >> 8) & 0xFF
        self.l = result & 0xFF
        self.pcIncrement(1)
    def inx (self, rp):
        print(f'INX {rp}')
        if rp == 'bc':
            value = (self.b << 8) | self.c
            value = (value + 1) & 0xFFFF
            self.b = (value >> 8) & 0xFF
            self.c = value & 0xFF
        elif rp == 'de':
            value = (self.d << 8) | self.e
            value = (value + 1) & 0xFFFF
            self.d = (value >> 8) & 0xFF
            self.e = value & 0xFF
        elif rp == 'hl':
            value = (self.h << 8) | self.l
            value = (value + 1) & 0xFFFF
            self.h = (value >> 8) & 0xFF
            self.l = value & 0xFF
        else:
            raise ValueError(f"Invalid register pair {rp}")
        self.pcIncrement(1)
    def dcx (self, rp):
        print(f'DCX {rp}')
        if rp == 'bc':
            value = (self.b << 8) | self.c
            value = (value - 1) & 0xFFFF
            self.b = (value >> 8) & 0xFF
            self.c = value & 0xFF
        elif rp == 'de':
            value = (self.d << 8) | self.e
            value = (value - 1) & 0xFFFF
            self.d = (value >> 8) & 0xFF
            self.e = value & 0xFF
        elif rp == 'hl':
            value = (self.h << 8) | self.l
            value = (value - 1) & 0xFFFF
            self.h = (value >> 8) & 0xFF
            self.l = value & 0xFF
        else:
            raise ValueError(f"Invalid register pair {rp}")
        self.pcIncrement(1)
    def xchg (self):
        print('XCHG')
        temp_h = self.h
        temp_l = self.l
        self.h = self.d
        self.l = self.e
        self.d = temp_h
        self.e = temp_l
        self.pcIncrement(1)
    def xthl (self):
        print('XTHL')
        temp_h = self.h
        temp_l = self.l
        self.h = self.memory[self.sp + 1]
        self.l = self.memory[self.sp]
        self.memory[self.sp] = temp_l
        self.memory[self.sp + 1] = temp_h
        self.pcIncrement(1)
    def sphl(self):
        print('SPHL')
        self.sp = (self.h << 8) | self.l
        self.pcIncrement(1)
    
    # immediate data instructions
    def mvi (self, dest):
        print(f'MVI {dest}')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        setattr(self, dest, value)
        print(f"Set {dest} to {value}")
        self.pcIncrement(1)

    def mvi_m (self):
        print('MVI M')
        self.pcIncrement(1)
        address = (self.h << 8) | self.l
        self.memory[address] = self.memory[self.pc]
        self.pcIncrement(1)

    # rotate accumulator instructions
    def rrc (self):
        print('RRC')
        self.stats = (self.stats & 0b11111110) | (self.a & 0x01) # set carry flag to the value of the bit that was rotated out
        self.a = ((self.a >> 1) | ((self.a & 0x01) << 7)) & 0xFF
        self.pcIncrement(1)
    def rlc (self):
        print('RLC')
        self.stats = (self.stats & 0b11111110) | ((self.a >> 7) & 0x01) # set carry flag to the value of the bit that was rotated out
        self.a = ((self.a << 1) | ((self.a >> 7) & 0x01)) & 0xFF
        self.pcIncrement(1)
    def ral (self):
        print('RAL')
        carry = self.stats & 0b1
        self.stats = (self.stats & 0b11111110) | ((self.a >> 7) & 0x01) # set carry flag to the value of the bit that was rotated out
        self.a = ((self.a << 1) | carry) & 0xFF
        self.pcIncrement(1)
    def rar (self):
        print('RAR')
        carry = self.stats & 0b1
        self.stats = (self.stats & 0b11111110) | (self.a & 0x01) # set carry flag to the value of the bit that was rotated out
        self.a = ((self.a >> 1) | (carry << 7)) & 0xFF
        self.pcIncrement(1)
    
    # data transfer instructions
    def mov (self, dest, src):
        print(f'MOV {dest}, {src}')
        value = getattr(self, src)       
        setattr(self, dest, value)
        self.pcIncrement(1)
    def mov_m (self, dest):
        print(f'MOV {dest}, M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        setattr(self, dest, value)
        self.pcIncrement(1)
    def mov_m2 (self, src):
        print(f'MOV M, {src}')
        address = (self.h << 8) | self.l
        value = getattr(self, src)
        self.memory[address] = value
        self.pcIncrement(1)
    def stax_bc (self):
        print('STAX BC')
        address = (self.b << 8) | self.c
        self.memory[address] = self.a
        self.pcIncrement(1)
    def stax_de (self):
        print('STAX DE')
        address = (self.d << 8) | self.e
        self.memory[address] = self.a
        self.pcIncrement(1)
    def ldax_bc (self):
        print('LDAX BC')
        address = (self.b << 8) | self.c
        self.a = self.memory[address]
        self.pcIncrement(1)
    def ldax_de (self):
        print('LDAX DE')
        address = (self.d << 8) | self.e
        self.a = self.memory[address]
        self.pcIncrement(1)
    def add (self, target):
        print(f'ADD {target}')
        value = getattr(self, target)
        result = self.a + value
        if result > 0xFF:
            self.stats |= 0b1 # set carry flag
            result &= 0xFF
        else:
            self.stats &= 0b11111110 # clear carry flag
        self.a = result
        self.pcIncrement(1)
    def add_m (self):
        print('ADD M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        result = self.a + value
        if result > 0xFF:
            self.stats |= 0b1 # set carry flag
            result &= 0xFF
        else:
            self.stats &= 0b11111110 # clear carry flag
        self.a = result
        self.pcIncrement(1)


    #jumps/calls/returns
    def jmp (self):
        print('JMP')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        self.pc = address

    def jnc (self):
        print('JNC')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        if (self.stats & 0b1) == 0:
            self.pc = address

    # buttons/switches
    instructions = {
        # command instructions
        0b11011011: { 'name': 'in',
            'func': input,
            'cycle': 3,
            'byte_count': 2,
            'operands': ['number']
        },
        0b11010011: { 'name': 'out',
            'func': output,
            'cycle': 3,
            'byte_count': 2,
            'operands': ['number']
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
        # register pair instructions
        0b11101011: { 'name': 'xchg',
            'func': xchg,
            'cycle': 1,
            'byte_count': 1
        },
        0b11100011: { 'name': 'xthl',
            'func': xthl,
            'cycle': 5,
            'byte_count': 1
        },
        0b11111001: { 'name': 'sphl',
            'func': sphl,
            'cycle': 1,
            'byte_count': 1
        },
        # immediate data instructions
        0b00110110: { 'name': 'mvi m',
            'func': mvi_m,
            'cycle': 3,
            'byte_count': 2,
            'operands': ['number']
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
        0b00000010: { 'name': 'stax bc', 
            'func': stax_bc,
            'cycle': 2,
            'byte_count': 1
        },
        0b00010010: { 'name': 'stax de',
            'func': stax_de,
            'cycle': 2,
            'byte_count': 1
        },
        0b00001010: { 'name': 'ldax bc',
            'func': ldax_bc,
            'cycle': 2,
            'byte_count': 1
        },
        0b00011010: { 'name': 'ldax de',
            'func': ldax_de,
            'cycle': 2,
            'byte_count': 1
        },
        0b10000110: {
            'name': 'add m',
            'func': add_m,
            'cycle': 2,
            'byte_count': 1

        },
        # jumps/calls/returns
        0b11000011: { 'name': 'jmp',
            'func': jmp,
            'cycle': 3,
            'byte_count': 3,
            'operands': ['address']
        },
        0b11010010: { 'name': 'jnc',
            'func': jnc,
            'cycle': 3,
            'byte_count': 3,
            'operands': ['address']
        },
    }
    # to make sure procedural generation of instructions does not overwrite existing ones
    def addInstruction (self, opcode, name, func, cycle, byte_count):
        for i in self.instructions.keys():
            if i == opcode:
                raise ValueError(f"Instruction with opcode {opcode} already exists.")
        self.instructions[opcode] = {
            'name': name,
            'func': func,
            'cycle': cycle,
            'byte_count': byte_count
        }


    def __init__ (self):
        print('Altair initialized')
        self.sp = len(self.memory) - 1
        # todo, procedural generation of instructions
        # all m register instructions will be manually added since they often have special handling
        register_bytecodes = {
            'b': 0b000,
            'c': 0b001,
            'd': 0b010,
            'e': 0b011,
            'h': 0b100,
            'l': 0b101,
            'm': 0b110,
            'a': 0b111
        }
        register_pairs = {
            'bc': 0b00,
            'de': 0b01,
            'hl': 0b10,
            'psw': 0b11
        }
        # push
        for rp, code in register_pairs.items():
            self.addInstruction(0b11000101 | (code << 4), f'push {rp}', lambda self, rp=rp: self.push(rp), 3, 1)

        # pop
        for rp, code in register_pairs.items():
            self.addInstruction(0b11000001 | (code << 4), f'pop {rp}', lambda self, rp=rp: self.pop(rp), 3, 1)
        # dad
        for rp, code in register_pairs.items():
            if rp == 'psw':
                continue # DAD PSW does not exist
            self.addInstruction(0b00001001 | (code << 4), f'dad {rp}', lambda self, rp=rp: self.dad(rp), 3, 1)
        # inx
        for rp, code in register_pairs.items():
            if rp == 'psw':
                continue # INX PSW does not exist
            self.addInstruction(0b00000011 | (code << 4), f'inx {rp}', lambda self, rp=rp: self.inx(rp), 1, 1)
        # dcx
        for rp, code in register_pairs.items():
            if rp == 'psw':
                continue # DCX PSW does not exist
            self.addInstruction(0b00001011 | (code << 4), f'dcx {rp}', lambda self, rp=rp: self.dcx(rp), 1, 1)

        # inr/dcr
        for reg, code in register_bytecodes.items():
            if (reg == 'm'):
                continue  # INR and DCR for M will be handled manually
            self.addInstruction(0b00000100 | (code << 3), f'inr {reg}', lambda self, reg=reg: self.inr(reg), 3, 1)
            self.addInstruction(0b00000101 | (code << 3), f'dcr {reg}', lambda self, reg=reg: self.dcr(reg), 3, 1)

        # mvi
        for dest, dest_code in register_bytecodes.items():
            opcode = 0b00000110 | (dest_code << 3)
            if (dest == 'm'):
                continue  # MVI for M will be handled manually
            self.addInstruction(opcode, f'mvi {dest}', lambda self, dest=dest: self.mvi(dest), 2, 2)
        # mov
        for dest, dest_code in register_bytecodes.items():
            for src, src_code in register_bytecodes.items():
                if dest == 'm' and src == 'm':
                    continue  # 0b01110110 is HLT, not MOV M,M
                opcode = 0b01000000 | (dest_code << 3) | src_code
                if src == 'm':
                    func = lambda self, dest=dest: self.mov_m(dest)
                elif dest == 'm':
                    func = lambda self, src=src: self.mov_m2(src)
                else:
                    func = lambda self, dest=dest, src=src: self.mov(dest, src)
                self.addInstruction(opcode, f'mov {dest}, {src}', func, 1 if src != 'm' and dest != 'm' else 2, 1)
        # add
        for dest, dest_code in register_bytecodes.items():
            if (dest == 'm'):
                continue  # ADD for M will be handled manually
            opcode = 0b10000000 | (dest_code)
            self.addInstruction(opcode, f'add {dest}', lambda self, dest=dest: self.add(dest), 1, 1)



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
                self.pcIncrement(1)
        return 0

    def processInput (self, input_data):
        string = input_data['command']
        if (string == 'program'):
            print('Received program command')
            self.execution_thread = threading.Thread(target=self.runProgram, args=(input_data['data'],))
            self.execution_thread.start()
        elif (string == 'program_assembly'):
            print('Received program_assembly command')
            hex_code = self.assembleProgram(input_data['data'])
            self.execution_thread = threading.Thread(target=self.runProgram, args=(hex_code,))
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
    
    def assembleProgram (self, assemblyFile):
        split_code = assemblyFile.splitlines()
        print(split_code)
        sections = {}
        bytecode = []
        bytecount = 0
        for line in split_code:
            line = line.strip()
            if len(line) == 0 or line.startswith(';'):
                continue
            if line.endswith(':'):
                sections[line[:-1]] = bytecount
                continue
            skip_parts = False
            for codes in self.instructions.values():
                if line == codes['name']:
                    bytecode.append(list(self.instructions.keys())[list(self.instructions.values()).index(codes)])
                    bytecount += codes['byte_count']
                    skip_parts = True
                    break
            if skip_parts:
                continue
            parts = line.split()
            print(parts)
            for codes in self.instructions.values():
                if parts[0] == codes['name']:
                    bytecode.append(list(self.instructions.keys())[list(self.instructions.values()).index(codes)])
                    # rest of parts are operands, need to convert to numbers and add to bytecode
                    for j in range(1, len(parts)):
                        operand = parts[j].replace(',', '')
                        if operand in sections:
                            bytecode.append(sections[operand] & 0xFF)
                            bytecode.append((sections[operand] >> 8) & 0xFF)
                        else:
                            if operand.endswith('h'):
                                operand = operand[:-1]
                                bytecode.append(int(operand, 16) & 0xFF)
                            else:
                                bytecode.append(int(operand) & 0xFF)
                    bytecount += codes['byte_count']
                    skip_parts = True
                    break
                elif parts[0] in codes['name']:
                    concat_part = parts[0]
                    for i in range(1, len(parts)):
                        concat_part += parts[i].replace(',', '')
                        if concat_part == codes['name'].replace(' ', ''):
                            bytecode.append(list(self.instructions.keys())[list(self.instructions.values()).index(codes)])
                            # rest of parts are operands, need to convert to numbers and add to bytecode
                            for j in range(i+1, len(parts)):
                                operand = parts[j].replace(',', '')
                                if operand in sections:
                                    bytecode.append(sections[operand] & 0xFF)
                                    bytecode.append((sections[operand] >> 8) & 0xFF)
                                else:
                                    if operand.endswith('h'):
                                        operand = operand[:-1]
                                        if (int(operand, 16) > 0xFF):
                                            raise ValueError(f"Operand {operand} out of range for byte")
                                        bytecode.append(int(operand, 16) & 0xFF)
                                    else:
                                        if (int(operand) > 0xFF):
                                            raise ValueError(f"Operand {operand} out of range for byte")
                                        bytecode.append(int(operand) & 0xFF)
                            bytecount += codes['byte_count']
                            skip_parts = True
                            break
                    if skip_parts:
                        break
        print(f"Generated bytecode: {bytecode}")
        print(f"Bytecode in hex: {[hex(b) for b in bytecode]}")
        return bytecode
        #except Exception as e:
         #   print(f"Error: {e}")
