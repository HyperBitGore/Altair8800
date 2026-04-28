import json
import socket
import threading
from time import sleep
import sys

input_register = 0
indicator_data = {}

HOST = '199.17.161.139'	# target IP
LOCAL = '127.0.0.1'
PORT = 3462	            # the target port

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send_client_data(data) -> None:
    """Send client data over a socket connection."""
    try:
        message = data.encode('utf-8')
        sock.sendall(message)
        print(f"Data sent: {data}")
    except Exception as e:
        print(f"Error: {e}")

def convertHEXFileToBytes(file_path: str) -> bytes:
    print(f"Attempting to read hex data from file: {file_path}")
    try:
        with open(file_path, 'r') as hex_file:
            hex_data = hex_file.read().split('\n')
            print(f"Hex data read from file: {hex_data}")
            byte_data = bytes.fromhex(''.join(hex_data))
            return byte_data
    except Exception as e:
        print(f"Error: {e}")
        return b''
def printHelp ():
    print('List of commands:')
    print('program - program the Altair with a hex or assembly file')
    print('device_set - set a device to a value')
    print('quit - exit the client')
    print('restart - restart the Altair')
    print('interrupt - send an interrupt to the Altair')
    print('memory - set the memory board size')
    print('switchboard - output switchboard values')
    print('step - step through the next instruction, requires manual mode to be set')
    print('manual - set the Altair to manual mode, where it will execute one instruction at a time and wait for a step command')
    print('auto - set the Altair to auto mode, where it will execute continuously until a HLT instruction or interrupt is encountered')
def renderSwitchboard ():
    # address leds
    val = indicator_data['address']
    for i in range(16):
        output = (val >> i) & 0x01
        if output == 1:
            print(f'A{i}[X]', end=' ')
        else:
            print(f'A{i}[ ]', end=' ')
    print()
    val = indicator_data['data']
    for i in range(8):
        output = (val >> i) & 0x01
        if output == 1:
            print(f'D{i}[X]', end=' ')
        else:
            print(f'D{i}[ ]', end=' ')
    print()

    val = indicator_data['inte']
    print(f"INTE: {'ON' if val == 1 else 'OFF'}")

    val = indicator_data['hlta']
    print(f"HLTA: {'ON' if val == 1 else 'OFF'}")
receive_exit_event = threading.Event()
def receive_indicators ():
    indicator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if local:
            print(f"Connecting to indicator socket at {LOCAL}:{PORT + 1}")
            indicator_socket.connect((LOCAL, PORT + 1))
        else:
            print(f"Connecting to indicator socket at {HOST}:{PORT + 1}")
            indicator_socket.connect((HOST, PORT + 1))
    except ConnectionRefusedError:
        print(f"Failed to connect to indicator socket at {HOST}:{PORT + 1}")
        return
    while not receive_exit_event.is_set():
        data = indicator_socket.recv(1024)
        if not data:
            print("Connection closed by server.")
            receive_exit_event.set()
        decoded = json.loads(data.decode('utf-8'))
        print(f"Received data: {decoded}")
        indicator_data.update(decoded)

args = {arg.lower() for arg in sys.argv[1:]}
local = 'local' in args or '--local' in args

try:
    if (local):
        print(f"Connecting to local server at {LOCAL}:{PORT}")
        sock.connect((LOCAL, PORT))
    else:
        print(f"Connecting to remote server at {HOST}:{PORT}")
        sock.connect((HOST, PORT))
except ConnectionRefusedError:
    print(f"Failed to connect to {HOST}:{PORT}")
except Exception as e:
    print(f"Error: {e}")

client_data = {
    "command": "program",
    "data": list()
}
threading.Thread(target=receive_indicators, daemon=True).start()

printHelp()
run = True
while run:
    action = input('Input action to take on Altair (type "quit" to exit, "help" for commands):')
    if (action == 'program'):
        assembly = input('Assembly or hex file? (a/h): ')
        if assembly == 'a':
            asm_file_path = input('Input the assembly file to load: ')
            assembly_text = ''
            try:
                with open(asm_file_path, 'r') as asm_file:
                    assembly_text = asm_file.read()
            except Exception as e:
                print(f"Error: {e}")
                continue
            client_data = {
                "command": "program_assembly",
                "data": assembly_text
            }
        else:
            hex_file_path = input('Input the hex file to load: ')
            echo_data = convertHEXFileToBytes(hex_file_path)
            client_data = {
                "command": "program",
                "data": list(echo_data)
            }
    elif (action == 'device_set'):
        device_no = input('Input the device number to set: ')
        value = input('Input the value to set: ')
        client_data = {
            "command": "device_set",
            "device_no": int(device_no),
            "value": int(value)
        }
    elif action == 'restart':
        client_data = {
            "command": "restart",
            "data": list()
        }
    elif action == 'interrupt':
        client_data = {
            "command": "interrupt",
            "data": list()
        }
    elif action == 'memory':
        board = input('What memory board set set? 1: 256 byte, 2: 1024 byte, 3: 4096 byte, 4: 8192 byte')
        if board == '1':
            board = '256'
        elif board == '2':
            board = '1024'
        elif board == '3':
            board = '4096'
        elif board == '4':
            board = '8192'
        client_data = {
            "command": "board",
            "data": board
        }
    elif action == 'help':
        printHelp()
        continue
    elif action == 'switchboard':
        renderSwitchboard()
        sleep(2)
        continue
    elif action == 'step':
        client_data = {
            "command": "step",
            "data": list()
        }
    elif action == 'manual':
        client_data = {
            "command": "manual",
            "data": list()
        }
    elif action == 'auto':
        client_data = {
            "command": "auto",
            "data": list()
        }
    elif action == 'quit':
        client_data = {
            "command": "quit",
            "data": list()
        }
        run = False
        receive_exit_event.set()
    else:
        print('Not a valid command!')
        continue
    send_client_data(json.dumps(client_data))
        

sock.close()