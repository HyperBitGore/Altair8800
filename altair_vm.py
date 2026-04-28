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
    memory = [0] * 256
    interrupt = False
    devices = {}
    execution_thread = None
    execution_thread_lock = threading.Lock()
    execution_thread_stop_event = threading.Event()
    execution_thread_interrupt_event = threading.Event()
    manual_mode = False
    halted = False

    # helper functions
    def pcIncrement (self, value):
        self.pc += value
        self.pc &= 0xFFFF
    def statusBitsUpdate (self, value, affected_bits=['zero', 'sign', 'parity', 'aux_carry', 'carry']):
        if 'zero' in affected_bits:
            if value == 0:
                self.stats |= 0b1000 # set the zero bit
            else:
                self.stats &= 0b11110111 # clear the zero bit
        if 'sign' in affected_bits:
            if value & 0x80 != 0:
                self.stats |= 0b100 # set the sign bit
            else:
                self.stats &= 0b11111011 # clear the sign bit
        if 'parity' in affected_bits:
            if bin(value).count('1') % 2 == 0:
                self.stats |= 0b10000 # set the parity bit
            else:
                self.stats &= 0b11101111 # clear the parity bit
        if 'aux_carry' in affected_bits:
            if (value & 0x0F) == 0:
                self.stats |= 0b10 # set the aux carry bit
            else:
                self.stats &= 0b11111101 # clear the aux carry bit
        if 'carry' in affected_bits:
            if value > 0xFF or value < 0:
                self.stats |= 0b1 # set the carry bit
            else:
                self.stats &= 0b11111110 # clear the carry bit
    # need this to prevent numbers above a byte value being inputted
    def setRegister (self, reg, value):
        if value < 0:
            value = 0xFF
        elif value > 0xFF:
            value = 0
        setattr(self, reg, value)
    # same thing as setRegister but for memory, need to prevent values above a byte value and addresses above 16 bit value
    def setMemory (self, address, value):
        if address < 0 or address > 0xFFFF:
            raise ValueError(f"Invalid memory address {address}")
        if value < 0:
            value = 0xFF
        elif value > 0xFF:
            value = 0
        self.memory[address] = value

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
        return 0
    # set carry
    def stc (self):
        self.stats |= 0b1
        self.pcIncrement(1)
        return 0
    # no operation
    def nop (self):
        print('NOP')
        self.pcIncrement(1)
        return 0

    # single register instructions
    def inr (self, reg):
        print(f'INR {reg}')
        value = getattr(self, reg)
        value += 1
        self.setRegister(reg, value)
        self.pcIncrement(1)
        return value

    def inr_m (self):
        print('INR M')
        address = (self.h << 8) | self.l
        value = self.memory[address] + 1
        self.setMemory(address, value)
        self.pcIncrement(1)
        return value
    def dcr (self, reg):
        print(f'DCR {reg}')
        value = getattr(self, reg)
        value -= 1
        self.setRegister(reg, value)
        self.pcIncrement(1)
        return value

    def dcr_m (self):
        print('DCR M')
        address = (self.h << 8) | self.l
        value = self.memory[address] - 1
        self.setMemory(address, value)
        self.pcIncrement(1)
        return value
    def cma (self):
        print('CMA')
        self.a = ~self.a
        self.pcIncrement(1)
        return self.a
    def daa (self):
        print('DAA')
        #if the lower 4 bits of A are greater than 9 or if the aux carry flag is set, add 6 to A
        value = self.a
        if (self.a & 0x0F > 9 | (self.stats & 0b10) != 0):
            value += 6
        #if the upper 4 bits of A are greater than 9 or if the carry flag is set, add 6 to A
        if (self.a >> 4) > 9 | (self.stats & 0b1) != 0:
            value += 0x60
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value
    
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
        self.setMemory(self.sp - 2, low)
        self.setMemory(self.sp - 1, high)
        print(f'PUSH {rp}: high={high}, low={low}')
        print(f'SP after PUSH {rp}: {self.sp - 2}')
        print(f'memory: {self.memory[self.sp - 2:self.sp]}')
        self.sp -= 2
        self.pcIncrement(1)
        return 0

    def pop (self, rp):
        print(f'POP {rp}')
        if rp == 'bc':
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.setRegister('c', low)
            self.setRegister('b', high)
        elif rp == 'de':
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.setRegister('e', low)
            self.setRegister('d', high)
        elif rp == 'hl':
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.setRegister('l', low)
            self.setRegister('h', high)
        elif rp == 'psw':
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.setRegister('a', low)
            self.setRegister('stats', high)
        else:
            raise ValueError(f"Invalid register pair {rp}")
        print (f'Popped {rp}: high={high}, low={low}')
        self.sp += 2
        print(f'SP after POP {rp}: {self.sp}')
        print(f'memory: {self.memory[self.sp - 2:self.sp]}')
        self.pcIncrement(1)
        return 0
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
        return 0
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
        return 0
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
        return 0
    def xchg (self):
        print('XCHG')
        temp_h = self.h
        temp_l = self.l
        self.h = self.d
        self.l = self.e
        self.d = temp_h
        self.e = temp_l
        self.pcIncrement(1)
        return 0
    def xthl (self):
        print('XTHL')
        temp_h = self.h
        temp_l = self.l
        self.h = self.memory[self.sp + 1]
        self.l = self.memory[self.sp]
        self.memory[self.sp] = temp_l
        self.memory[self.sp + 1] = temp_h
        self.pcIncrement(1)
        return 0
    def sphl(self):
        print('SPHL')
        self.sp = (self.h << 8) | self.l
        self.pcIncrement(1)
        return 0
    
    # immediate data instructions
    def mvi (self, dest):
        print(f'MVI {dest}')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        setattr(self, dest, value)
        print(f"Set {dest} to {value}")
        self.pcIncrement(1)
        return 0
    def mvi_m (self):
        print('MVI M')
        self.pcIncrement(1)
        address = (self.h << 8) | self.l
        self.memory[address] = self.memory[self.pc]
        self.pcIncrement(1)
        return 0
    def lxi (self, rp):
        print(f'LXI {rp}')
        self.pcIncrement(1)
        if rp == 'bc':
            self.setRegister('b', self.memory[self.pc])
            self.setRegister('c', self.memory[self.pc + 1])
        elif rp == 'de':
            self.setRegister('d', self.memory[self.pc])
            self.setRegister('e', self.memory[self.pc + 1])
        elif rp == 'hl':
            self.setRegister('h', self.memory[self.pc])
            self.setRegister('l', self.memory[self.pc + 1])
        elif rp == 'sp':
            self.sp = (self.memory[self.pc + 1] << 8) | self.memory[self.pc]
        self.pcIncrement(2)
        return 0
    def adi (self):
        print('ADI')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        result = self.a + value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def aci (self):
        print('ACI')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        value = value + self.a + (self.stats & 0b1) # add carry flag
        self.setRegister('a', value) # add carry flag
        self.pcIncrement(1)
        return value
    def sui (self):
        print('SUI')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        result = self.a - value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def sbi (self):
        print('SBI')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        result = self.a - value - (self.stats & 0b1) # subtract borrow flag
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def ani (self):
        print('ANI')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        result = value & self.a
        self.setRegister('a', result)
        return result
    def xri (self):
        print('XRI')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        result = value ^ self.a
        self.setRegister('a', result)
        return result
    def ori (self):
        print('ORI')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        result = value | self.a
        self.setRegister('a', result)
        return result
    def cpi (self):
        print('CPI')
        self.pcIncrement(1)
        value = self.memory[self.pc]
        result = self.a - value
        self.pcIncrement(1)
        return result

    # rotate accumulator instructions
    def rrc (self):
        print('RRC')
        value = ((self.a >> 1) | ((self.a & 0x01) << 7)) & 0xFF
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value

    def rlc (self):
        print('RLC')
        self.stats = (self.stats & 0b11111110) | ((self.a >> 7) & 0x01) # set carry flag to the value of the bit that was rotated out
        value = ((self.a << 1) | ((self.a >> 7) & 0x01)) & 0xFF
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value
    def ral (self):
        print('RAL')
        carry = self.stats & 0b1
        self.stats = (self.stats & 0b11111110) | ((self.a >> 7) & 0x01) # set carry flag to the value of the bit that was rotated out
        value = ((self.a << 1) | carry) & 0xFF
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value
    def rar (self):
        print('RAR')
        carry = self.stats & 0b1
        self.stats = (self.stats & 0b11111110) | (self.a & 0x01) # set carry flag to the value of the bit that was rotated out
        value = ((self.a >> 1) | (carry << 7)) & 0xFF
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value
    
    # data transfer instructions
    def mov (self, dest, src):
        print(f'MOV {dest}, {src}')
        value = getattr(self, src)       
        setattr(self, dest, value)
        self.pcIncrement(1)
        return 0
    def mov_m (self, dest):
        print(f'MOV {dest}, M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        setattr(self, dest, value)
        self.pcIncrement(1)
        return 0
    def mov_m2 (self, src):
        print(f'MOV M, {src}')
        address = (self.h << 8) | self.l
        value = getattr(self, src)
        self.setMemory(address, value)
        self.pcIncrement(1)
        return 0
    def stax_bc (self):
        print('STAX BC')
        address = (self.b << 8) | self.c
        self.setMemory(address, self.a)
        self.pcIncrement(1)
        return 0
    def stax_de (self):
        print('STAX DE')
        address = (self.d << 8) | self.e
        self.setMemory(address, self.a)
        self.pcIncrement(1)
        return 0
    def ldax_bc (self):
        print('LDAX BC')
        address = (self.b << 8) | self.c
        self.a = self.memory[address]
        self.pcIncrement(1)
        return 0

    def ldax_de (self):
        print('LDAX DE')
        address = (self.d << 8) | self.e
        self.a = self.memory[address]
        self.pcIncrement(1)
        return 0
    def add (self, target):
        print(f'ADD {target}')
        value = getattr(self, target)
        result = self.a + value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def add_m (self):
        print('ADD M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        result = self.a + value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def adc (self, target):
        print(f'ADC {target}')
        value = getattr(self, target)
        value += self.a
        value += self.stats & 0b1 # add carry flag
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value
    def adc_m (self):
        print('ADC M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        value += self.a
        value += self.stats & 0b1 # add carry flag
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value
    def sub (self, target):
        print(f'SUB {target}')
        value = getattr(self, target)
        result = self.a - value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def sub_m (self):
        print('SUB M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        result = self.a - value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def sbb (self, target):
        print(f'SBB {target}')
        value = getattr(self, target)
        value = self.a - value - (self.stats & 0b1) # subtract carry flag
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value
    def sbb_m (self):
        print('SBB M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        value = self.a - value - (self.stats & 0b1) # subtract carry flag
        self.setRegister('a', value)
        self.pcIncrement(1)
        return value
    def ana (self, target):
        print(f'ANA {target}')
        value = getattr(self, target)
        result = self.a & value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def ana_m (self):
        print('ANA M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        result = self.a & value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def xra (self, target):
        print(f'XRA {target}')
        value = getattr(self, target)
        result = self.a ^ value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def xra_m (self):
        print('XRA M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        result = self.a ^ value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def ora (self, target):
        print(f'ORA {target}')
        value = getattr(self, target)
        result = self.a | value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def ora_m (self):
        print('ORA M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        result = self.a | value
        self.setRegister('a', result)
        self.pcIncrement(1)
        return result
    def cmp (self, target):
        print(f'CMP {target}')
        value = getattr(self, target)
        value = self.a - value
        return value
    def cmp_m (self):
        print('CMP M')
        address = (self.h << 8) | self.l
        value = self.memory[address]
        value = self.a - value
        return value
    def sta (self):
        print('STA')
        self.pcIncrement(1)
        address = (self.memory[self.pc + 1] << 8) | self.memory[self.pc]
        self.setMemory(address, self.a)
        self.pcIncrement(2)
        return 0
    def lda (self):
        print('LDA')
        self.pcIncrement(1)
        address = (self.memory[self.pc + 1] << 8) | self.memory[self.pc]
        self.setRegister('a', self.memory[address])
        self.pcIncrement(2)
        return 0
    def shld (self):
        print('SHLD')
        self.pcIncrement(1)
        address = (self.memory[self.pc + 1] << 8) | self.memory[self.pc]
        self.setMemory(address, self.l)
        self.setMemory(address + 1, self.h)
        self.pcIncrement(2)
        return 0
    def lhld (self):
        print('LHLD')
        self.pcIncrement(1)
        address = (self.memory[self.pc + 1] << 8) | self.memory[self.pc]
        self.setRegister('l', self.memory[address])
        self.setRegister('h', self.memory[address + 1])
        self.pcIncrement(2)
        return 0
    #jumps/calls/returns
    def pchl (self):
        print('PCHL')
        self.pc = (self.h << 8) | self.l
        return 0

    def jmp (self):
        print('JMP')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        self.pc = address
        return 0
    def jc (self):
        print('JC')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        if (self.stats & 0b1) != 0:
            self.pc = address
        return 0
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
        return 0
    def jz (self):
        print('JZ')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        if (self.stats & 0b1000) != 0:
            self.pc = address
        return 0
    def jnz (self):
        print('JNZ')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        if (self.stats & 0b1000) == 0:
            self.pc = address
        return 0
    def jm (self):
        print('JM')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        if (self.stats & 0b100) != 0:
            self.pc = address
        return 0
    def jp (self):
        print('JP')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        if (self.stats & 0b100) == 0:
            self.pc = address
        return 0
    def jpe (self):
        print('JPE')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        if (self.stats & 0b10000) != 0:
            self.pc = address
        return 0
    def jpo (self):
        print('JPO')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        address = (high << 8) | low
        if (self.stats & 0b10000) == 0:
            self.pc = address
        return 0
    # call instructions
    def call (self):
        print('CALL')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        # push return address onto stack
        self.pc = address
        self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
        self.memory[self.sp - 2] = return_address & 0xFF # push low byte
        self.sp -= 2
        return 0
    def cc (self):
        print('CC')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        if (self.stats & 0b1) != 0:
            # push return address onto stack
            self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
            self.memory[self.sp - 2] = return_address & 0xFF # push low byte
            self.sp -= 2
            self.pc = address
        return 0
    def cnc (self):
        print('CNC')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        if (self.stats & 0b1) == 0:
            # push return address onto stack
            self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
            self.memory[self.sp - 2] = return_address & 0xFF # push low byte
            self.sp -= 2
            self.pc = address
        return 0
    def cz (self):
        print('CZ')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        if (self.stats & 0b1000) != 0:
            # push return address onto stack
            self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
            self.memory[self.sp - 2] = return_address & 0xFF # push low byte
            self.sp -= 2
            self.pc = address
        return 0
    def cnz (self):
        print('CNZ')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        if (self.stats & 0b1000) == 0:
            # push return address onto stack
            self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
            self.memory[self.sp - 2] = return_address & 0xFF # push low byte
            self.sp -= 2
            self.pc = address
        return 0
    def cm (self):
        print('CM')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        if (self.stats & 0b100) != 0:
            # push return address onto stack
            self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
            self.memory[self.sp - 2] = return_address & 0xFF # push low byte
            self.sp -= 2
            self.pc = address
        return 0
    def cp (self):
        print('CP')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        if (self.stats & 0b100) == 0:
            # push return address onto stack
            self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
            self.memory[self.sp - 2] = return_address & 0xFF # push low byte
            self.sp -= 2
            self.pc = address
        return 0
    def cpe (self):
        print('CPE')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        if (self.stats & 0b10000) != 0:
            # push return address onto stack
            self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
            self.memory[self.sp - 2] = return_address & 0xFF # push low byte
            self.sp -= 2
            self.pc = address
        return 0
    def cpo (self):
        print('CPO')
        self.pcIncrement(1)
        low = self.memory[self.pc]
        self.pcIncrement(1)
        high = self.memory[self.pc]
        self.pcIncrement(1)
        return_address = self.pc
        address = (high << 8) | low
        if (self.stats & 0b10000) == 0:
            # push return address onto stack
            self.memory[self.sp - 1] = (return_address >> 8) & 0xFF # push high byte
            self.memory[self.sp - 2] = return_address & 0xFF # push low byte
            self.sp -= 2
            self.pc = address
        return 0
    # return instructions
    def ret (self):
        print('RET')
        low = self.memory[self.sp]
        high = self.memory[self.sp + 1]
        self.sp += 2
        address = (high << 8) | low
        self.pc = address
        return 0
    def rc (self):
        print('RC')
        if (self.stats & 0b1) != 0:
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.sp += 2
            address = (high << 8) | low
            self.pc = address
        return 0
    def rnc (self):
        print('RNC')
        if (self.stats & 0b1) == 0:
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.sp += 2
            address = (high << 8) | low
            self.pc = address
        return 0
    def rz (self):
        print('RZ')
        if (self.stats & 0b1000) != 0:
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.sp += 2
            address = (high << 8) | low
            self.pc = address
        return 0
    def rnz (self):
        print('RNZ')
        if (self.stats & 0b1000) == 0:
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.sp += 2
            address = (high << 8) | low
            self.pc = address
        return 0
    def rm (self):
        print('RM')
        if (self.stats & 0b100) != 0:
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.sp += 2
            address = (high << 8) | low
            self.pc = address
        return 0
    def rp (self):
        print('RP')
        if (self.stats & 0b100) == 0:
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.sp += 2
            address = (high << 8) | low
            self.pc = address
        return 0
    def rpe (self):
        print('RPE')
        if (self.stats & 0b10000) != 0:
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.sp += 2
            address = (high << 8) | low
            self.pc = address
        return 0
    def rpo (self):
        print('RPO')
        if (self.stats & 0b10000) == 0:
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            self.sp += 2
            address = (high << 8) | low
            self.pc = address
        return 0
    # buttons/switches
    instructions = {
        # command instructions
        0b11011011: { 'name': 'in',
            'func': input,
            'cycle': 3,
            'byte_count': 2,
            'status_bits_affected': []
        },
        0b11010011: { 'name': 'out',
            'func': output,
            'cycle': 3,
            'byte_count': 2,
            'status_bits_affected': []
        },
        # interrupt instructions
        0b11111011: { 'name': 'ei',
            'func': ei,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11110011: { 'name': 'di',
            'func': di,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b01110110: { 'name': 'hlt',
            'func': hlt,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': []
        },
        # carry bit instructions
        0b00111111: { 'name': 'cmc',
            'func': cmc,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['']
        },
        0b00110111: { 'name': 'stc',
            'func': stc,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['']
        },
        # nop
        0x00: { 'name': 'nop',
            'func': nop,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': []
            
        },
        # single register instructions
        0b00110100: { 'name': 'inr m',
            'func': inr_m,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': ['zero', 'sign', 'parity', 'aux_carry']
        },
        0b00110101: { 'name': 'dcr m',
            'func': dcr_m,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': ['zero', 'sign', 'parity', 'aux_carry']
        },
        0b00101111: { 'name': 'cma',
            'func': cma,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b00100111: { 'name': 'daa',
            'func': daa,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['zero', 'sign', 'parity', 'carry', 'aux_carry']
        },
        # register pair instructions
        0b11101011: { 'name': 'xchg',
            'func': xchg,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': []

        },
        0b11100011: { 'name': 'xthl',
            'func': xthl,
            'cycle': 5,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11111001: { 'name': 'sphl',
            'func': sphl,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': []
        },
        # immediate data instructions
        0b00110110: { 'name': 'mvi m',
            'func': mvi_m,
            'cycle': 3,
            'byte_count': 2,
            'operands': ['number']
        },
        0b11000110: { 'name': 'adi',
            'func': adi,
            'cycle': 2,
            'byte_count': 2,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b11001110: { 'name': 'aci',
            'func': aci,
            'cycle': 2,
            'byte_count': 2,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b11010110: { 'name': 'sui',
            'func': sui,
            'cycle': 2,
            'byte_count': 2,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b11011110: { 'name': 'sbi',
            'func': sbi,
            'cycle': 2,
            'byte_count': 2,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b11100110: { 'name': 'ani',
            'func': ani,
            'cycle': 2,
            'byte_count': 2,
            'status_bits_affected': ['zero', 'sign', 'parity', 'aux_carry']
        },
        0b11101110: { 'name': 'xri',
            'func': xri,
            'cycle': 2,
            'byte_count': 2,
            'status_bits_affected': ['zero', 'sign', 'parity', 'aux_carry']
        },
        0b11110110: { 'name': 'ori',
            'func': ori,
            'cycle': 2,
            'byte_count': 2,
            'status_bits_affected': ['zero', 'sign', 'parity', 'aux_carry']
        },
        0b11111110: { 'name': 'cpi',
            'func': cpi,
            'cycle': 2,
            'byte_count': 2,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        # rotate accumulator instructions
        0b00001111: { 'name': 'rrc',
            'func': rrc,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry']
        },
        0b00000111: { 'name': 'rlc',
            'func': rlc,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry']
        },
        0b00010111: { 'name': 'ral',
            'func': ral,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry']
        },
        0b00011111: { 'name': 'rar',
            'func': rar,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry']
        },
        # data transfer intsructions
        0b00000010: { 'name': 'stax bc', 
            'func': stax_bc,
            'cycle': 2,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b00010010: { 'name': 'stax de',
            'func': stax_de,
            'cycle': 2,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b00001010: { 'name': 'ldax bc',
            'func': ldax_bc,
            'cycle': 2,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b00011010: { 'name': 'ldax de',
            'func': ldax_de,
            'cycle': 2,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b10000110: {
            'name': 'add m',
            'func': add_m,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b10001110: {
            'name': 'adc m',
            'func': adc_m,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b10010110: {
            'name': 'sub m',
            'func': sub_m,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b10011110: {
            'name': 'sbb m',
            'func': sbb_m,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b10100110: {
            'name': 'ana m',
            'func': ana_m,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['zero', 'sign', 'parity', 'aux_carry']
        },
        0b10101110: {
            'name': 'xra m',
            'func': xra_m,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['zero', 'sign', 'parity', 'aux_carry']
        },
        0b10110110: {
            'name': 'ora m',
            'func': ora_m,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['zero', 'sign', 'parity', 'aux_carry']
        },
        0b10111110: {
            'name': 'cmp m',
            'func': cmp_m,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': ['carry', 'zero', 'sign', 'parity', 'aux_carry']
        },
        0b00110010: { 'name': 'sta',
            'func': sta,
            'cycle': 4,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b00111010: { 'name': 'lda',
            'func': lda,
            'cycle': 4,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b00100010: { 'name': 'shld',
            'func': shld,
            'cycle': 5,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b00101010: { 'name': 'lhld',
            'func': lhld,
            'cycle': 5,
            'byte_count': 3,
            'status_bits_affected': []
        },
        # jumps/calls/returns
        0b11000011: { 'name': 'jmp',
            'func': jmp,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11010010: { 'name': 'jnc',
            'func': jnc,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11101001: { 'name': 'pchl',
            'func': pchl,
            'cycle': 1,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11011010: { 'name': 'jc',
            'func': jc,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11001010: { 'name': 'jz',
            'func': jz,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11000010: { 'name': 'jnz',
            'func': jnz,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11111010: { 'name': 'jm',
            'func': jm,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11110010: { 'name': 'jp',
            'func': jp,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11101010: { 'name': 'jpe',
            'func': jpe,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11100010: { 'name': 'jpo',
            'func': jpo,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        # call instrcutions
        0b11001101: { 'name': 'call',
            'func': call,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11011100: { 'name': 'cc',
            'func': cc,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11010100: { 'name': 'cnc',
            'func': cnc,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11001100: { 'name': 'cz',
            'func': cz,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11000100: { 'name': 'cnz',
            'func': cnz,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11111100: { 'name': 'cm',
            'func': cm,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11110100: { 'name': 'cp',
            'func': cp,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11101100: { 'name': 'cpe',
            'func': cpe,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        0b11100100: { 'name': 'cpo',
            'func': cpo,
            'cycle': 3,
            'byte_count': 3,
            'status_bits_affected': []
        },
        # return instructions
        0b11001011: { 'name': 'ret',
            'func': ret,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11011000: { 'name': 'rc',
            'func': rc,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11010000: { 'name': 'rnc',
            'func': rnc,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11001000: { 'name': 'rz',
            'func': rz,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11000000: { 'name': 'rnz',
            'func': rnz,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11111000: { 'name': 'rm',
            'func': rm,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11110000: { 'name': 'rp',
            'func': rp,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11101000: { 'name': 'rpe',
            'func': rpe,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        },
        0b11100000: { 'name': 'rpo',
            'func': rpo,
            'cycle': 3,
            'byte_count': 1,
            'status_bits_affected': []
        }
    }
    # to make sure procedural generation of instructions does not overwrite existing ones
    def addInstruction (self, opcode, name, func, cycle, byte_count, status_bits_affected=[]):
        for i in self.instructions.keys():
            if i == opcode:
                raise ValueError(f"Instruction with opcode {opcode} already exists.")
        self.instructions[opcode] = {
            'name': name,
            'func': func,
            'cycle': cycle,
            'byte_count': byte_count,
            'status_bits_affected': status_bits_affected
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
            self.addInstruction(0b00000100 | (code << 3), f'inr {reg}', lambda self, reg=reg: self.inr(reg), 3, 1, ['zero', 'sign', 'parity', 'aux_carry'])
            self.addInstruction(0b00000101 | (code << 3), f'dcr {reg}', lambda self, reg=reg: self.dcr(reg), 3, 1, ['zero', 'sign', 'parity', 'aux_carry'])

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
            self.addInstruction(opcode, f'add {dest}', lambda self, dest=dest: self.add(dest), 1, 1, ['carry', 'zero', 'sign', 'parity', 'aux_carry'])
        # adc
        for dest, dest_code in register_bytecodes.items():
            if (dest == 'm'):
                continue  # ADC for M will be handled manually
            opcode = 0b10001000 | (dest_code)
            self.addInstruction(opcode, f'adc {dest}', lambda self, dest=dest: self.adc(dest), 1, 1, ['carry', 'zero', 'sign', 'parity', 'aux_carry'])
        # sub
        for dest, dest_code in register_bytecodes.items():
            if (dest == 'm'):
                continue  # SUB for M will be handled manually
            opcode = 0b10010000 | (dest_code)
            self.addInstruction(opcode, f'sub {dest}', lambda self, dest=dest: self.sub(dest), 1, 1, ['carry', 'zero', 'sign', 'parity', 'aux_carry'])
        # sbb
        for dest, dest_code in register_bytecodes.items():
            if (dest == 'm'):
                continue  # SBB for M will be handled manually
            opcode = 0b10011000 | (dest_code)
            self.addInstruction(opcode, f'sbb {dest}', lambda self, dest=dest: self.sbb(dest), 1, 1, ['carry', 'zero', 'sign', 'parity', 'aux_carry'])
        # ana
        for dest, dest_code in register_bytecodes.items():
            if (dest == 'm'):
                continue  # ANA for M will be handled manually
            opcode = 0b10100000 | (dest_code)
            self.addInstruction(opcode, f'ana {dest}', lambda self, dest=dest: self.ana(dest), 1, 1, ['carry', 'zero', 'sign', 'parity', 'aux_carry'])
        # xra
        for dest, dest_code in register_bytecodes.items():
            if (dest == 'm'):
                continue  # XRA for M will be handled manually
            opcode = 0b10101000 | (dest_code)
            self.addInstruction(opcode, f'xra {dest}', lambda self, dest=dest: self.xra(dest), 1, 1, ['carry', 'zero', 'sign', 'parity', 'aux_carry'])
        # ora
        for dest, dest_code in register_bytecodes.items():
            if (dest == 'm'):
                continue  # ORA for M will be handled manually
            opcode = 0b10110000 | (dest_code)
            self.addInstruction(opcode, f'ora {dest}', lambda self, dest=dest: self.ora(dest), 1, 1, ['carry', 'zero', 'sign', 'parity', 'aux_carry'])
        # cmp
        for dest, dest_code in register_bytecodes.items():
            if (dest == 'm'):
                continue  # CMP for M will be handled manually
            opcode = 0b10111000 | (dest_code)
            self.addInstruction(opcode, f'cmp {dest}', lambda self, dest=dest: self.cmp(dest), 1, 1, ['carry', 'zero', 'sign', 'parity', 'aux_carry'])
        # lxi
        register_pairs_lxi = {
            'bc': 0b00,
            'de': 0b01,
            'hl': 0b10,
            'sp': 0b11
        }
        for rp, code in register_pairs_lxi.items():
            opcode = 0b00000001 | (code << 4)
            self.addInstruction(opcode, f'lxi {rp}', lambda self, rp=rp: self.lxi(rp), 3, 3)
        



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
                value = func(self)
                self.statusBitsUpdate(value, instruction['status_bits_affected'])
                if instruction['name'] == 'hlt' or self.manual_mode:
                   self.halted = True
                   print("HLT instruction or manual mode encountered, stopping execution.") 
                   while self.execution_thread_interrupt_event.is_set() == False:
                       if self.execution_thread_stop_event.is_set():
                           print("Execution thread stop event set during HLT, stopping execution.")
                           break
                       pass
                   self.execution_thread_interrupt_event.clear()
                   print("Resuming execution after interrupt or manual step.")
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
        elif (string == 'board'):
            board = int(input_data['data'])
            self.memory = [0] * board
        elif (string == 'step'):
            print('Received step command')
            if self.execution_thread is not None and self.execution_thread.is_alive():
                print("Stepping execution thread...")
                self.execution_thread_interrupt_event.set()
            else:
                print("No execution thread running, cannot step.")
        elif (string == 'manual'):
            print('Received manual command')
            self.manual_mode = True
        elif (string == 'auto'):
            print('Received auto command')
            self.manual_mode = False
            if self.execution_thread is not None and self.execution_thread.is_alive():
                print("Resuming execution thread from manual mode...")
                self.execution_thread_interrupt_event.set()
        elif (string == 'quit'):
            print('Received quit command, stopping execution and exiting.')
            if self.execution_thread is not None and self.execution_thread.is_alive():
                self.execution_thread_stop_event.set()
                self.execution_thread.join()
            return 0
        elif (string == 'switchboard'):
            print('Received switchboard command')
            # return the indicator data
            indicator_data = {
                'address': self.pc,
                'data': self.memory[self.pc] if self.pc < len(self.memory) else 0,
                'inte': 1 if self.interrupt else 0,
                'hlta': 1 if self.halted else 0
            }
            return indicator_data
        else:
            print(f"Unknown command: {string}")
        return 1

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
            for code in self.instructions.values():
                if line == code['name']:
                    bytecode.append(list(self.instructions.keys())[list(self.instructions.values()).index(code)])
                    bytecount += code['byte_count']
                    skip_parts = True
                    break
            if skip_parts:
                continue
            parts = line.split()
            print(parts)
            for code in self.instructions.values():
                if parts[0] == code['name']:
                    bytecode.append(list(self.instructions.keys())[list(self.instructions.values()).index(code)])
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
                    bytecount += code['byte_count']
                    skip_parts = True
                    break
                elif parts[0] in code['name']:
                    concat_part = parts[0]
                    for i in range(1, len(parts)):
                        concat_part += parts[i].replace(',', '')
                        if concat_part == code['name'].replace(' ', ''):
                            # find the opcode for this instruction and add to bytecode
                            bytecode.append(next(k for k, v in self.instructions.items() if v == code))
                            # rest of parts are operands, need to convert to numbers and add to bytecode
                            for j in range(i+1, len(parts)):
                                operand = parts[j].replace(',', '')
                                # jmp or call
                                if operand in sections:
                                    bytecode.append(sections[operand] & 0xFF)
                                    bytecode.append((sections[operand] >> 8) & 0xFF)
                                else:
                                    if operand.endswith('h'):
                                        operand = operand[:-1]
                                        # if the instruction is 3 bytes, means we have a 16 bit number to output instead of just one
                                        if code['byte_count'] == 3 and int(operand, 16) > 0xFFFF:
                                            raise ValueError(f"Operand {operand} out of range for word")
                                        if code['byte_count'] == 2 and int(operand, 16) > 0xFF:
                                            raise ValueError(f"Operand {operand} out of range for byte")
                                        val = int(operand, 16)
                                        if code['byte_count'] == 3:
                                            bytecode.append(val & 0xFF)
                                            bytecode.append((val >> 8) & 0xFF)
                                        else:
                                            bytecode.append(int(operand, 16) & 0xFF)
                                    else:
                                        if (int(operand) > 0xFF):
                                            raise ValueError(f"Operand {operand} out of range for byte")
                                        bytecode.append(int(operand) & 0xFF)
                            bytecount += code['byte_count']
                            skip_parts = True
                            break
                    if skip_parts:
                        break
        print(f"Generated bytecode: {bytecode}")
        print(f"Bytecode in hex: {[hex(b) for b in bytecode]}")
        return bytecode