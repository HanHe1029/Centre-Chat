#!/usr/bin/env python
##Author: Han He
import centrechat
import thread
import time


##This is the tester of the center chat room.
##Tests whether can add construct server, adds clients to the room, and remove 
##clients from the room
def main(port):
    s = centrechat.ChatServer(port)
    thread.start_new_thread(s.handleMessages,())
    
    clientList = []

##    c1 = centrechat.ChatClient("localhost", port, "Han")
    c1 = centrechat.ChatClient("127.0.0.1", port, "Han")
    thread.start_new_thread(c1.handleMessages,())
    clientList.append("Han")
    print

    time.sleep(10)

        
    c2 = centrechat.ChatClient("127.0.0.1", port, "Alison")
    thread.start_new_thread(c2.handleMessages,())
    clientList.append("Alison")
    print

    time.sleep(10)
    
    c3 = centrechat.ChatClient("127.0.0.1", port, "John")
    thread.start_new_thread(c3.handleMessages,())
    clientList.append("John")
    print

    time.sleep(10)

        
    c4 = centrechat.ChatClient("127.0.0.1", port, "Dave")
    thread.start_new_thread(c4.handleMessages,())
    clientList.append("Dave")
    print 

    time.sleep(10)

    clientList.sort()
    print
    print "my list accumulated: ", clientList
    print "list got from server: ",s.getClients()
    print "added all clients: ",
    print s.getClients() == clientList
    assert s.getClients()==clientList
    print 

    time.sleep(10)
    c1.disconnect()
    clientList.remove("Han")
    print

    time.sleep(10)
    print
    clientList.sort()
    print "my list accumulated: ", clientList
    print "list got from server: ",s.getClients()
    print "Lists are the same: ",
    print s.getClients()== clientList
    assert s.getClients()==clientList
    print
    

    time.sleep(10)
    c4.disconnect()
    clientList.remove("Dave")
    print
    
    time.sleep(10)
    print 
    clientList.sort()
    print "my list accumulated: ", clientList
    print "list got from server: ",s.getClients()
    print "Lists are the same: ",
    print s.getClients()== clientList
    print 



    c2.sendMessage("HI!!!")
    time.sleep(10)   
    print "C2 sees:-----------------"
    message = c2.getMessage()
    if not message == None:
        print message[0] + ": "+message[1]
    else:
        print message
    print "-------------------------"

    print "C3 sees:-----------------"
    m2 = c3.getMessage()
    if not m2==None:
        print m2[0] + ": "+m2[1]
    else:
        print m2
    print "-------------------------"
    print 
    assert message==m2 and not message == None



    c3.sendMessage("How are you?!")
    time.sleep(10)
    print "C2 sees:-----------------"
    message = c2.getMessage()
    if not message == None:
        print message[0] + ": "+message[1]
    else:
        print message
    print "-------------------------"

    print "C3 sees:-----------------"
    m2 = c3.getMessage()
    if not m2==None:
        print m2[0] + ": "+m2[1]
    else:
        print m2
    print "-------------------------"
    
    assert message==m2 and not message == None

    c2.sendMessage("Do you want to build a snow man???")
    time.sleep(10)
    print "C2 sees:-----------------"
    message = c2.getMessage()
    if not message == None:
        print message[0] + ": "+message[1]
    else:
        print message
    print "-------------------------"

    print "C3 sees:-----------------"
    m2 = c3.getMessage()
    if not m2==None:
        print m2[0] + ": "+m2[1]
    else:
        print m2
    print "-------------------------"
    print
    assert message==m2 and not message == None
    


    c3.sendMessage("ALOHA")
    time.sleep(10)
    c5 = centrechat.ChatClient("127.0.0.1", port, "Han")
    thread.start_new_thread(c5.handleMessages,())
    clientList.append("Han")
    time.sleep(10)
    print "C2 sees:-----------------"
    message = c2.getMessage()
    if not message == None:
        print message[0] + ": "+message[1]
    else:
        print message
    print "-------------------------"

    print "C3 sees:-----------------"
    m2 = c3.getMessage()
    if not m2==None:
        print m2[0] + ": "+m2[1]
    else:
        print m2
    print "-------------------------"

    print "C5 sees:-----------------"
    m = c5.getMessage()
    if m == None:
        print m
    else:   
        print m[0]+": "+m[1]
    print "-------------------------"
    print 
    assert message==m2 and (not message == None) and m == None




    c2.sendMessage("Yo!!!")
    time.sleep(10)
    print "C2 sees:-----------------"
    message = c2.getMessage()
    if not message == None:
        print message[0] + ": "+message[1]
    else:
        print message
    print "-------------------------"

    print "C3 sees:-----------------"
    m2 = c3.getMessage()
    if not m2==None:
        print m2[0] + ": "+m2[1]
    else:
        print m2
    print "-------------------------"

    print "C5 sees:-----------------"
    m = c5.getMessage()
    if not m==None:
        print m[0]+": "+m[1]
    else:
        print m
    print "-------------------------"
    print 
    assert message==m2 and message == m and not message == None

    

    c5.sendMessage("Computer science ROCKs!!!!")
    time.sleep(10)
    c5.disconnect()
    clientList.remove("Han")
    time.sleep(10)
    print "C2 sees:-----------------"
    message = c2.getMessage()
    if not message==None:
        print message[0] + ": "+message[1]
    else:
        print message
    print "-------------------------"

    print "C3 sees:-----------------"
    m2 = c3.getMessage()
    if not m2==None:
        print m2[0] + ": "+m2[1]
    else:
        print m2
    print "-------------------------"
    print 
    assert message==m2 and not message == None

    print
    print "HISTORY:"
    for message in s.getAllMessages():
        print message[0]+": "+message[1]

main(8083)
