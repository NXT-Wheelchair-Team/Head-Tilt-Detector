import time
import socket
import json


def run(sock, ip, port):
    mock_dict = {
        'type': 'accel',
        'data': [0, 1, 2]
    }
    while True:
        sock.sendto(bytes(json.dumps(mock_dict), 'utf-8'), (ip, port))
        print('test out')
        time.sleep(0.2)


if __name__ == '__main__':
    ip = '127.0.0.1'  # INPUT_IP
    out_port = 12345

    # sock = zmq.Context().socket(zmq.PAIR)
    # sock.connect('{}:{}'.format(ip, out_port))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    run(sock, ip, out_port)

