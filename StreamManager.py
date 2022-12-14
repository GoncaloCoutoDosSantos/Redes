import socket, threading, sys
from socket import AF_INET,SOCK_DGRAM
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time
import logging
from Connection_stream import Connection

class StreamManager:
	#mode == 'client' or "cliente ativo" or "server"
	#se for um client então fecha recievingStream caso não esteja a passar a stream a alguem
	def __init__(self,port,hostname,mode, sendingAddress = None):
		self.sendstreams = []
		self.port = port
		self.mode = mode
		self.listener = None
		self.lock = threading.Lock()
		self.hostname = hostname
		self.Recivingtream = None
		self.timeStamps = []
		self.lastPacketTime = 0
		self.timeStampsLock = threading.Lock()
		self.running = False

		self.waitingForCC = False
		self.receivedCC = False
		self.ccLogicLock = threading.Lock()

		if(sendingAddress is not None):
			self.addSendingStream(sendingAddress)
		self.updateReicivingStream(mode)

	def setReceivedCC(self, value):
		self.ccLogicLock.acquire()
		self.receivedCC=value
		self.ccLogicLock.release()


	def lockLock(self):
		self.lock.acquire()

	def unlockLock(self):
		self.lock.release()

	def getHostName(self):
		return self.hostname

	def close(self):
		self.running = False
		for connection in self.sendstreams:
			connection.close()
		self.sendstreams = []
		self.Recivingtream.close()
		if(self.listener != None):
			c = Connection()
			c.connect(("",self.port))
			c.close()

	def getSendingStreamVizinho(self):
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
		threading.Thread(target=self.__updateReicivingStreamThread,args=(mode,)).start()

	def getRecivingStreamVizinho(self):
		return self.Recivingtream.getAddress()[0]

	def __updateReicivingStreamThread(self,mode):
		self.mode= mode
		if(self.Recivingtream!= None):
			self.Recivingtream.close()
			print("closed reciving stream")
			
		self.listener = socket.socket(AF_INET,SOCK_DGRAM)
		self.listener.bind(("",self.port))

		logging.info("listenig")
		c, addr = Connection.listen(self.listener)
		print("listening done")

		self.listener.close()
		self.listener= None

		self.Recivingtream = c
		self.__recv(addr)

	def removeSendingStream(self,sendingAddress):
		self.sendstreams[:] = ((connection) 
			for (connection) in self.sendstreams if connection.getAddress()!=sendingAddress)

	def isRunning(self):
		return self.running

	def getTimeTaken(self):
		self.timeStampsLock.acquire()
		if(len(self.timeStamps)!=0):
			mean = sum(self.timeStamps) / len(self.timeStamps)
			self.timeStamps = []
			lastTime = self.lastPacketTime

			self.timeStampsLock.release()
			return (mean,lastTime)
		
		else:
			self.timeStampsLock.release()
			return (-1,-1)

	def __recv(self,addr):
		self.lockLock()
		self.running = True
		while self.running:
			#print("ready to receive")
			data = self.Recivingtream.recv()
			if(data == None):
				logging.info("DATA == NONE")
				self.running = False
				print("close recievingStream")
				self.Recivingtream.close()
			elif(data[0] == 3): # STREAM PACKET
				logging.info("receive Stream, from {}:".format(addr))

				(framePacket, timeSent) = Packet.decode_STREAM(data)
				timeTaken = (time.time_ns()-timeSent)

				self.timeStampsLock.acquire()
				self.timeStamps.append(timeTaken)
				self.lastPacketTime = timeSent
				self.timeStampsLock.release()

				self.sendAll(data)
				if(self.mode=='client' and len(self.sendstreams)==0):
					print("no more streams to send")
					self.running = False
					self.close()
			elif(data[0] == 4):
				if(self.mode=='client'):
					print("loop detected")
					self.running = False
					self.close()
			else:
				logging.warning("Receive warning from {} data:{}".format(addr,data))
		self.unlockLock()
		logging.info("Sai recv {}".format(addr))

	def sendAll(self,packet):
		for connection in self.sendstreams:
			logging.info("send stream to " + str(connection.getAddress()) )
			threading.Thread(target=self.send,args=(connection,packet)).start()

	def send(self,connection,packet):
		logging.info("start send")
		(buffer,addr_recv) = connection.send(packet)
		logging.info("end send")
		if(buffer == None):
			connection.close()
			self.removeSendingStream(connection.getAddress())


if __name__ == '__main__':
	print("main")