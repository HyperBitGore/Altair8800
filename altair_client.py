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

# Example usage
client_data = 'flip0'
try:
    sock.connect((HOST, PORT))
except ConnectionRefusedError:
    print(f"Failed to connect to {HOST}:{PORT}")
except Exception as e:
    print(f"Error: {e}")

while True:
    send_client_data(client_data)
    sleep(5)