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


TIMEOUT = 0.5
SIZE = 1024 #tamanha maximo dos pacotes

class Connection:
	timeout = 0.5 #definition of timeout in seconds
	max_tries = 5 #number of max tries to do a connection


	def __init__(self,mode = "control",socket = None,addr = None,last_seq = -1):
		self.socket = socket #socket used to send messeges
		self.addr = addr #addr of the other socket
		self.last_seq = last_seq
		self.lock = threading.Lock()
		self.lock_read = threading.Lock()
		self.seq = randint(0,255)
		self.last_seq = -1
		self.alive = True #bollean that says if connection is active

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


	#function that first recv the information in the socket 
	#recv the type of mesg that is looking for 
	#check if anything can go to trash 
	def recv_buffer(self,target,timeout = TIMEOUT):
		flag = True #flag that says is recv the right tipy of package
		s = self.socket
		buffer = None
		addr_recv = None

		try:
			while flag and self.alive:

				self.lock_read.acquire()

				s.settimeout(timeout)
				buffer,addr_recv = s.recvfrom(SIZE,MSG_PEEK)
				logging.debug(":Conn:recv:{}".format(buffer))
				tipo = buffer[0]

				if (tipo == 0): #recebeu data 
					last_seq = (self.last_seq + 1) % 256
					seq_recv = int.from_bytes(buffer[1:2],"big")
					if(last_seq != seq_recv and self.last_seq != -1):
						s.recvfrom(SIZE)
						logging.debug(":Conn:data rejeitado: Esperado:{} recebido:{}".format(last_seq,seq_recv))
					elif(target == tipo):
						self.last_seq = seq_recv 
						buffer,addr_recv = s.recvfrom(SIZE)
						flag = not flag

				elif (tipo == 1): # recebeu ack
					seq = self.seq
					seq_recv = int.from_bytes(buffer[1:2],"big")
					if(seq != seq_recv):
						s.recvfrom(SIZE)
						logging.debug(":Conn:ack rejeitado")
					elif(target == tipo):
						buffer,addr_recv = s.recvfrom(SIZE)
						flag = not flag					
				else:
					logging.warning(":Conn: PACKET NOT IDENTIFED {}:{}".format(tipo,buffer))

				self.lock_read.release()
			
			return buffer,addr_recv
		
		except Exception as e:
			self.lock_read.release()
			raise e



		

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
				buffer,addr_recv = self.recv_buffer(1)
				logging.debug(":Conn:Recv Ack:{}".format(buffer))
				flag = not flag
				self.seq = (seq + 1) % 256
			except timeout:
				tries = tries + 1
				logging.debug(":Conn:timeout tries: {}".format(tries))

		self.lock.release()

		return buffer,addr_recv

	# function that recive mesg for the server
	def recv(self,size=SIZE):
		flag = True
		s = self.socket
		buffer = None
		addr = None

		try:
			buffer,addr = self.recv_buffer(0,None)
			s.sendto(b'\x01' + buffer[1].to_bytes(1,'big'),addr)
			buffer = buffer[2:]
			logging.debug(":Conn:recv Data:{}".format(buffer))
			flag = not flag
	
		except Exception as e:
			logging.warning(":Conn: {}".format(e))

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

	def getAddress(self):
		return self.addr

	def close():
		pass

			
