import socket, threading, sys
from socket import AF_INET,SOCK_DGRAM
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time
import logging
from Connection import Connection

class StreamManager:
	#mode == 'client' or 'server'
	#se for um cliente o recievingAddress é required
	#se for um servidor o recievingAddress não é utilizado
	def __init__(self,port,hostname,recievingAddress):
		self.sendstreams = []
		self.port = port
		self.interface = None
		self.running = True
		self.hostname = hostname
		
		s = socket.socket(AF_INET,SOCK_DGRAM)
		s.bind(("",self.port))

		c, addr = Connection.listen(s)
		s.close()
		self.Recivingtream = c
		threading.Thread(target=self.__recv,args=(c,addr)).start()

	def getHostName(self):
		return self.hostname

	def close(self):
		self.running = False

	def addSendingStream(self,sendingAddress, port=0):
		print("start adding stream")
		if(port == 0):
			port=self.port 
		s= Connection()
		print("trying to connect in sending address:"+sendingAddress+" and port:"+str(port))
		if(s.connect((sendingAddress,self.port))):
			self.sendstreams.append(s)
			print("coonection done")
		else:
			raise Exception("Connection not established in stream manager") 

	def removeSendingStream(self,sendingAddress):
		self.sendstreams[:] = ((connection) 
			for (connection) in self.sendstreams if connection.getAddress()!=sendingAddress)

	def __recv(self,s,addr):
		while self.running:
			data = s.recv()
			
			if(data == None):
				self.running = False
			elif(data[0] == 3): # STREAM PACKET
				#logging.info("receive Stream, from {}:".format(addr))
				self.sendAll(data)
				if(self.interface!=None):
					self.interface.send(Packet.decode_STREAM(data))
			else:
				logging.warning("Receive warning from {} data:{}".format(addr,data))

		logging.info("Sai recv {}".format(addr))

	def sendAll(self,packet):
		for connection in self.sendstreams:
			self.send(connection,packet)

	def send(self,connection,packet):
		(buffer,addr_recv) = connection.send(packet)
		if(buffer == None):
			self.removeSendingStream(connection.getAddress())


if __name__ == '__main__':
	print("main")