#!/usr/bin/python

import socket
import struct
import time
import datetime
import sys
import pexpect
import select
import random

# We want unbuffeshred stdout so we can provide live feedback for
# each TTL. You could also use the "-u" flag to Python.
class flushfile(file):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def mytraceroute(dest_name):
    serverIP = "149.171.37.145" ##### CHANGE SERVER IP ADDRESS HERE   #####
    #serverIP = "127.0.0.1"
    dest_addr = socket.gethostbyname(dest_name)
    port = 33434
    max_hops = 15 ###  CHANGE NUMBER OF MAXIMUM HOPS FOR TRACE ROUTE HERE   ######
    icmp = socket.getprotobyname('icmp')
    udp = socket.getprotobyname('udp')
    ttl = 1
    curr_addr = None
    curr_name = None
    closest_router = list()
    closest_router.append("serverIP")
    while True:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        
        # Build the GNU timeval struct (seconds, microseconds)
        timeout = struct.pack("ll", 5, 0)
        
        # Set the receive timeout so we behave more like regular traceroute
        recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeout)
        
        recv_socket.bind(("", port))
        sys.stdout.write(" %d  " % ttl)
        send_socket.sendto("", (dest_name, port))
        finished = False
        tries = 3
	stars = 0

        while not finished and tries > 0:
            try:
                _, curr_addr = recv_socket.recvfrom(512)
                finished = True
                curr_addr = curr_addr[0]
                try:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]
                except socket.error:
                    curr_name = curr_addr
            except socket.error as (errno, errmsg):
                tries = tries - 1
                sys.stdout.write("* ")
		stars +=1
        
        send_socket.close()
        recv_socket.close()
        
        if not finished:
            pass
        
        if curr_addr is not None and stars is not 3:
            curr_host = "%s (%s)" % (curr_name, curr_addr)
	    closest_router.append(curr_addr)

        else:
            curr_host = ""
        sys.stdout.write("%s\n" % (curr_host))

        ttl += 1
        if curr_addr == dest_addr or ttl > max_hops:
		
            break
    closest_router.reverse()
    
    return closest_router

if __name__ == "__main__":
	
	with open("serverLog.csv", "a") as myfile:
		    		myfile.write("Comments" + "," + "client nature" + "," + "client IP" + "," + "closest router IP" + "," + "nonce sent" +", " + "nonce received" + ", " + "client Epoch time(sec)"+ ", " +"client Time" +", " + "server Epoch time(sec)"+ ", " + "server Time" + "," + "Average latency (sec)"+  "," + "Maximum latency (sec)" + "," + "Std. Dev. of latency" + "," + "Time error (sec)" + "," + "Mean Time error (sec)" + "," + "Std. Dev. of time error" + "\n\n")
		    		myfile.close()
	
	while True:
		closest_router = list()
		nonce_count = 0
		Tproc = 0    ##### CHANGE PROCESSING TIME HERE ######
		Tmargin = 1  ##### CHANGE MARGIN TIME HERE ######
		max_pings = 15 ##### CHANGE MAXIMUM NUMBER OF PINGS HERE   ######
		serveraddress = ("149.171.37.145", 9999) ###  CHANGE SERVER ADDRESS HERE  #######
		#serveraddress = ("127.0.0.1", 9999)
		sockr = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sockr.bind(serveraddress)
		sys.stdout.write("Waiting for the client\n")
		password_nature, (clientIP, clientport) = sockr.recvfrom(1024)
		password, nature = password_nature.split("_",1)
		if password == "wearables":
			sys.stdout.write("password validated\n")
		else:
			sys.stdout.write("ERROR: wrong password\n")
			continue
		sys.stdout.write("client IP: %s\n" % (clientIP))
		sys.stdout.write("client port: %s\n" % (clientport))

		#clientIP = "www.google.com" #####
		sys.stdout.write("Starting traceroute to the client IP (%s)\n" % (clientIP))

		closest_router = mytraceroute(clientIP)
		i=0
		if closest_router[i] == clientIP or closest_router[i] == "127.0.0.1":
			i+=1
		else:
			pass

		while 1:
			sys.stdout.write("closest router> %s\n" % (closest_router[i]))
			sys.stdout.write("Pinging the closest router (%s) to the client\n" % (closest_router[i]))
			comments = "Estimation of latency"
			ping_argument = 'ping -i 0.5 -c'+' '+ str(max_pings) + ' ' + closest_router[i]

			child = pexpect.spawn(ping_argument)
			roundtriptimes = list()
			linefinal = ''

			while 1:
				line = child.readline()
				if not line: break
				sys.stdout.write("%s\n" % (line))
				linefinal = line
				if line[0] == '6':
					first, second, third, fourth = line.split("=")
					rtt, units = fourth.split(" ")
					roundtriptimes.append(rtt)
			if linefinal[0] != 'r':
				sys.stdout.write("No ping reply. Updating the closest router\n")
				i+=1
			else:

				roundtriptimes_fl = [float(q) for q in roundtriptimes]
				max_rtt = max(roundtriptimes_fl)
				meanrtt = sum(roundtriptimes_fl)/float(len(roundtriptimes_fl))
				mean_fl = meanrtt/2000
				sum_of_squared_errors = sum((float(q/2000) - mean_fl) ** 2 for q in roundtriptimes_fl) # loop 2
				varx = sum_of_squared_errors / float((len(roundtriptimes_fl) - 1))

				max_latencyStr = str(max_rtt/2000)
				meanStr = str(mean_fl)
				stdev_latency = varx**0.5
				stdev_latStr = str(stdev_latency)
				with open("serverLog.csv", "a") as myfile:
					myfile.write(comments + "," + nature +"," + clientIP +","+ closest_router[i] + "," + ", " + ", "+ ", "+", "+ ", "+ ", " +meanStr + "," + max_latencyStr + "," + stdev_latStr + "\n")	
					myfile.close()
				break
			
		
		timeout_in_seconds = Tproc + Tmargin + max_rtt/1000.0
		max_nonces = 10 ###  CHANGE MAXIMUM NUMBER OF NONCE MESSAGES HERE #######
		time_error = []
		error_mean = 0
		var_error = 0
		var_sensor = 0
		while nonce_count < max_nonces+1:
			
			nonce = random.randint(1000,9999)
			nonce_sent=str(nonce)
			if nonce_count == max_nonces:
				nonce_sent = "epoch"
			#clientIP = "127.0.0.1" ####
			sockr.sendto(nonce_sent,(clientIP, clientport))
			if nonce_sent == "epoch":
				sys.stdout.write("End of challenges in this epoch\n")
				break
			sys.stdout.write("nonce sent> %s\n" % (nonce_sent))

			extra_nonces = 0
			while True:
				nonce_clientTime = "_"
				sockr.settimeout(timeout_in_seconds)
				try:	
					nonce_clientTime, (clientIP, clientport) = sockr.recvfrom(1024)
				except:					
					if extra_nonces ==0:
						sys.stdout.write("ERROR: nonce timed out\n")
						comments = "ERROR: Nonce timed out"
						with open("serverLog.csv", "a") as myfile:
				    			myfile.write(comments + ","+ "," + clientIP + "," + ","+nonce_sent +"\n")
				    			myfile.close()
					time.sleep(2)
					nonce_count +=1
					break			
				nonce_received, clientEpochtimeStr = nonce_clientTime.split("_",1)

				if nonce_received != nonce_sent:
					sys.stdout.write("ERROR: nonce mismatch\n")
					comments = "ERROR: Nonce mismatch"
					with open("serverLog.csv", "a") as myfile:
			    			myfile.write(comments + "," + "," + clientIP + ", " +","  + nonce_sent +","+nonce_received + "\n")
			    			myfile.close()
					extra_nonces +=1
					continue
				else:
					comments = "OK: Nonce matched: Timed reply"
					serverEpochtime = time.time()
					serverEpochtime = float("{:.5f}".format(serverEpochtime))
					serverEpochtimeStr = "{:.5f}".format(serverEpochtime)
					serverTime = datetime.datetime.fromtimestamp(serverEpochtime).strftime('%Y-%m-%d %H:%M:%S.%f')
					clientEpochtime = float(clientEpochtimeStr)
					clientTime = datetime.datetime.fromtimestamp(clientEpochtime).strftime('%Y-%m-%d %H:%M:%S.%f')
					sys.stdout.write("nonce received back> %s\n" % (nonce_received))
					sys.stdout.write("client time received> %s\n" % (clientTime))      
					sys.stdout.write("server time> %s\n" % (serverTime))
					timeError = serverEpochtime - clientEpochtime - mean_fl
					time_error.append(timeError)
					error_mean = sum(time_error)/len(time_error)
					
					if len(time_error) ==1:
						stdev_error_str = " "
						#var_sensor_str = " "
					else:
						sum_of_sq_errs = sum((float(q) - error_mean) ** 2 for q in time_error) # loop 2
						var_error = sum_of_sq_errs / float((len(time_error) - 1))
						stdev_error = var_error**0.5
						stdev_error_str = str(stdev_error)
						#var_sensor = var_error - varx
						#var_sensor_str = str(var_sensor)
					with open("serverLog.csv", "a") as myfile:
				    		myfile.write(comments + "," +"," + clientIP + "," + ", " + nonce_sent + "," +nonce_received + ", " +clientEpochtimeStr+ ", " +clientTime +", " +serverEpochtimeStr+ ", " +serverTime+ "," + "," + "," + "," + str(timeError) + "," + str(error_mean)+ "," + stdev_error_str + "\n")
				    		myfile.close()
					time.sleep(2)
					nonce_count +=1
					break

			
			if nonce_sent == "epoch":
				sys.stdout.write("End of challenges in this epoch\n")
				#first_nonce = nonce_sent
				break
		
		#sys.stdout.write("mean error in time = %s\n" % error_mean)
		#sys.stdout.write("variance in time = %s\n" % var_error)
		
		sockr.close()


