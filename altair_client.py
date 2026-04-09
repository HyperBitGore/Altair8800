import json
import socket
from time import sleep

HOST = '127.0.0.1'	# target IP
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

hex_file_path = input('Input the hex file to load: ')

echo_data = convertHEXFileToBytes(hex_file_path)
print(f"Echo data: {echo_data}")
try:
    sock.connect((HOST, PORT))
except ConnectionRefusedError:
    print(f"Failed to connect to {HOST}:{PORT}")
except Exception as e:
    print(f"Error: {e}")

client_data = {
    "command": "program",
    "data": list(echo_data)
}

while True:
    send_client_data(json.dumps(client_data))
    sleep(5)