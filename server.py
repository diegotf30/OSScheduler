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
    print>> sys.stderr, 'starting up on %s port %s' % server_address
    sock.bind(server_address)

    # Listen for incoming connections, socket is in server-mode
    sock.listen(1)
    print>> sys.stderr, 'waiting for a connection...'

    return sock.accept()

def receiveData() :
    "Receives data from client, removes comments and formats it into a list"
    data = connection.recv(256)
    print>> sys.stderr, 'server received "%s"' % data
    return data.split('/')[0].split()

def createProcess(readyQueue, process, pid) :
    """Adds process to readyQueue, sorts based on policy
        Process: PID, entryTime, CPUTime, remainingTime"""
    readyQueue.append((pid, process[0], process[3], process[3]))
    readyQueue.sort(key=lambda tup: tup[3])

def changeQueue(pid, removeFrom, addTo) :
    """Moves Process from CPU/readyQueue into blockedQueue (or vice versa)
        because of I/O burst"""

    process = [i for i in removeFrom if i[0] == pid][0]
    removeFrom = [i for i in removeFrom if i[0] != pid]

    addTo.append(process)
    addTo.sort(key=lambda tup: tup[3])

def scheduleSRT(data) :
    "Focuses on executing the process with the Shortest Remaining Time left"
    readyQueue = []
    blockedQueue = []
    pid = 0

    while True:
        if 'CREATE' in data :
            createProcess(readyQueue, data, pid)
            connection.sendall('process created with PID: ', pid)
            pid += 1

        elif 'I/O' in data :
            pid = data[3]
            if 'INICIA' in data :
                changeQueue(pid, readyQueue, blockedQueue)
                connection.sendall('process #', pid, ' has entered I/O')
            else :
                changeQueue(pid, blockedQueue, readyQueue)
                connection.sendall('process #', pid, ' has successfully exited I/O')

        data = receiveData()

def scheduleSJF(data) :
    "Executes the Shortest Job First (in non-expulsive manner)"
    pass


if __name__ == '__main__':
    connection, client_address = setup()
    print>> sys.stderr, 'connection from', client_address

    # Policy to work upon (SRT or SJF)
    policy = sys.argv[1]
    # Context change, time wasted whilst switching processes in CPU
    cc = sys.argv[2]
    # Number of CPUs available for processes
    num_cpus = int(sys.argv[3])

    try:
        data = receiveData()
        start = int(data[0])
        if data:
            if policy == 'SRT' :
                scheduleSRT(data)
            else :
                scheduleSJF(data)
        else:  # No data sent by client
            print>> sys.stderr, 'no data from', client_address
            connection.close()
            sys.exit()
    finally:
        # Clean up the connection
        print>> sys.stderr, 'se fue al finally'
        connection.close()

    sys.exit()
