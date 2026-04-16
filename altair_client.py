import json
import socket
from time import sleep
import sys

HOST = '199.17.161.139'	# target IP
LOCAL = '127.0.0.1'
PORT = 3461	            # the target port

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

# todo, switch board view

while True:
    action = input('Input action to take on Altair:')
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
    elif (action == 'exit'):
        print("Exiting client.")
        break
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
    send_client_data(json.dumps(client_data))

sock.close()