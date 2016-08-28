''' Hub Data Decoder
Started 21.8.16
Reads a LoRa data packet and decodes it.

'''

# constants that will not change in program
# command bytes that are used by LoRa module
DataToSendRequest = 0x34
ClearToSendData = 0x35
DataPacketandReq = 0x36
DataPacketFinal = 0x37
Ping = 0x32

# initialise global variables for data packet. Defined here so that they are global
Packet = []         # start with empty packet
# pointers in packet
StartHubAddr = 0    # poisiton in packet where hub addr starts
StartELBAddr = 5    # posiiton in packet where ELB starts
StartCommand = 10   # posiiton of command byte
StartPayloadLength = 11     # position of payload length byte
StartPayload = 12   # poition of start of payload
#TODO - check thees pointers are true of ping, request to send and data packets
Command = 0         # default value fo rcommand

# initialise variables
ComsIdle = True     # set to false when an initial RequestToSendData has been received.
CurrentELB = "0000" # when coms has started this variable holds the ELB addr that we are talking to
                    # all others will be ignored.
PacketReceived = False  # set true when a packet has been received - trigger write operation.



def GetModuleData():
    # function to get data from LoRa module
    # need to wait here until we have data

    '''
    HubAddr = "00000"   
    ELBAddr = "1234!"
    Command = Ping
    PayloadLength = 30
    PayloadBytes = [0x80,0x00,0x30,0x45,0x12,0x25,0x12,0x15,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x11,0x22,0x33,0x44,0x11,0x22,0x33,0x22,0x45,0x67,0x56,0x78,0x03,0xA4]
    '''
    # this is a data packet - Packet = ['0','0','0','0','1','2','3','4','!',Command,PayloadLength,0x80,0x00,0x30,0x45,0x12,0x25,0x12,0x15,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x11,0x22,0x33,0x44,0x11,0x22,0x33,0x22,0x45,0x67,0x56,0x78,0x03,0xA4]   # build packet
    # ping packet
    Packet = ['0','0','0','0','!','1','2','3','4','!',Ping]

    # need to put data validation here

    '''
    with open("F:\\Users\Duncan\Documents\Dropbox\Pace_Bostin\CognIoT\SinglePacket.txt", "rb") as f:
    byte = f.read(1)
    while byte != b"":
        # Do stuff with byte.
        byte = f.read(1)
    '''
    return (Packet)
    # return the data from the get data function

def WriteLogFile(LogFileName, PayloadBytes):
    # write log file
    LogFile = open("Log" + ELBAddr[:4] +"yymmddhhmmss.txt","w")
    for i in PayloadBytes:
        LogFile.write(str(i))
    LoogFile.close()

def RespondToPing(Packet):
    # responds to the ping command.
    # global variables cotain the addresses
    print ("in respond to ping")

def RespondDataToSend(Packet):
    # responds to the Data to Send Request
    print ("in respond to data to send")

def RespondDataPacketandReq(Packet):
    # data packet received and further data is on its way
    print ("in respond to data packet received and another to follow")

def RespondDataPacketFinal(Packet):
    # data packet received and no more to come
    print ("in respond to last data packet")

def UnrecognisedCommand():
    # send relevant Nack.
    print ("in respond to unrecognised")
    

    

while True:
    '''
    The struture of the main loop is to loop forever getting data and then processing it.
    3 variables indicate if
        coms is idle - no conversation has been started
        a packet has been received - data received, validated and acked. Ready to write
        who we are talking to - the ELB address that has started a conversation
    '''
    print ("in main loop")
    Packet = GetModuleData()
         # waits in Get data until we have now received a packet from the radio module and it has been checked for validity
    print ("S"+str(Packet[StartCommand:StartCommand+1])+"E")
    Command = Packet[StartCommand:StartCommand+1]   # extract command byte
    # Test = int(Packet[StartCommand:StartCommand+1])
    #BUG command is a list element and not a number
    if ComsIdle:     # not yet in communication with an ELB
        print ("ComsIdle = False")
        if Command == [Ping]:
            print ("ping")
        #    RespondToPing()     # respond to a ping command
        elif Command == [DataToSendRequest]:
            print ("DataToSendRequest")
            RespondDataToSend(Packet)
            # this will send CleartoSendData.
            # will also set ComsIdle to false and CurrentELB to the addr of the ELB we are talking to
            # we will be back through this loop with the data packets
        else:
            UnrecognisedCommand()
    elif Command == [DataPacketandReq]: # coms has started and received data packet with more to follow
        RespondDataPacketandReq(Packet)
    elif Command == [DataPacketFinal]: # coms has started and received final data packet
        RespondDataPacketFinal(Packet)
    else:
        UnrecognisedCommand()
    
