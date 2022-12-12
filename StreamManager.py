import socket, threading, sys
from socket import AF_INET,SOCK_DGRAM
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time
import logging
from Connection import Connection

class StreamManager:
	#mode == 'client' or "cliente ativo" or "server"
	#se for um client então fecha recievingStream caso não esteja a passar a stream a alguem
	def __init__(self,port,hostname,mode, sendingAddress = None):
		self.sendstreams = []
		self.port = port
		self.mode = mode
		self.running = True
		self.hostname = hostname
		self.Recivingtream = None
		if(sendingAddress is not None):
			self.addSendingStream(sendingAddress)
		threading.Thread(target=self.updateReicivingStream,args=(mode,)).start()

	def getHostName(self):
		return self.hostname

	def close(self):
		self.running = False

	def getVizinho(self):
		return self.Recivingtream.getAddress()[0]

	def addSendingStream(self,sendingAddress, port=0):
		if(port == 0):
			port=self.port 
		logging.info("try to connect")
		s= Connection()

		if(s.connect((sendingAddress,self.port))):
			logging.info("connected")
			self.sendstreams.append(s)
		else:
			raise Exception("Connection not established in stream manager")

	def updateReicivingStream(self,mode):
		self.mode= mode
		if(self.Recivingtream!= None):
			print("ola")
			self.Recivingtream.close()
			print("close")
			#self.running = False
		s = socket.socket(AF_INET,SOCK_DGRAM)
		s.bind(("",self.port))

		logging.info("listenig")
		c, addr = Connection.listen(s)
		print("ola1")

		s.close()
		self.Recivingtream = c
		threading.Thread(target=self.__recv,args=(addr,)).start()

	def removeSendingStream(self,sendingAddress):
		self.sendstreams[:] = ((connection) 
			for (connection) in self.sendstreams if connection.getAddress()!=sendingAddress)

	def __recv(self,addr):
		self.running = True
		while self.running:
			data = self.Recivingtream.recv()
			if(data == None):
				logging.info("Fuck!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!{}".format(self.Recivingtream.getAddress()))
				self.running = False
			elif(data[0] == 3): # STREAM PACKET
				logging.info("receive Stream, from {}:".format(addr))
				self.sendAll(data)
				if(self.mode=='client' and len(self.sendstreams)==0):
					print("close recievingStream")
					self.Recivingtream.close()
			else:
				logging.warning("Receive warning from {} data:{}".format(addr,data))

		logging.info("Sai recv {}".format(addr))

	def sendAll(self,packet):
		for connection in self.sendstreams:
			logging.info("send stream to " + str(connection.getAddress()) )
			self.send(connection,packet)

	def send(self,connection,packet):
		logging.info("start send")
		(buffer,addr_recv) = connection.send(packet)
		logging.info("end send")
		if(buffer == None):
			connection.close()
			self.removeSendingStream(connection.getAddress())


if __name__ == '__main__':
	print("main")