#!/usr/bin/env python3
import socket
import random
import argparse
import signal
import errno
import os
import sys
import atexit
import logzero
from logzero import logger

def parent():
    logger.info( f"Parent: {os.getpid()} is logged in")
    
def child(ticket2):
    logger.info( f"Child: {os.getpid()} is logged in, Numbers to send to user (array format)-\n {ticket2}\n")

#Function to convert aspecific format given string to array
def stringToArray(string):
    resultArray = list(string.split(" "))
    return resultArray

# Function to convet array to specific format string
def arrayToString(array):
    resultString = ''
    for h in range(0, len(array)):
        #print(f"inside for h {h}")
        for i in range(0,  len(array[h])):
            #print(f"inside for i {i} {len(array[h])}")
            splitter = " "
            resultString += splitter.join(map(str,  array[h][i]))
            if i < (len(array[h])-1):
                resultString += '-'
        if h < (len(array)-1):
            resultString += '/'
    return resultString

# Function for "killing" child process so no zombies would apppear
def childHandler(signalNumber, frame):
    while True:
        try:
            #wait for child
            pid, status = os.waitpid(
                -1,
                os.WNOHANG
            )
        except OSError:
            return
        if pid == 0:
            return

# This function will receive the amount of tickets the user want, 
# the lottery type, the range to create a pool and the amount of
# sequence to draw
def lotteryNumbers( lotteryType, ticketAmount,  poolRange,  numbersAmount) :     
    ticket2 = []    
    iterationAmount = 1    
    #Check for max lotto, because it asks for three sequences
    if lotteryType == "max" :
        
        iterationAmount = 3      
        
    #First iteration defines the amount of tickets to print
    for j in range(0,  ticketAmount) :   
        #Create a pool and fill it
        pool = [x for x in range(1, poolRange+1)]  
        
        ticket = []
        #Second iteration defines how many sequence inside each ticket
        for h in range(0,  iterationAmount) : 
            drawNumbers = []
            
            #Third iteration to get the numbers from the pool
            for i in range(0,  numbersAmount) :
                
                #Shuffle the pool so the number at the back will be "random"
                random.shuffle(pool)
                
                #Append the popped number from the pool
                drawNumbers.append(pool.pop())
                
            ticket.append(drawNumbers)
            
        ticket2.append(ticket)  
    child(ticket2)
    return arrayToString(ticket2)

# Function that handle the connections
def requestHandler(socketObjectConnection):
    request = socketObjectConnection.recv(128)
    messageFromClient = request.decode("utf-8")
    arrayMessage = stringToArray(messageFromClient)
    lotteryResultString = lotteryNumbers(arrayMessage[0], int(arrayMessage[1]),  int(arrayMessage[2]), int(arrayMessage[3]))  
    sendToClient = lotteryResultString.encode("utf-8")
    socketObjectConnection.send(sendToClient)


# The runDarmon function will get the arguments for CLI,
# create socket objects, wait for connections from clients, 
# fork when client makes a request (the parent stop dealing
# with the request and the child stop listening at all), after
# the child process deals with the request, close it. Also
# and create queue's (for the time being). Since I am using the VM
# the daemon will accept every host.
def runDaemon(host,  port):
    daemonQueue = 200    
    try:
        serverAddress = (host, port,  0,  0)
        socketListen = socket.socket(socket.AF_INET6,  socket.SOCK_STREAM) #set Ipv6
        socketListen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#try to prevent hijacking
        socketListen.bind(serverAddress)
        socketListen.listen(daemonQueue)
        signal.signal(signal.SIGCHLD, childHandler) #start the child process "killer"
        while True:
            try:
                socketObjectConnection,  clientAddress = socketListen.accept()
            except IOError as e:
                errorCode, message = e.args
                if errorCode == errno.EINTR:
                    continue
                else:
                    raise
            processId = os.fork() #generate the child
            if processId == 0: #check if this is a child
                socketListen.close() # This makes the child not listen.
                requestHandler(socketObjectConnection)
                socketObjectConnection.close()
                os._exit(0) # this makes the child process wait to be harvested.
            else:
                parent() #log parent call
                socketObjectConnection.close() #this makes the parent close object to client.
    except Exception as err :
        logger.error(err)
        socketListen.close()


#Function to daemonize the program.
def daemonize(pidFile,  *,  
    stdin='/dev/null',
    stdout='/dev/null',
    stderr='/dev/null'):
    if os.path.exists(pidFile):
        logger.error('Daemon already up and running')
        raise RuntimeError('Daemon already up and running')
    #First fork to create new session owner        
    try:
        if os.fork() > 0:
            raise SystemExit(0) #kill parent
    except OSError as e:
        logger.error("First fork failed for daemonize")
        raise RuntimeError('First fork failed for daemonize >' + e)
        
        

    #umasking, changin environment, setting ids.
    id = os.getuid()
    os.chdir('/')
    os.umask(0)
    os.setsid()
    os.setuid(id)
    os.setgid(id)
    
    #Second fork for peace of mind
    try:
        if os.fork() > 0:
            raise SystemExit(0) #kill parent
    except OSError as e:
        logger.error("Second fork failed for daemonize")
        raise RuntimeError('Second fork failed for daemonize >' + e)
    #flush for safe
    sys.stdout.flush()
    sys.stderr.flush()
    #closing, dupping the closing to a log.
    with open(stdin,  'rb',  0) as stdReplace:
        os.dup2(stdReplace.fileno(),  sys.stdin.fileno())
    with open(stdout,  'ab',  0) as stdReplace:
        os.dup2(stdReplace.fileno(),  sys.stdout.fileno())
    with open(stderr,  'ab',  0) as stdReplace:
        os.dup2(stdReplace.fileno(),  sys.stderr.fileno())
    
    #create a path to create a directory
    dirPath = '/var/run'
    newDirName = "tempDirectory"
    path = os.path.join(dirPath,  newDirName)
    #checking if directory exists to create one in "su"
    if os.path.exists(path) == False :
        os.mkdir(path)
    #Open file that has pid to write the pid in.
    with open(pidFile,  'w') as pidFil:
        print(os.getpid(),  file=pidFil)
        
    #Delete pid file before exiting.
    atexit.register(lambda: os.remove(pidFile))
    
#signal handler for sigterm.
def sigterm_handler(signo,  frame):
    raise SystemExit(1)
#another way of making a log, not in use for this now.
def daemonAlive():
    import time
    sys.stdout.write(f'Daemon started with pid {os.getpid()}\n')
    while True:
        sys.stdout.write(f"Daemon Alive, time - {time.ctime()}\n")
        time.sleep(10)

if __name__ == '__main__':
    port = 8080
    host = "::1"
    #location where pid file is supposed to be.
    pidFileHolder = '/var/run/tempDirectory/daemon.pid'
    signal.signal(signal.SIGTERM,  sigterm_handler)
    parser = argparse.ArgumentParser(
        description = 'This is the Daemon of sequence of numbers generator.'
    )
    startStop=parser.add_mutually_exclusive_group(required=True)
    
    startStop.add_argument(
        '-start',  action = 'store_const',
        dest = 'startStop',  help = 'start script', 
        const = True )

    startStop.add_argument(
        '-stop',  action = 'store_const',
        dest = 'startStop',  help = 'Stop script if it is not running', 
        const = False )

    parser.add_argument(
        '-V', '--version',  action = 'version',
        version = '#(prog)s 1.0')

    argument = parser.parse_args() 
  
    # Setup rotating logfire, 3 rotations, 1mb max.
    logzero.logfile("/var/tmp/rotating-logfile.log",  
        maxBytes=1e6,  backupCount=3,  disableStderrLogger=True)
    #start or stop daemon
    if argument.startStop:
        try:
            #daemonize the daemon.
            daemonize(pidFileHolder,  stdout='/var/tmp/daemon.log', 
                stderr='/var/tmp/daemonErr.log')
        except RuntimeError as e: # catch error
            print(e,  file=sys.stderr)
            raise SystemExit(1)
        logger.info(f"Started with {os.getpid()}") # log start
        try:
            runDaemon(host,  port) #run daemon to listen
        except Exception as err :
            logger.error(err)
            raise SystemExit(1)
    else:
        #delete the file where the pid is when exiting signal happens.
        if os.path.exists(pidFileHolder):
            with open(pidFileHolder) as pidFile:
                os.kill(int(pidFile.read()),  signal.SIGTERM)
        else:
            #write to log and print to user.
            logger.error('Daemon currently not Runnig')
            print('Daemon currently not Runnig',  file=sys.stderr)
            raise SystemExit(1)
    
