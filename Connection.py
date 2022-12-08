import socket,time,threading
from socket import AF_INET,SOCK_DGRAM,MSG_PEEK,timeout
import logging
import time
from random import randint

"""
Pacote - tipo | sequencia | mensagem 
Tipos - \x00 = data
        \x01 = Ack
        \x03 = connection request
"""



SIZE = 1024 #tamanha maximo dos pacotes

class Connection:
	timeout = 0.5 #definition of timeout in seconds
	max_tries = 5 #number of max tries to do a connection
	alive = True #bollean that says if connection is active
	socket = None #socket used to send messeges
	addr = None #addr of the other socket
	mode = ""
	seq = randint(0,255)
	last_seq = -1
	lock = threading.Lock()

	def __init__(self,mode = "control",socket = None,addr = None,last_seq = -1):
		self.socket = socket
		self.addr = addr
		self.last_seq = last_seq

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

		buffer,addr_recv = self.send(b'',b'\x03')

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
	def send(self,mesg,tipo=b'\x00'):

		self.lock.acquire()

		s = self.socket
		addr = self.addr
		flag = False #if already recv the message
		buffer = None
		addr_recv = None
		tries = 0
		seq = self.seq
		seq_recv = 0

		mesg = tipo + seq.to_bytes(1,'big') + mesg

		while (tries < self.max_tries and not flag) and self.alive:
			s.sendto(mesg,addr)
			try:
				while not flag:
					s.settimeout(self.timeout)
					buffer,addr_recv = s.recvfrom(SIZE,MSG_PEEK)
					logging.debug(":Conn:send Ack:{}".format(buffer))
					if(buffer[0] == 1):
						seq_recv = int.from_bytes(buffer[1:2],"big")
						if(seq_recv == seq):
							buffer,addr_recv = s.recvfrom(SIZE)
							flag = not flag
							self.seq = (seq + 1) % 256
						else:#limpa buffer se for um ack mas n corresponder a seq 
							s.recvfrom(SIZE)
					else:
						time.sleep(0.01)
			except timeout:
				tries = tries + 1
				logging.debug(":Conn:timeout tries: {}".format(tries))

		self.lock.release()

		return buffer,addr_recv

	# function that recive mesg for the server
	def recv(self,size=SIZE):
		flag = True
		s = self.socket.dup()
		buffer = None
		addr = None
		last_seq = (self.last_seq + 1) % 256

		try:
			while(flag and self.alive):
				s.settimeout(None) # sem timeout 
				buffer,addr = s.recvfrom(size,MSG_PEEK)
				logging.debug(":Conn:recv Ack:{}".format(buffer))
				if(buffer[0] == 0):
					seq_recv = int.from_bytes(buffer[1:2],"big")
					if(last_seq == seq_recv or self.last_seq == -1):
						buffer,addr = s.recvfrom(size)
						flag = not flag
						s.sendto(b'\x01' + buffer[1].to_bytes(1,'big'),addr)
						buffer = buffer[2:]
						self.last_seq = seq_recv
					else:
						s.recvfrom(size)
				else:
					time.sleep(0.01)
		except Exception as e:
			logging.warning(":Conn:",e)

		return buffer

	# funtion used to listen to new connections
	# return a new connection
	def listen(s,mode = "control"):
		flag = True

		while (flag):
			s.settimeout(None)
			buffer,addr = s.recvfrom(SIZE,MSG_PEEK)
			if(buffer[0] == 3):
				buffer,addr = s.recvfrom(SIZE)
				seq = buffer[1]
				flag = not flag
			else:
				time.sleep(0.01)


		ret_s = socket.socket(AF_INET,SOCK_DGRAM)
		ret_s.bind(("",0))
		msg = b'\x01' + seq.to_bytes(1,'big')
		ret_s.sendto(msg,addr)

		return Connection(mode,ret_s,addr,seq),addr

	def close():
		pass



