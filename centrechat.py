#!/usr/bin/env python

##Author: Han He

import socket
import traceback
import select
import threading
import random

##This function manually adds in loss to the program
def lossySend(sock,message,dest,prob):
    randomNumber = random.randint(1,100)
    if randomNumber <= prob:
        sock.sendto(message,dest)
    else:
        print "This packet was dropped:\n"\
              +"-----------------------\n"\
              +message+"\n"\
              +"-----------------------\n"
        

##This class is for client of the chat room
##the client have a functionality of entering and leaving the chat room
##and respond to application with sendMessage and getMessage calls
##which would result in the interaction between client and server
class ChatClient:
    def __init__(self, name, port, nickname):
        """Constructor of client, taking name of the server, the port of the server. and the nickname of the user. Sends the connection message directly to the server"""
        self.handle = nickname
        self.hostAddress = (name,port)
        self.mysocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mysocket.bind(("",0))
        self.myAddress = ("127.0.0.1",self.mysocket.getsockname()[1])
        self.buffer = []
        self.sequence = 0
        self.expectSeq = 0
        message = "CONNECT\n%s\n%d\n\n"%(self.handle, self.sequence)
##       self.mysocket.sendto(message, self.hostAddress)
        lossySend(self.mysocket,message,self.hostAddress,50)
##        self.mysocket.sendto(message, self.hostAddress)
        self.previousMessage = message
        self.toSend = []
        self.lock = threading.RLock()

    def getToSend(self):
        """returns the message to send buffer"""
        return self.toSend


    def getSequenceNumber(self):
        """returns the sequence number that should be used"""
        return self.sequence
    
    def getSocket(self):
        """returns the client socket"""
        return self.mysocket

    def getMyAddress(self):
        """returns the client's address"""
        return self.myAddress

    def getHostAddress(self):
        """returns the address of the host"""
        return self.hostAddress
    
    def getHostName(self):
        """returns the name of the host"""
        return self.hostAddress[0]
    
    def getHostPort(self):
        """returns the port number of the server"""
        return self.hostAddress[0]

    def getBuffer(self):
        """returns the buffer"""
        with self.lock:
            return self.buffer

    def addBuffer(self, message):
        """adds a message to the buffer"""
        with self.lock:
            self.buffer.append(message)



    def getPreviousMessage(self):
        """returns the message that has not received ACK"""
        return self.previousMessage

    def updateSeq(self):
        """updates the sequence number"""
        self.sequence = (self.sequence+1)%1024

    def updatePreviousMessage(self, message):
        """sets the previous unACKed message to a new message"""
        self.previousMessage = message

    def disconnect(self):
        """disconnect method that the user could call on to disconnect with the server"""
        message = "DISCONNECT\n%s\n%d\n\n"%(self.handle, self.getSequenceNumber())
        print self.handle + " wants to leave."
        self.mysocket.sendto(message, self.getMyAddress())


    def getMessage(self):
        """returns the first message in the buffer"""
        with self.lock:
            if len(self.buffer) != 0:
                message = self.buffer[0]
                self.buffer = self.buffer[1:]
                return message
            else:
                return None
                                                
    def sendMessage(self,message):
        """called by the application, sends a SEND message to the client socket"""
        if len(message)>1400:
            print "Error: Message should not exceed the length of 1400."
        else:
            message = "SEND\n%s\n%d\n\n%s"%(self.handle, self.getSequenceNumber(),message)
            print self.getHandle(message), "wants to send a message."
            self.mysocket.sendto(message, self.getMyAddress())

    def getKeyWord(self,message):
        """returns the keyword of the message"""
        index = message.find("\n")
        keyword = message[:index]
        return keyword

    def getSeq(self,message):
        """returns the sequence number from the message"""
        if self.getKeyWord(message)=="ACK":
            index = message.find("\n")
            seq =  message[index+1:message.find("\n",index+1)]
            return eval(seq)
        else:
            index = message.find("\n")
            index = message.find("\n",index+1)
            seq =  message[index+1:message.find("\n",index+1)]
            return eval(seq)


    def getHandle(self,message):
        """returns the handle from the message"""
        index = message.find("\n")
        handle = message[index+1:message.find("\n",index+1)]
        return handle

    def getBody(self,message):
        """returns the body of the messge"""
        index = message.find("\n\n")
        body = message[index+2:]
        return body
            
    
    def waitForConnectAck(self):
        """state 1. Time out limit is set to 1 sec and if timeout, resend the message, if received ACK, enter stage 2"""
        timeoutLimit = 0.25
        readReady,outputready,exceptReady = select.select([self.getSocket()],[],[],timeoutLimit)
        if [readReady,outputready,exceptReady] == [[],[],[]]:
            lossySend(self.mysocket,self.getPreviousMessage(), self.getHostAddress(),50)
##            self.mysocket.sendto(self.getPreviousMessage(), self.getHostAddress())
            return 1
        else:
            message, address = self.getSocket().recvfrom(1500)
            if address == self.getHostAddress():
                if self.getKeyWord(message) == "ACK":
                    print "Client: Received ack."
                    self.updateSeq()
                    return 2
            return 1


    def chatState(self):
        """state 2. Waits for messages from both user and server"""
        readReady,outputready,exceptReady = select.select([self.getSocket()],[],[])
        if readReady!= []:
            message, address = self.getSocket().recvfrom(1500)
            if address == self.getMyAddress():
                if self.getKeyWord(message) == "DISCONNECT":
                    newMessage = "DISCONNECT\n%s\n%d\n\n"%(self.handle, self.getSequenceNumber())
                    lossySend(self.mysocket,newMessage, self.getHostAddress(),50)
##                    self.mysocket.sendto(newMessage, self.getHostAddress())
                    self.updatePreviousMessage(newMessage)                    
                    return 3
                if self.getKeyWord(message) == "SEND":
                    if len(self.getToSend()) == 0:
                        lossySend(self.mysocket,message,self.getHostAddress(),50)
##                        self.mysocket.sendto(message,self.getHostAddress())
                        self.updatePreviousMessage(message)
                        return 4
                    else: 
                        self.getToSend().insert(0,self.getBody(message))
                        return 2
            elif address == self.getHostAddress():
                if self.getKeyWord(message) == "SEND":
                    print "Client: Received a broadcast"
                    if self.getSeq(message)==self.expectSeq:  
                        handle = self.getHandle(message)
                        body = self.getBody(message)
                        self.addBuffer((handle,body))
                        self.expectSeq = (self.expectSeq+1)%1024
                    lossySend(self.mysocket,"ACK\n%s\n%d\n\n"%(self.handle,self.getSeq(message)),self.getHostAddress(),50)
##                    self.mysocket.sendto("ACK\n%s\n%d\n\n"%(self.handle,self.getSeq(message)),self.getHostAddress()) 
                    return 2
                    
        else:
            if len(self.getToSend())==0:
                return 2
            else:
                messageToSend = self.getToSend().pop()
                message = "SEND\n%s\n%d\n\n%s"%(self.handle, self.getSequenceNumber(),messageToSend)
                lossySend(self.mysocket,message,self.getHostAddress(),50)
##                self.mysocket.sendto(message,self.getHostAddress())
                self.updatePreviousMessage(message)
                return 4


              
    def waitForDisconnectAck(self):
        """state3. Time out limit is set to 1 sec and if timeout, resend the message, if received ACK, enter state 0. 'close socket'"""
        timeoutLimit = 0.25
        readReady,outputready,exceptReady = select.select([self.getSocket()],[],[],timeoutLimit)
        if [readReady,outputready,exceptReady] == [[],[],[]]:
            lossySend(self.mysocket,self.getPreviousMessage(), self.getHostAddress(),50)
##            self.mysocket.sendto(self.getPreviousMessage(), self.getHostAddress())
            return 3
        else:
            message, address = self.getSocket().recvfrom(1500)
            if address == self.getHostAddress():
                if self.getKeyWord(message) == "ACK":
                    seq = self.getSeq(message)
                    if seq == self.getSequenceNumber():
                        print "Client: Received ack for DISCONNECT"
                        self.getSocket().close()
                        return 0
            return 3
                


    def waitForSendAck(self):
        """state 4, Waits for the acknoledgement from the server. Handles the situation where the user send further requests"""
        timeoutLimit = 0.25
        readReady, outputReady, exceptReady = select.select([self.getSocket()],[],[],timeoutLimit)
        if [readReady,outputReady,exceptReady] == [[],[],[]]:
            print "Client: There is a timeout, resending the message to server"
            lossySend(self.mysocket,self.getPreviousMessage(), self.getHostAddress(),50)
##            self.mysocket.sendto(self.getPreviousMessage(), self.getHostAddress())
            return 4
        else:
            message,address = self.getSocket().recvfrom(1500)
            if address == self.getHostAddress():
                if self.getKeyWord(message)=="ACK":
                    seq = self.getSeq(message)
                    if seq == self.getSequenceNumber():
                        print "Client: Received ACK for message send"
                        self.updateSeq()
                        return 2
                elif self.getKeyWord(message)=="SEND":
                    if self.getSeq(message)==self.expectSeq:
                        handle = self.getHandle(message)
                        body = self.getBody(message)
                        self.addBuffer((handle,body))
                        self.expectSeq = (self.expectSeq+1)%1024
                        lossySend(self.mysocket,"ACK\n%s\n%d\n\n"%(self.handle,self.getSeq(message)),self.getHostAddress(),50)
##                        self.mysocket.sendto("ACK\n%s\n%d\n\n"%(self.handle,self.getSeq(message)),self.getHostAddress())
##                        if (handle == self.handle)and (body==self.getBody(self.getPreviousMessage())):
##                            return 2
                        return 4
            elif address == self.getMyAddress():
                if self.getKeyWord(message)=="SEND":
                    self.getToSend().insert(0,self.getBody(message))
                    return 4
                elif self.getKeyWord(message) == "DISCONNECT":
                    self.sequence = self.sequence+1
                    newMessage = "DISCONNECT\n%s\n%d\n\n"%(self.handle, self.getSequenceNumber())
                    lossySend(self.mysocket,newMessage,self.getHostAddress(),50)
##                    self.mysocket.sendto(newMessage, self.getHostAddress())
                    self.updatePreviousMessage(newMessage)
                    return 3

    def handleMessages(self):
        """handles the messages that is passed in to the client socket"""
        open = True
        
        state = 1
        ##state 1 is the waiting for CONNECT ACK stage
        ##state 2 is the chatroom state
        ##state 3 is the wait for DISCONNECT ACK state
        ##state 4 is the wait for SEND ACK state
        try:
            while open:
                if state == 1:
                    state = self.waitForConnectAck()
                elif state == 2:
                    state = self.chatState()
                elif state == 3:
                    state = self.waitForDisconnectAck()
                elif state == 4:
                    state = self.waitForSendAck()
                elif state == 0:
                    open = False

                            
        except Exception, e:
            print traceback.format_exc()



            
################################################################################
################################################################################
################################################################################
##class chatServer. Built to represent the chat server for centre chatroom.
##the server now has the functionality of adding a client to the chatroom
##and deleting a client from the chat.
##the server can also receive the message from client and broadcast with
##handle of loss.
class ChatServer:
    def __init__(self,port):
        """Constructor of the chat server class. Takes in only one parameter that is the port of the server"""
        self.serverPort = port
        self.clientList = []
        self.messageQueue = []
        self.serverSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.serverSocket.bind(('',self.serverPort))
        self.waitForAckList = []
        self.allMessages = []
        self.lock = threading.RLock()


    def getWaitForAckList(self):
        """returns the list of client that have not send ACK back"""
        return self.waitForAckList

    def getAllMessages(self):
        """returns the list of all handle and message tuple that had been successfully sent out"""
        with self.lock:
            return self.allMessages

    def getServerSocket(self):
        """returns the server socket"""
        return self.serverSocket
    
    def getMessageQueue(self):
        """returns the list of handle and message tuples that awaits to be sent"""
        return self.messageQueue
    
    def getClients(self):
        """returns a alphabetical sorted list of handles of the clients"""
        cl = []
        with self.lock:
            for client in self.clientList:
            #0 is address, 1 is handle, 2 is server seq, 3 is expected seq, 4 is timeoutTimes
                cl.append(client[1])
        cl.sort()
        return cl

    def getKeyWord(self,message):
        """returns the keyword from the message that is passed in"""
        index = message.find("\n")
        keyword = message[:index]
        return keyword

    def getHandle(self,message):
        """returns the handle from the message"""
        index = message.find("\n")
        handle = message[index+1:message.find("\n",index+1)]
        return handle

    def getSeq(self,message):
        """returns the sequence number from the message"""
        index = message.find("\n")
        index = message.find("\n",index+1)
        seq =  message[index+1:message.find("\n",index+1)]
        return eval(seq)

    def getBody(self,message):
        """returns the entity body of the message"""
        index = message.find("\n\n")
        body = message[index+2:]
        return body

    
    def updateExpectSeq(self, clientAddress):
        """updates the expected sequence number from a particular client with specific client address"""
        with self.lock:
            for i in range(len(self.clientList)):
                if self.clientList[i][0]==clientAddress:
                    break
            client = self.clientList[i]
            client = (client[0],client[1],client[2],(client[3]+1)%1024,client[4])
            self.clientList[i] = client

    def updateServerSeq(self,clientAddress):
        """updates the server sequence number that should be used of a particular client"""
        with self.lock:
            for i in range(len(self.clientList)):
                if self.clientList[i][0]==clientAddress:
                    break
            client = self.clientList[i]
            client = (client[0],client[1],(client[2]+1)%1024,client[3],client[4])
            self.clientList[i] = client


    def updateTimeOutTime(self,clientAddress):
        """updates the number of timeout that has occured to a particular client with a specific client address"""
        for i in range(len(self.getWaitForAckList())):
            if self.getWaitForAckList()[i][0]==clientAddress:
                break
        client = self.getWaitForAckList()[i]
        client = (client[0],client[1],client[2],client[3],client[4]+1)
        self.getWaitForAckList()[i] = client
        with self.lock:
            for i in range(len(self.clientList)):
                if self.clientList[i][0]==clientAddress:
                    break
            client = self.clientList[i]
            client = (client[0],client[1],client[2],client[3],client[4]+1)
            self.clientList[i] = client


    def checkClientExist(self, clientAddress):
        """checks if one client is already in the chatroom. returns True if this client is recorded, False if not."""
        with self.lock:
            for client in self.clientList:
                if client[0]== clientAddress:
                    return True
            return False

    def removeClient(self,clientAddress):
        """removes a client from the chatroom."""
        with self.lock:
            index = 0
            for client in self.clientList:
                if client[0]== clientAddress:
                    break
                else:
                    index = index+1
            self.clientList = self.clientList[:index] + self.clientList[index+1:]

    def removeClientFromWaitList(self,clientAddress):
        """removes a client with a specific client address from the list of clients that has not send ACK back"""
        index = 0
        for client in self.waitForAckList:
            if client[0]== clientAddress:
                break
            else:
                index = index+1
        self.waitForAckList = self.waitForAckList[:index] + self.getWaitForAckList()[index+1:]
            
    def broadcast(self):
        """sends out broadcast to all clients and adds the clients to the waitForAckList"""
        handleMessageTuple = self.getMessageQueue()[0]
        for client in self.clientList: 
            message = "SEND\n%s\n%d\n\n%s"%(handleMessageTuple[0],client[2],handleMessageTuple[1])
            lossySend(self.serverSocket, message,client[0],50)
##            self.serverSocket.sendto(message,client[0])
            self.waitForAckList.append(client)            
        print "Finished Sending Broadcast messages to All Clients."

    def getClient(self,clientAddress):
        """returns the client of a specific client address from the clientList"""
        with self.lock:
            for client in self.clientList:
                if client[0]== clientAddress:
                    return client
            return None
        
            
         
    def startStage(self):
        """state 0, server waits for messages from the clients, and responds accordingly. Returns to this stage after a message is processed."""
        print "Server: ready to respond"
        readReady,outputready,exceptReady = select.select([self.getServerSocket()],[],[])
        if readReady!=[]:
            message, clientAddress = self.serverSocket.recvfrom(1500)
            if self.getKeyWord(message) == "CONNECT":
                lossySend(self.serverSocket, "ACK\n%d\n\n"%(self.getSeq(message)),clientAddress,50)
##                self.serverSocket.sendto("ACK\n%d\n\n"%(self.getSeq(message)),clientAddress)
                
                if self.checkClientExist(clientAddress):
                    print "Already added " + self.getHandle(message)+"!!"
                else:
                    with self.lock:
                        self.clientList.append((clientAddress,self.getHandle(message),0,1,0))
                    print "Server: Added Client "+self.getHandle(message) + " to chat."
                return 0
            elif self.getKeyWord(message) == "DISCONNECT":
                lossySend(self.serverSocket, "ACK\n%d\n\n"%(self.getSeq(message)),clientAddress,50)
##                self.serverSocket.sendto("ACK\n%d\n\n"%(self.getSeq(message)),clientAddress)
                if not self.checkClientExist(clientAddress):
                    print "Already removed " + self.getHandle(message)+"!!"
                else:
                    self.removeClient(clientAddress)
                    print "Server: "+ self.getHandle(message)+ " is removed successfully."
                return 0
            elif self.getKeyWord(message) == "SEND":
                if self.getSeq(message) == self.getClient(clientAddress)[3]:
                    print "Server: received a message from a client"
                    lossySend(self.serverSocket, "ACK\n%d\n\n"%(self.getSeq(message)),clientAddress,50)
##                    self.serverSocket.sendto("ACK\n%d\n\n"%(self.getSeq(message)),clientAddress)
                    self.updateExpectSeq(clientAddress)
                    if len(self.getMessageQueue())==0:
                        self.getMessageQueue().append((self.getHandle(message),self.getBody(message)))
                        self.broadcast()
                        print "Server: broadcasting!!!"
                        return 1
                    else:
                        self.getMessageQueue().append((self.getHandle(message),self.getBody(message)))
                else:
                    lossySend(self.serverSocket, "ACK\n%d\n\n"%(self.getSeq(message)),clientAddress,50)
##                    self.serverSocket.sendto("ACK\n%d\n\n"%(self.getSeq(message)),clientAddress)
                    return 0
        else:
            if len(self.getMessageQueue())!=0:
                self.broadcat()
                return 1
            else:
                return 0



    def broadCastState(self):
        """state 1, waits for the ACKs from all clients and handles the losses by resending the packets"""
        print "Server: waiting for ACKs"
        timeoutLimit = 0.25
        readReady,outputready,exceptReady = select.select([self.getServerSocket()],[],[],timeoutLimit)
        if [readReady,outputready,exceptReady] == [[],[],[]]:
            print "Server: timeout. Resending stuff!!!!!"
            kickoutList = []
            for client in self.waitForAckList:
                self.updateTimeOutTime(client[0])
                if client[4]>1000:
                    kickoutList.append(client)    
            for client in kickoutList:
                self.removeClient(client[0])
                self.removeClientFromWaitList(client[0])
                print "Client %s got kicked out due to too many timeouts"%(client[1])
            for client in self.waitForAckList:
                handleMessageTuple = self.getMessageQueue()[0]
                message = "SEND\n%s\n%d\n\n%s"%(handleMessageTuple[0],client[2],handleMessageTuple[1])
                lossySend(self.serverSocket, message,client[0],50)
##                self.serverSocket.sendto(message,client[0])
            return 1
        else:
            message,clientAddress = self.serverSocket.recvfrom(1500)
            print "Server: received a message send request while waiting for the previous acks"
            if self.getKeyWord(message) == "SEND":
                if self.getSeq(message) == self.getClient(clientAddress)[3]:
                    self.getMessageQueue().append((self.getHandle(message),self.getBody(message)))
                    self.updateExpectSeq(clientAddress)
                lossySend(self.serverSocket, "ACK\n%d\n\n"%(self.getSeq(message)),clientAddress,50)
##                self.serverSocket.sendto("ACK\n%d\n\n"%(self.getSeq(message)),clientAddress)
                return 1
                
            elif self.getKeyWord(message) == "DISCONNECT":
                lossySend(self.serverSocket, "ACK\n%d\n\n"%(self.getSeq(message)),clientAddress,50)
##                self.serverSocket.sendto("ACK\n%d\n\n"%(self.getSeq(message)),clientAddress)
                if not self.checkClientExist(clientAddress):
                    print "Already removed " + self.getHandle(message)+"!!"
                else:
                    self.removeClient(clientAddress)
                    self.removeClientFromWaitList(clientAddress)
                    print "Server: "+ self.getHandle(message)+ " is removed successfully."
            elif self.getKeyWord(message) == "CONNECT":
                lossySend(self.serverSocket, "ACK\n%d\n\n"%(self.getSeq(message)),clientAddress,50)
##                self.serverSocket.sendto("ACK\n%d\n\n"%(self.getSeq(message)),clientAddress)
                if self.checkClientExist(clientAddress):
                    print "Already added " + self.getHandle(message)+"!!"
                else:
                    with self.lock:
                        self.clientList.append((clientAddress,self.getHandle(message),0,1,0))
                    print "Server: Added Client "+self.getHandle(message) + " to chat."
            elif self.getKeyWord(message)== "ACK":
                if self.getSeq(message)== self.getClient(clientAddress)[2]:
                    print "Server: received an ACK from client!!!"
                    self.removeClientFromWaitList(clientAddress)
                    self.updateServerSeq(clientAddress)
                    if (len(self.waitForAckList)==0):
                        self.allMessages.append(self.messageQueue[0])
                        self.messageQueue = self.messageQueue[1:]
                        return 0
            return 1
                
               

    def handleMessages(self):
        """handles the messages that the server received."""
        state = 0;
        try:
            while True:
                if state ==0:
                    state = self.startStage()
                elif state == 1:
                    state = self.broadCastState()
        except Exception, e:
            print traceback.format_exc()
