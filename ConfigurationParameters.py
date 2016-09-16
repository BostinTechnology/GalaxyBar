'''
Configuration File

Only change values in the User Configuration Section

'''

import logging
import datetime


'''
  --------------------------------------------
  -    U S E R   C O N F I G U R A T I O N   -
  --------------------------------------------

These values are tunable by the user
'''

# Used to determine how much data is to be captured within the logging function
# A new logging file is created each time the program starts
# Possible levels are below, the uncomment one is in use


#DEBUG_LEVEL = logging.critical
#DEBUG_LEVEL = logging.error
DEBUG_LEVEL = logging.warning
#DEBUG_LEVEL = logging.info
#DEBUG_LEVEL = logging.debug


# Time window parameters
# Outside of these times, all messagesd except PING are ignored
# 00:00:00 --- START_COMMS_TIME ======== STOP_COMMS_TIME ------------------------------------------- 23:59:59
# Values to be in the format HH:MM:SS, leading zero's are rerquired
#
#   START & STOP times must NOT cross midnight else defaults of 1am till 5am will be used.
#

START_TIME = '08:00:00'
STOP_TIME = '22:00:00'

print("Comms Time Window From:%s To:%s" % (START_TIME, STOP_TIME))

'''
  --------------------------------------------
  - S Y S T E M    C O N F I G U R A T I O N -
  --------------------------------------------

These values are not normally changed by the user
'''


# The delay between send and receive of data using the UART to the LoRa module
# This is not a delay between messages, but the UART level comms
SRDELAY = 0.1

# The delay between receiving one message via the LoRa module and sending the next message
# Typically used when configuring the LoRa module
INTERDELAY = 0.2

# The delay applied after a failed message has been received. This could be either a
# fail to send or a failed response
FAILDELAY = 0.5

# The connected GPIO pin to indicate when the LoRa module has data to read
INPUT_PIN = 17

# The minimum length of a valid packet to be received from the LoRa module
MIN_LENGTH = 11

# During processing of LoRa messages, there is a timeout to determine if the message is old
# This is measured in seconds
COMMS_TIMEOUT = 2



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
        return
    except:
        return False

#Validate the time given above
# Check for
#   valid times
#   Stop being after start

if ValidateTime(START_TIME):
    START_COMMS_TIME = datetime.datetime.strptime(START_TIME, "%H:%M:%S")
    print("Start OK")
else:
    print("Start Time in Configuration File - ConfigurationParameters - is invalid, default being used")
    START_COMMS_TIME = datetime.datetime.strptime('01:00:00', "%H:%M:%S")

if ValidateTime(STOP_TIME) == False:
    STOP_COMMS_TIME = datetime.datetime.strptime(STOP_TIME, "%H:%M:%S")
    print("Stop OK")
else:
    print("Stop Time in Configuration File - ConfigurationParameters - is invalid, default being used")
    STOP_COMMS_TIME = datetime.datetime.strptime('05:00:00', "%H:%M:%S")

if (STOP_COMMS_TIME - START_COMMS_TIME).total_seconds() < 0:
    print("Time in Configuration File - ConfigurationParameters - Stop Time is after start time, default being used")
    START_COMMS_TIME = datetime.datetime.strptime('01:00:00', "%H:%M:%S")
    STOP_COMMS_TIME = datetime.datetime.strptime('05:00:00', "%H:%M:%S")
else:
    print("Stop after start")


# Check Debug level
dbg = 0
try:
    dbg = DEBUG_LEVEL
except:
    dbg = 0

#BUG: dbg iois beign set to a function, not the value of the logging level"!
if dbg < 1:
    DEBUG_LEVEL = logging.warning


# Only used to validate this program
if __name__ == "__main__":
    """
    This is the main entry point for the program when it is being run independently.

    """

#    CheckEntries()
