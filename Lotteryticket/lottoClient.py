#!/usr/bin/python3
import argparse
import socket
import sys
import os
import random
import signal

random.seed()
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
    

# Function receives an string in specific format and
# convert it in an array.
def stringToArray(string):
    finalResult =[]
    firstSplitList = list(string.split("/"))#splitter for amount of tickets requested
    for h in range(0, len(firstSplitList)):        
        secondSplitList = list(firstSplitList[h].split("-")) #splitt for max lotto (which generates 3 sets)
        finalTemp =[]
        for i in range(0, len(secondSplitList)):
            temp = list(secondSplitList[i].split(" "))
            finalTemp.append(temp)
        finalResult.append(finalTemp)
        
    return finalResult

# This function will receive the amount of tickets the user want, 
# the lottery type, the range to create a pool and the amount of
# sequence to draw
def lotteryNumbers(lotteryType, ticketFinal, userIdentifier) :    
        
    #Try to open a file and write, with the user 
    # identifier as name, the sequence numbers and display to user.
    #get errors otherwise
    try:
        filehandle = open(f"{userIdentifier}",  "w")
        
        print(f"These are your numbers for your lotto {lotteryType} game, with user {userIdentifier}!\n" )
        filehandle.write(f"These are your numbers for your lotto {lotteryType}, with user {userIdentifier}\n")
        #check for lotto max to print and write
        if lotteryType == "max": 
        
            for i in range(0,  len(ticketFinal)):
                
                print(f"{i+1}) " )
                
                filehandle.write(f"Ticked#{i+1} \n")
                
                #Print the ticket for max lotto, three sequences of numbers for it.
                for j in range(0,  len(ticketFinal[i])): 
                    print(f"{ticketFinal[i][j]}")

                    filehandle.write(f"{j+1}) ")  
                    
                    filehandle.write(str(ticketFinal[i][j]) + ' ')
                    
                    filehandle.write('\n')
                           
            print("\n")
         
        #check for other lottos to print and write
        else:
            
              for i in range(0,  len(ticketFinal)):
                  
                filehandle.write(f"Ticket#{i+1} \n")
                
                #Print sequence for other lottos 
                print(f"{i+1}) {ticketFinal[i][0]}\n" )
                
                filehandle.write(f"{i+1}) " + str(ticketFinal[i][0]) + "\n\n")
                
    except IOError as err:
        print("We were unable to register your numbers to files, error:  ", err )
    except Exception as err:
        print("Unexpected error occurred and we were unable to register your numbers to files, error:  ", err )
    else:
        print(f"Just to remide you! \nYour numbers were registered at our files successfully under {userIdentifier}!\n")
        filehandle.close() #close
# Function to run the client getting arguments
# and input from user so it can connect to daemon
def clientRunning(lotteryType, maxClients, hostName, port,  reqAmount): 

    poolRange = 0

    numbers = 0

    while True:
        uniqueIdent = input("Please type your unique identifier with no spaces or -1Exit to close the app > ")
        findSpaces = ' ' in uniqueIdent
        if(findSpaces == True):
            print("There are spaces in yout identifier.")
        else:
            if(uniqueIdent == '-1Exit'):
                sys.exit("You choose to exit, thank you, hope to see you soon!")
            break
    #I changed the way to get the number of tickets so it will be
    #  easier to check if user input a number higher than 0
    while True:
        numberOfTickets = input("How many tickets would you like?(1 ticket minimum) > ")
        if(numberOfTickets.isnumeric() == False):
            print(f"{numberOfTickets} is not a number")
        else:
            if(int(numberOfTickets) <= 0 ):
                print("Minimum of 1 ticket requeired!")
            else:
                break
    
    uniqueIdentCounter = 0 #To change unique identifies
    uniqueIdentCounterNew = 1 #To change unique identifies
    oldText= f'>{str(uniqueIdentCounter)}' #To change unique identifies
    uniqueIdent += oldText #To change unique identifies
    oldTextReq= f'-{str(uniqueIdentCounter)}' #To change unique identifies for Request part
    uniqueIdent += oldTextReq #To change unique identifies for Request part
    lotteryArray = ['max', '649', 'lottario']
    for clientNumber in range(maxClients):
        try:
            pid = os.fork()
        except OSError:
            print("Client could not create child process!\n")
            continue
        if pid == 0:
            uniqueIdentCounterRequest = 0 #To change unique identifies for Request part
            uniqueIdentCounterNewRequest = 1 #To change unique identifies for Request part
            for requests in range(reqAmount):
                #Set poolRange and number amount for reach type of lotto.
                if lotteryType == "max":
                    poolRange = 49
                    numbers = 7
                elif lotteryType == "649":
                    poolRange = 49
                    numbers = 6
                else:
                    poolRange = 45
                    numbers = 6
                # Convert the arguments and details of ticket into string
                lotteryString = f"{lotteryType} {int(numberOfTickets)} {poolRange} {numbers}"
                stringToServer = lotteryString.encode("utf-8") #encode
                serverAddress = (hostName, port,  0,  0) #create an address to connect
                socketObject= socket.socket(socket.AF_INET6,  socket.SOCK_STREAM) #create the socket object
                socketObject.connect(serverAddress)
                bufferSize = int(numberOfTickets) * 128 #increase the buffer depending on amount of tickets
                socketObject.send(stringToServer)
                resultFromServer = socketObject.recv(bufferSize) #receive from daemon
                resultDecoded = resultFromServer.decode("utf-8") #decode
                resultArray = stringToArray(resultDecoded)
                socketObject.close()#close  
                lotteryNumbers(lotteryType, resultArray, uniqueIdent)
                
                #"Randomly" set the next  request
                randNumber = random.randrange(3)
                numberOfTickets = random.randrange(5) + 1
                lotteryType = lotteryArray[randNumber]
                uniqueIdent = uniqueIdent.replace(f'-{str(uniqueIdentCounterRequest)}', f'-{str(uniqueIdentCounterNewRequest)}')
                uniqueIdentCounterNewRequest += 1
                uniqueIdentCounterRequest += 1
            #finish child process.
            os._exit(0) 
        #"Randomly" set the next client request
        randNumber = random.randrange(3)
        numberOfTickets = random.randrange(5) + 1
        lotteryType = lotteryArray[randNumber]
        uniqueIdent = uniqueIdent.replace(f'>{str(uniqueIdentCounter)}', f'>{str(uniqueIdentCounterNew)}')
        uniqueIdentCounterNew += 1
        uniqueIdentCounter += 1

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
    description = 'This is the Client of the sequence of numbers generator.'
    )

    lotteryChoice=parser.add_mutually_exclusive_group(required=True)

    lotteryChoice.add_argument(
        '-max', action = 'store_const',  
        dest = 'lotteryType', const = 'max', 
        help = 'LottoMax Option')

    lotteryChoice.add_argument(
        '-649', action = 'store_const', 
        dest = 'lotteryType', const = '649',
        help = '649 lotto Option')

    lotteryChoice.add_argument(
        '-lottario', action = 'store_const', 
        dest = 'lotteryType', const = 'lottario',
        help = 'lottario Option')

    parser.add_argument(
        '-c',
        type=int,
        default = 2,
        help = 'Maximum number of client.',
        required=False,
        dest = 'maxClients'
    )
    
    parser.add_argument(
        '-req',
        type=int,
        default = 2,
        help = 'Maximum number of Requests.',
        required=False,
        dest = 'request'
    )

    parser.add_argument(
        '-port',
        action = 'store_const',
        dest = 'port',
        help = 'Using Port 8080',
        const = 8080, required=True)

    parser.add_argument(
        '-host',  action = 'store_const',
        dest = 'hostName',
        help = 'Using Host ::1',  const = '::1', required=True)

    parser.add_argument(
        '-v',  '--version',
        action = 'version', 
        version = '%(prog)s 1.0')
    
    argument = parser.parse_args()
    signal.signal(signal.SIGCHLD, childHandler) #start the child process "killer"
    #Passing arguments to function which will make requests   
    clientRunning(argument.lotteryType, argument.maxClients, argument.hostName,  argument.port,  argument.request)
    count = argument.request * argument.maxClients
    i = 0
    #sketchy way of trying to count the children forked. so the main process
    #only exits after all child are finished
    while i < count:
        try:            
            os.waitpid(0, 0)
        except Exception as e:
            i += 1
            continue
        i += 1
    sys.exit()
    
