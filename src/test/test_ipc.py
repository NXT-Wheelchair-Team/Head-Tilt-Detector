import zmq


def run(sock):
    while True:
        msg = sock.recv()
        print(msg)


if __name__ == '__main__':
    ip = '127.0.0.1'  # INPUT_IP
    port = 5557       # INPUT_PORT
    out_port = 12345

    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind('tcp://{}:{}'.format(ip, port))

    out_socket = zmq.Context().socket(zmq.PAIR)
    out_socket.connect('tcp://{}:{}'.format(ip, out_port))

    run(socket)

