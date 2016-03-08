#!/usr/bin/python

import socket
import time
import datetime
import sys

serverIP = "149.171.37.149" ### CHANGE SERVER IP ADDRESS HERE  ####
#serverIP = "127.0.0.1"
serveraddress = (serverIP, 9999) ###  CHANGE SERVER PORT HERE ####
socks = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
password = "wearables"
nature = "drop"
password_nature = password + "_" + nature
socks.sendto(password_nature,serveraddress)

number_nonces = 1
while True:
	nonce, (serverIP, serverport) = socks.recvfrom(1024)
	if nonce != "epoch":
		sys.stdout.write("nonce received from server (%s) at port (%s)> %s\n" % (serverIP, serverport, nonce))
	else:
		break

	number_nonces += 1
sys.stdout.write("End of the challenges in this epoch\n\n")


