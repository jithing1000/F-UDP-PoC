#!/usr/bin/env python
#cfe: This program (client) sends custom data to a server by fragmenting UDP packets--
#     --following F-UDP on Layer 7.

"""
THIS PROGRAM IS A DEMONSTRATION OF THE F-UDP CONCEPT.
THIS IS A CRUDE IMPLEMENTATION. 
IT IS NOT RECOMMENDED TO USE THIS FILE IN PART/FULL ON A PROJECT.
"""

# Imports.
import socket
from random import choices
from math import ceil

# Macros.
REMOTE_UDP_IP      = "172.31.107.73"
# Unassigned UDP port range: ~ (49152-65535)
REMOTE_UDP_PORT    = 53000
serverAddressPort  = (REMOTE_UDP_IP, REMOTE_UDP_PORT)
"""
Max packet size is set to 65467.
65535 (IPv4 max length) - 60 (max IPv4 header size) - 8 (UDP header size) = 65467.
Never set this to less than 8 bytes - we do not want to split F-UDP header!
"""
MAX_PACKET_SIZE    = 65467
"""
Arbitrary limitation - theoretical F-UDP limitaion is infinity.
The below limitation sets max payload size to (MAX_SEQ_SIZE * MAX_PACKET_SIZE).
For sequence size greater than 0xFFFF, modify program to assign additional bytes to--
--sequence ID field. 
Modify as seen fit. 
"""
MAX_SEQ_SIZE       = 0xFFFF
"""
Arbitrary limitation - theoretical F-UDP limitaion is infinity.
The below limitation sets max "actual" data size accounting for F-UDP header size.
"""
FRAME1_HEADER_SIZE = 0x06
FRAMEX_HEADER_SIZE = 0x04
HEADER_SIZES_DIFF  = FRAME1_HEADER_SIZE - FRAMEX_HEADER_SIZE
MAX_DATA_SIZE      = ((MAX_SEQ_SIZE * (MAX_PACKET_SIZE - FRAMEX_HEADER_SIZE)) \
                        - HEADER_SIZES_DIFF)

"""
Name: sendPacket
Function: Send packet to server.
Input: Packet to be sent.
Output: Nil.
Remark: Nil.
"""
def sendPacket (msgFromClient):
    # Send to server.
    udpClientSocket.sendto (bytes(msgFromClient), serverAddressPort)

    # Print confirmation.
    print ("Data sent to IP: " + REMOTE_UDP_IP + ", port: " + str(REMOTE_UDP_PORT) + " ! ! !")

"""
Name: fragmentAndTx
Function: Fragment input message buffer following F-UDP.
Input: Message buffer to be sent.
Output: Nil.
Remark: Nil.
"""
def fragmentAndTx (msgFromClient):
    totalPayloadLen = len(msgFromClient)
    # Check if payload length is feasible with imposed limitation.
    if MAX_DATA_SIZE < totalPayloadLen:
        raise ValueError ("This payload is obese. Try cutting down on cheese.")
    
    # Estimate the total payload length.
    # NOTE: This estimation is not accurate! 
    # TODO: Fix total payload length calculation.
    totalPayloadLen = (totalPayloadLen + ((ceil ((totalPayloadLen + FRAME1_HEADER_SIZE) \
                        / MAX_PACKET_SIZE)) * FRAMEX_HEADER_SIZE) + HEADER_SIZES_DIFF)
    """
    DEFECT NOTE: THIS IS INACCURATE IN CERTAIN CASES!
    TODO: FIX ME!
    """
    packetFragments = ceil (totalPayloadLen / MAX_PACKET_SIZE)

    # Add F-UDP header for frame 1:
    """
    2 bytes - 16-bit AUTH Key
    2 bytes - Sequence ID
    2 bytes - Total Fragments
    """
    # Generate authentication key.
    authKey = choices (range(0x00, 0xFF), k = 0x02)
    # Create F-UDP header with addn data.
    fUDPHeader = authKey + [0x00, 0x00, (packetFragments >> 0x08) & 0x00FF, packetFragments & 0x00FF]
    msgFromClient = fUDPHeader + msgFromClient
    # Reset totalPayloadLen with length of current msgFromClient.
    # Crude handling to negate estimation errors and ensure real-time tracking.
    totalPayloadLen = len(msgFromClient)
    
    if 0x01 >= packetFragments:
        sendPacket (msgFromClient)
    else:
        sequenceID = 0x01
        byteCounter = 0x00
        
        while byteCounter < totalPayloadLen:
            msgEoLPointer = byteCounter + MAX_PACKET_SIZE
            if msgEoLPointer > totalPayloadLen:
                msgFragment = msgFromClient[byteCounter : totalPayloadLen]
            else:
                msgFragment = msgFromClient[byteCounter : msgEoLPointer]
            sendPacket (msgFragment)
            
            # Add F-UDP sequence counter for consecutive frames:
            """
            2 bytes - 16-bit AUTH Key
            2 bytes - Sequence ID
            """
            msgFromClient[msgEoLPointer : msgEoLPointer] = authKey + [(sequenceID >> 0x08) & 0xFF, \
                                                            sequenceID & 0xFF]
            if (msgEoLPointer < totalPayloadLen):
                totalPayloadLen = len(msgFromClient)
            
            byteCounter += MAX_PACKET_SIZE
            sequenceID += 0x01
            
"""
Name: main
Function: This is the main call.
Input: Nil.
Output: Nil.
Remark: Nil.
"""            
if __name__ == "__main__":
    # Create UDP socket.
    udpClientSocket = socket.socket (family = socket.AF_INET, type = socket.SOCK_DGRAM)

    # Custom msg:
    msgFromClient = choices (range(0x00, 0xFF), k = 100000)
    print (" ".join(format(each, '02x') for each in msgFromClient))
    
    # F-UDP:
    fragmentAndTx (msgFromClient)
    
    