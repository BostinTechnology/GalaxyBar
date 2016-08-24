/*
 * NFCReader.c
 *
 * Copyright 2016  <pi@R-Pi-01>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 *
 *
 */


#include <stdio.h>   // Standard input/output definitions
#include <string.h>  // String function definitions
#include <unistd.h>  // UNIX standard function definitions
#include <fcntl.h>   // File control definitions
#include <errno.h>   // Error number definitions
#include <termios.h> // POSIX terminal control definitions



#include <wiringPi.h>
#include <wiringSerial.h>

#define GPIO17 0        // This defines the GPIO reference for wiringPi
#define GPIO18 1        // This defines the GPIO reference for wiringPi

#define GPIO GPIO17


// Define global variables

int fd; // File handle for connection to the serial port.


// Helper functions

void WaitForCTS()
{
    // Generic call to wait for the CTS going high
    // CTS is implemented via the use of the GPIO as the UART on the
    // Pi doen't have any control lines.
    serialFlush(fd);

    while (digitalRead(GPIO) == HIGH)
    {
        // Do Nothing
        //printf(".");
    }

}

void GetTextResult()
{
    // Generic routine to return text from the serial port.

    while (serialDataAvail (fd))
    {
        printf ("%c", serialGetchar (fd)) ;
        fflush (stdout) ;
    }
    //printf("\n\n");
}





int main ()
{
//


// Initialise WiringPi so we can use the GPIO on the Raspberry Pi

 if (wiringPiSetup () == -1)
  {
    fprintf (stdout, "Unable to start wiringPi: %s\n", strerror (errno)) ;
    return 1 ;
  }

// The PirFix can use one of the following GPIO pins configured as an input
//
// GPIO17
// GPIO18
// GPIO21
// GPIO22
//

  pinMode(GPIO,INPUT);  // We are using GPIO as the pin to identify the "CTS" function



  if ((fd = serialOpen ("/dev/ttyUSB1", 57600)) < 0)  // Try to open a connection to the serial port
  {
   fprintf (stderr, "Unable to open serial device: %s\n", strerror (errno)) ;
    return 1 ;
  }
  else
  {
    // We have opened communications with the onboard Serial device

    printf("Opened communications with Modem.\n");  // Communications opened successfully

    struct termios options ;
    int rc;

   // Get the current options for the port
    if((rc = tcgetattr(fd, &options)) < 0){
        fprintf(stderr, "failed to get attr: %d, %s\n", fd, strerror(errno));
    }

    // Set the baud rates to 230400
    cfsetispeed(&options, B57600);

    // Set the baud rates to 230400
    cfsetospeed(&options, B57600);

    cfmakeraw(&options);
    options.c_cflag |= (CLOCAL | CREAD);   // Enable the receiver and set local mode
    options.c_cflag &= ~PARENB;             // No parity bit
    options.c_cflag &= ~CSTOPB;             // 1 stop bit
    options.c_cflag &= ~CSIZE;              // Mask data size
    options.c_cflag |=  CS8;                // Select 8 data bits
    options.c_cc[VMIN]  = 1;
    options.c_cc[VTIME] = 2;

    // Set the new attributes
    if((rc = tcsetattr(fd, TCSANOW, &options)) < 0){
        fprintf(stderr, "failed to set attr: %d, %s\n", fd, strerror(errno));
    }

  }




char option;


do {
    printf(" \n\n");
    printf("**************************************************************************\n");
    printf("Available commands: -\n\n");
    printf("R - Reset LoRa Modem and display version information\n");
    printf("m - Monitor Mode - listen for packets\n");
    printf("e - Exit program \n");
    printf(" \n");

    printf("Please select command -> ");

    option = getchar();
    getchar();  // have to press enter and this consumes the enter character


       switch (option)
       {

            case 'R': // Read the firmware version

            printf("\nReset Modem and Read Firmware Details\n\n");

            //WaitForCTS();

            serialPrintf(fd, "AT!!\n\0");

            delay(100); // ??? Need to wait otherwise the command does not work

            GetTextResult();

            serialPrintf(fd, "sloramode 1\n\0");

            delay(100); // ??? Need to wait otherwise the command does not work

            GetTextResult();

            break;


        case 'm':

            printf("\nListening for Packets ....\n");
            while (1)
            {
                serialPrintf(fd, "\ngeta\0");

                delay(100); // ??? Need to wait otherwise the command does not work

                GetTextResult();



            }



        case 'e':
            printf("Exiting.......\n");
        option = 'e';
        break;

        default:
        printf("Unrecognised command!\n");


       }

       fflush (stdout) ;

     } while(option != 'e');

     serialClose(fd);

return(0);

}



