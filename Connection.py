import socket,time,threading
from socket import AF_INET,SOCK_DGRAM,MSG_PEEK
import logging

"""
Pacote - tipo | sequencia ??? | mensagem 
"""



SIZE = 1024 #tamanha maximo dos pacotes

class Connection:
	timeout = 0.5 #definition of timeout in seconds
	max_tries = 5 #number of max tries to do a connection
	alive = True #bollean that says if connection is active
	socket = None #socket used to send messeges
	addr = None #addr of the other socket
	mode = ""

	def __init__(self,mode = "control",socket = None,addr = None):
		self.socket = socket
		self.addr = addr

		if(mode == "control"):
			self.mode = mode 
		elif(mode == "stream"):
			self.mode = mode

	#tries to start a new connection with a new node 
	#if succed the starts an keep alive to check if the connection still stands 
	def connect(self,addr):
		ip,port = addr
		s = socket.socket(AF_INET,SOCK_DGRAM)
		s.bind(("",0))

		self.socket = s
		self.addr = addr

		buffer,addr_recv = self.send(bytearray(12))

		if(buffer == None):
			s.close()
			self.alive = False
			self.socket = None
			self.addr = None
		else:
			self.addr = addr_recv

		return self.alive
		

	# funtion that send a message and confirm reception by receiving an ack 
	# in case that the send fail the funtion tries again 
	# if alive is false return None
	# return the (response,endereço do no que enviou) or None
	def send(self,mesg):
		s = self.socket
		addr = self.addr
		flag = False #if already recv the message
		buffer = None
		addr_recv = None
		tries = 0
		s.settimeout(self.timeout)

		mesg = b'\x00' + mesg

		while (tries < self.max_tries and not flag) and self.alive:
			s.sendto(mesg,addr)
			try:
				while not flag:
					buffer,addr_recv = s.recvfrom(SIZE,MSG_PEEK)
					logging.debug(":Conn:send Ack:{}".format(buffer))
					if(buffer[0] == 1):
						buffer,addr_recv = s.recvfrom(SIZE)
						flag = not flag
			except TimeoutError:
				tries = tries + 1
				logging.debug(":Conn:timeout tries: {}".format(tries))

		return buffer,addr_recv

	# function that recive mesg for the server
	def recv(self,size=SIZE):
		flag = True
		s = self.socket
		buffer = None
		addr = None

		try:
			while(flag and self.alive):
				s.settimeout(None) # sem timeout 
				buffer,addr = s.recvfrom(size,MSG_PEEK)
				logging.debug(":CONN:recv Ack:{}".format(buffer))
				if(buffer[0] == 0):
					buffer,addr = s.recvfrom(size)
					flag = not flag
					s.sendto(b'\x01',addr)
					buffer = buffer[1:]
		except Exception as e:
			logging.warning(":CONN:",e)

		return buffer

	# funtion used to listen to new connections
	# return a new connection
	def listen(s,mode = "control"):

		s.settimeout(None)
		buffer,addr = s.recvfrom(SIZE)
		ret_s = socket.socket(AF_INET,SOCK_DGRAM)
		ret_s.bind(("",0))
		ret_s.sendto(b'\x01',addr)

		return Connection(mode,ret_s,addr),addr

	def close():
		pass



