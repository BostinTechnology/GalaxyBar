# GalaxyBar
ELBs and HUBs

For more information contact BostinTechnology (www.BostinTechnology.com) or email support@bostintechnology.com

Within this library are the following software
  LoRaCommsReceiver - Manage and process data to and from the LoRa module located on the Hub board
  HubDataDecoder    - Comms layer to receive and respond to messages from the ELB
                      - Includes functionality to enable time based transmissions
  ConfigurationSettings - Location where all the settings are stored outside of the main code base
  ELBReplicator - A python program to emulate the comms from the ELB to test the hub
  AutoStart.sh  - An autostart script to ensure the program starts and runs from bootup
  LoRaPacketWriter  - A program to write a file of the correct format
  LogFileWriter   - Given the data from the ELB write a log file for transmission
  LoRaMonitor     - A program using the 7" display that sows data packets travelling between LoRa modules.
  
