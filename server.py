#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import sys
import time


def setup() :
    """Initializes server in localhost:10000, returns connection socket
        & client's address upon connection"""
    # TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 10000)
    print('starting up on %s port %s' % server_address, file=sys.stderr)
    sock.bind(server_address)

    # Listen for incoming connections, socket is in server-mode
    sock.listen(1)
    print('waiting for a connection...', file=sys.stderr)

    return sock.accept()

def scheduleSRT(data) :
    "Focuses on executing the process with the Shortest remaining time left"
    return 0

def scheduleSJF(data) :
    "Executes the Shortest Job First (in non-expulsive manner)"
    return 0


if __name__ == '__main__':
    connection, client_address = setup()
    print('connection from', client_address, file=sys.stderr)

    # Policy to work upon (SRT or SJF)
    policy = sys.argv[1]
    # Context change, time wasted whilst switching processes in CPU
    cc = sys.argv[2]
    # Number of CPUs available for processes
    num_cpus = int(sys.argv[3])

    try:
        # Receive the data
        while True:
            data = connection.recv(256)
            print('server received "%s"' % data, file=sys.stderr)
            if data:
                if policy is 'SRT' :
                    scheduleSRT(data)
                else :
                    scheduleSJF(data)

                # print('sending answer back to the client', file=sys.stderr)
                # connection.sendall('process created')
            else:  # No data sent by client
                print('no data from', client_address, file=sys.stderr)
                connection.close()
                sys.exit()
    finally:
        # Clean up the connection
        print('se fue al finally', file=sys.stderr)
        connection.close()

    sys.exit()
