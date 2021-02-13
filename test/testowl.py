#!/usr/bin/python3
#
# Test code to validate that the OWL intuition device is effectively
# sending data to the configured port
#
# Ported from https://github.com/glpatcern/domotica/blob/master/demos/owlintuition.py

import socket
import sys
import select
#from xml.etree import ElementTree as ET

port = 3200

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    sock.bind((socket.gethostbyname(socket.getfqdn()), port))
except socket.error as err:
    print("Unable to bind on port %d: %s" % (port, err))
    sys.exit(1)

print("Listening for OWL data on port %d" % port)
while True:
    readable, _, _ = select.select([sock], [], [], 5)
    if readable:
        data, addr = sock.recvfrom(1024)
#       xml = ET.fromstring(data)
        print(data)
        print("\n\n")
#       etxml = ET.ElementTree(xml)
#       for e in etxml.iter():
#           print "%s: '%s'" % (e.tag, e.text)
#        curr1 = (xml.find(".//curr/..[@id='0']"))[0].text
#        curr2 = (xml.find(".//curr/..[@id='1']"))[0].text
#        curr3 = (xml.find(".//curr/..[@id='2']"))[0].text
#        print curr1, curr2, curr3
