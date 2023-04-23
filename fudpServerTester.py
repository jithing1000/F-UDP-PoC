#!/usr/bin/env python
#cfe: This program (server) receives data from a client and stitches the fragmented--
#     --UDP packets together following F-UDP on Layer 7.

"""
THIS PROGRAM IS A DEMONSTRATION OF THE F-UDP CONCEPT.
THIS IS A CRUDE IMPLEMENTATION. 
IT IS NOT RECOMMENDED TO USE THIS FILE IN PART/FULL ON A PROJECT.
"""

# Imports.
import socket

# Macros.
BUF_SIZE         = 0xFFFF
LOCAL_UDP_IP     = "172.31.107.73"
# Unassigned UDP port range: ~ (49152-65535)
LOCAL_UDP_PORT   = 53000
localAddressPort = (LOCAL_UDP_IP, LOCAL_UDP_PORT)

if __name__ == "__main__":
    # Create UDP socket.
    UDPServerSocket  = socket.socket (family = socket.AF_INET, type = socket.SOCK_DGRAM)

    # Bind to IP and port.
    UDPServerSocket.bind (localAddressPort)

    print ("Listening for incoming messages. . .")
    
    expAuthID = BUF_SIZE
    expSeqID = 0x00
    msgFromClient = []
    packetFragments = BUF_SIZE

    # This is indefinite.
    """
    DEFECT NOTE: LOOP WILL NOT TERMINATE UNTIL A COMPLETE SEQUENCE IS RECEIVED!
    TODO: FIX ME!
    """
    while (True):
        # Listen for incoming datagrams.
        bytesAddressPair = UDPServerSocket.recvfrom (BUF_SIZE)

        msgFragment = bytesAddressPair[0]
        clientAddr = bytesAddressPair[1]

        clientIP  = "Received msg from IP, port: {}".format(clientAddr)
        
        # Check F-UDP header for data:
        """
        2 bytes - 16-bit AUTH Key
        2 bytes - Sequence ID
        2 bytes - Total Fragments
        """
        recAuthID = ((msgFragment[0x00] & 0x00FF) << 0x08) | (msgFragment[0x01] & 0x00FF)
        recSeqID = ((msgFragment[0x02] & 0x00FF) << 0x08) | (msgFragment[0x03] & 0x00FF)
        # Ascertain if this is the first sequence to set authenticator and read total expected fragments.
        if 0x00 == recSeqID:
            expAuthID = recAuthID
            packetFragments = ((msgFragment[0x04] & 0x00FF) << 0x08) | (msgFragment[0x05] & 0x00FF)
            
        if expAuthID == recAuthID:
            # Check if a sequence is dropped by UDP.
            if expSeqID != recSeqID:
                raise ValueError ("Packet lost in transit. Discarding entire payload. . .")
            
            if 0x00 == recSeqID:
                msgFromClient = msgFragment[0x06 : ]
            else:
                msgFromClient += msgFragment[0x04 : ]
            
            # Break out if all expected fragments have been received.
            if (packetFragments - 0x01) == recSeqID:
                break
            
            expSeqID += 0x01
    
    print ("UDP Payload: ")
    print (" ".join(format(each, '02x') for each in msgFromClient))