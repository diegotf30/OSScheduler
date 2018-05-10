#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import sys


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
    "Receives data from client, removes comments and formats instruction into a list"
    data = connection.recv(256)
    print>> sys.stderr, 'server received "%s"' % data
    return data.split('/')[0].split()

def createProcess(readyQueue, process, pid) :
    """Adds process to readyQueue, sorts based on policy
        Process: PID, entryTime, CPUTime, remainingTime"""
    readyQueue.append((pid, float(process[0]), int(process[3]), int(process[3])))
    readyQueue.sort(key=lambda tup: tup[3])

def removeFromCPU(pid, CPUs, readyQueue) :
    """Moves currently running process to readyQueue,
        helper function for changeQueue() & killProcess()"""
    for CPU in CPUs :
        if CPU and CPU[0] == pid :
            readyQueue.append(CPU)
            CPUs[CPUs.index(CPU)] = ()  # Add idle CPU
            break  # No need to check rest of CPUs

def changeQueue(pid, removeFrom, addTo) :
    """Moves Process from CPU/readyQueue into blockedQueue (or vice versa)
        because of an I/O burst"""
    process = [i for i in removeFrom if i[0] == pid][0]
    removeFrom = [i for i in removeFrom if i[0] != pid]

    addTo.append(process)
    addTo.sort(key=lambda tup: tup[3])

def killProcess(pid, readyQueue, blockedQueue) :
    process2kill = [i for i in readyQueue if i[0] == pid]

    if process2kill :
        readyQueue = [i for i in readyQueue if i[0] != pid]
        return process2kill[0]
    else :  # Not found in readyQueue, process must be blocked
        blockedQueue = [i for i in blockedQueue if i[0] != pid]
        return [i for i in blockedQueue if i[0] == pid][0]

def expropiateProcess(CPUs, CPU, readyQueue) :
    "If there's a shorter job in queue it is placed in CPU instead of the current one"
    if CPU and CPU[3] > readyQueue[0][3] :
        readyQueue.append(CPU)
        readyQueue.sort(key=lambda tup: tup[3])
        CPUs[CPUs.index(CPU)] = readyQueue.pop(0)

def updateCPUStatus(connection, CPUs, policy, readyQueue, terminatedQueue, last_time, curr_time) :
    """Substracts a second to the CPUs running processes, assigns process
        to idle ones, and verifies (SRT-only) if there's a shorter job"""
    for CPU in CPUs :
        # Verifies if CPU is not empty and process has pending CPU time
        if CPU and CPU[3] > 0 :
            # Work-around because of variable names
            tempCPU = CPU[:3] + (CPU[3] - (curr_time - last_time),)
            if tempCPU[3] < 0:
                tempCPU = CPU[:3] + (0,)
            CPUs[CPUs.index(CPU)] = tempCPU
            CPU = tempCPU
        else :  # Is empty, assigns to CPU the next process ready2go
            if CPU and CPU[3] <= 0 :
                # Logs terminated process info and its exit time
                terminatedQueue.append(CPU + (curr_time,))
            if readyQueue :
                CPUs[CPUs.index(CPU)] = readyQueue.pop(0)

        if policy == 'SRT' :
            expropiateProcess(CPUs, CPU, readyQueue)

def formatOutput(process, status) :
    "Helper function for printing process info. and its status"
    print>> sys.stderr, "{}\t{}\t   {}\t\t{}\n".format(process[0], process[2], process[3], status)

def printProgress(CPUs, readyQueue, blockedQueue, terminatedQueue) :
    "Prints status and relevant info for each process received"
    print>> sys.stderr, "----------------PROGRESS----------------"
    print>> sys.stderr, "PID\tCPUtime\t   Time Left    Status"
    n = 1
    for process in CPUs :
        if process :
            formatOutput(process, "(ON CPU {})".format(n))
            n += 1

    for process in readyQueue :
        formatOutput(process, "(IN QUEUE)")

    for process in blockedQueue :
        formatOutput(process, "(BLOCKED)")

    for process in terminatedQueue :
        formatOutput(process, "(TERMINATED AT t={} s)".format(process[4]))

def scheduler(data, policy, num_cpus, curr_time) :
    "Focuses on executing the process with the Shortest Remaining Time left"
    readyQueue = []
    blockedQueue = []
    terminatedQueue = []
    # Keeps track of last-assigned PID
    PIDCounter = 1
    # Var. for time management
    last_time = 0
    # Makes list of idle CPUs, each one contains process info to be executed
    CPUs = [() for i in range(0, num_cpus)]

    while True:
        if 'CREATE' in data :
            createProcess(readyQueue, data, PIDCounter)
            connection.sendall('process created with PID: {}'.format(PIDCounter))
            PIDCounter += 1

        elif 'I/O' in data :
            pid = int(data[3])  # Helper
            if 'INICIA' in data :
                removeFromCPU(pid, CPUs, readyQueue)
                changeQueue(pid, readyQueue, blockedQueue)
                connection.sendall('process #{} has entered I/O'.format(pid))
            else :  # TERMINA I/O
                changeQueue(pid, blockedQueue, readyQueue)
                connection.sendall('process #{} has successfully exited I/O'.format(pid))

        elif 'KILL' in data :
            pid = int(data[2])  # Helper
            removeFromCPU(pid, CPUs, readyQueue)
            killedProcess = killProcess(pid, readyQueue, blockedQueue)
            terminatedQueue.append(killedProcess + (curr_time,))
            connection.sendall('process #{} terminated. CPU time: {}'
                            .format(killedProcess[0], killedProcess[2] - killedProcess[3]))
        elif 'END' in data :
            break
        else :
            connection.sendall('received {}'.format(' '.join(data)))

        updateCPUStatus(connection, CPUs, policy, readyQueue, terminatedQueue, last_time, curr_time)
        printProgress(CPUs, readyQueue, blockedQueue, terminatedQueue)
        data = receiveData()
        last_time = curr_time
        curr_time = float(data[0])


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
        time = float(data[0])
        if data:
            scheduler(data, policy, num_cpus, time)
        else:  # No data sent by client
            print>> sys.stderr, 'no data from', client_address
            connection.close()
            sys.exit()
    finally:
        # Clean up the connection
        print>> sys.stderr, 'Conexion con cliente ha terminado'
        connection.close()

    sys.exit()
