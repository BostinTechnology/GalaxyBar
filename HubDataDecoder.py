''' Hub Data Decoder
Started 21.8.16
Reads a LoRa data packet from a file and decodes it
'''

# initialise global variables for data packet. Defined here so that they are global
HubAddr = "0000!"   # the address of this hub
ELBAddr = "0000"    # the default value for the ELB address
PayloadLength = 0   # Default length of payload
PayloadBytes = []   # default contents of data

# command bytes
DataToSendRequest = 0x34
ClearToSendData = 0x35
DataPacketandReq = 0x36
DataPacketFinal = 0x37

'''
with open("F:\\Users\Duncan\Documents\Dropbox\Pace_Bostin\CognIoT\SinglePacket.txt", "rb") as f:
    byte = f.read(1)
    while byte != b"":
        # Do stuff with byte.
        byte = f.read(1)
'''

while (1):
    # main progam loop
    GetData()
    if Command = DataToSendRequest:
        RespondDataToSend()
    elif Command = DataPacketandReq:
        RespondDataPacketandReq()
    elif Command = DataPacketFinal
        RespondDataPacketFinal()
    else:
        UnrecognisedCommand()
        


def GetData():
    # function to get data from LoRa module
    
    ELBAddr = "1234!"
    Command = 0x36
    PayloadLength = 30
    PayloadBytes = [0x80,0x00,0x30,0x45,0x12,0x25,0x12,0x15,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x11,0x22,0x33,0x44,0x11,0x22,0x33,0x22,0x45,0x67,0x56,0x78,0x03,0xA4]

    return (ELBAddr,Command, PayloadLength, PayloadBytes)
    # return the data from the get data function

def WriteLogFile(LogFileName, PayloadBytes):
# write log file
    LogFile = open("Log" + ELBAddr[:4] +"yymmddhhmmss.txt","w")
    for i in PayloadBytes:
        LogFile.write(str(i))
    LoogFile.close()
