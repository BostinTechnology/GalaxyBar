'''
Configuration File

Only change values in the User Configuration Section

'''

import logging
import datetime

print("\n\n")
print("     ========================================================================")
print("     |                                                                       |")
print("     |                   B O S T I N   T E C H N O L O G Y                   |")
print("     |                                                                       |")
print("     |                         in conjuntion with                            |")
print("     |                                                                       |")
print("     |           A F R I C I A N   W A T E R   E N T E R P R I S E S         |")
print("     |                                                                       |")
print("     |                                                                       |")
print("     ========================================================================")
print ("\n\n\n\n")
print("This program is copywrite of CognIot, a trading name of Bostin Technology\n\n")


'''
  --------------------------------------------
  -    U S E R   C O N F I G U R A T I O N   -
  --------------------------------------------

These values are tunable by the user
'''

# Used to determine how much data is to be captured within the logging function
# A new logging file is created each time the program starts
# Possible levels are below, the uncomment one is in use


LOGGING_LEVEL = "CRITICAL"
#LOGGING_LEVEL = "ERROR"
#LOGGING_LEVEL = "WARNING"
#LOGGING_LEVEL = "INFO"
#LOGGING_LEVEL = "DEBUG"


# Time window parameters
# Outside of these times, all messagesd except PING are ignored
# 00:00:00 --- START_COMMS_TIME ======== STOP_COMMS_TIME ------------------------------------------- 23:59:59
# Values to be in the format HH:MM:SS, leading zero's are rerquired
#
#   START & STOP times must NOT cross midnight else defaults of 1am till 5am will be used.
#

START_TIME = '01:00:00'
STOP_TIME = '05:00:00'

# Set this to True or False to determine if the time parameters above are to be used.
USE_TIME = True
#USE_TIME = False

# Information that is related to the EWC
# These values are used in the calculations for the data file

TAP_ID = 1

POLLING_RATE = 2

FLOW_CONVERSION = 600












'''
  --------------------------------------------
  - S Y S T E M    C O N F I G U R A T I O N -
  --------------------------------------------

These values are not normally changed by the user
'''


# The delay between send and receive of data using the UART to the LoRa module
# This is not a delay between messages, but the UART level comms
SRDELAY = 0.01

# The delay between receiving one message via the LoRa module and sending the next message
# Typically used when configuring the LoRa module
INTERDELAY = 0.02

# The delay applied after a failed message has been received. This could be either a
# fail to send or a failed response
FAILDELAY = 0.03

# The connected GPIO pin to indicate when the LoRa module has data to read
INPUT_PIN = 17

# The minimum length of a valid packet to be received from the LoRa module
MIN_LENGTH = 11

# During processing of LoRa messages, there is a timeout to determine if the message is old
# This is measured in seconds
COMMS_TIMEOUT = 2

#Read and set the MAC address for use by the LogFileWriter

try:
    sys = open('/sys/class/net/eth0/address').read()
except:
    sys = '00:00:00:00:00:00'
    logging.warning("[LFR] - Reading of the MAC address from system file failed")
logging.debug("[LFR] - MAC Address captured (all zero's is a failure):%s" % sys)
mac = sys.replace(':','')
MACADDRESS = mac[0:12]



'''
  --------------------------------------------
  - U S E R   D A T A   V A L I D A T I O N  -
  --------------------------------------------

This section validates the data entered by the user and sets defaults if it is invalid
'''

# Time Parameters Validation
def ValidateTime(given):
    # Validate the give time to the defined format
    try:
        datetime.datetime.strptime(given, "%H:%M:%S")
        return True
    except:
        return False

#Validate the time given above
# Check for
#   valid times
#   Stop being after start

if ValidateTime(START_TIME):
    START_COMMS_TIME = datetime.datetime.strptime(START_TIME, "%H:%M:%S")
    #print("Start OK")
else:
    print("Start Time in Configuration File - Settings.py - is invalid, default being used")
    START_COMMS_TIME = datetime.datetime.strptime('01:00:00', "%H:%M:%S")

if ValidateTime(STOP_TIME):
    STOP_COMMS_TIME = datetime.datetime.strptime(STOP_TIME, "%H:%M:%S")
    #print("Stop OK")
else:
    print("Stop Time in Configuration File - Settings.py - is invalid, default being used")
    STOP_COMMS_TIME = datetime.datetime.strptime('05:00:00', "%H:%M:%S")

if (STOP_COMMS_TIME - START_COMMS_TIME).total_seconds() < 0:
    print("Time in Configuration File - Settings.py - Stop Time is after start time, default being used")
    START_COMMS_TIME = datetime.datetime.strptime('01:00:00', "%H:%M:%S")
    STOP_COMMS_TIME = datetime.datetime.strptime('05:00:00', "%H:%M:%S")


# Check logigng level
LG_LVL = getattr(logging, LOGGING_LEVEL.upper(), None)
if not isinstance(LG_LVL, int):
    LG_LVL = logging.critical


print("Comms Time Window From:%s To:%s" % (START_TIME, STOP_TIME))

logging_levels = {50:"CRITICAL", 40:"ERROR", 30:"WARNING", 20:"INFO", 10:"DEBUG"}
if LG_LVL in logging_levels:
    print("Loggin Level in use: %s" % logging_levels[LG_LVL])
else:
    LG_LVL = logging.critical


