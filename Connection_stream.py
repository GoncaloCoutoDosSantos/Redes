import socket,time,threading
from socket import AF_INET,SOCK_DGRAM,MSG_PEEK,timeout
import logging
import time
from random import randint
import threading

"""
Pacote - tipo | sequencia | mensagem 
Tipos - \x00 = data
        \x01 = Ack
        \x02 = close
        \x03 = connection request
"""

TIMEOUT_STREAM = 5
KEEP_ALIVE = 0.5
TIMEOUT = 3
SIZE = 20480#1024 #tamanho maximo dos pacotes

class Connection:
	timeout = 0.5 #definition of timeout in seconds
	max_tries = 5 #number of max tries to do a connection


	def __init__(self,mode = "send",socket = None,addr = None,last_seq = -1):
		self.socket = socket #socket used to send messeges
		self.addr = addr #addr of the other socket
		self.last_seq = last_seq
		self.lock = threading.Lock()
		self.lock_read = threading.Lock()
		self.seq = randint(0,255)
		self.last_seq = -1
		self.alive = True #bollean that says if connection is active

		self.mode = mode 
		if mode == "recv":
			threading.Thread(target=self.keep_alive).start()


	#tries to start a new connection with a new node 
	#if succed the starts an keep alive to check if the connection still stands 
	def connect(self,addr):
		ip,port = addr
		s = socket.socket(AF_INET,SOCK_DGRAM)
		s.bind(("",0))

		self.socket = s
		self.addr = addr

		buffer,addr_recv = self.send_ack(b'',b'\x03')

		if(buffer == None):
			s.close()
			self.alive = False
			self.socket = None
			self.addr = None
		else:
			self.addr = addr_recv
			logging.info("connect to {}".format(addr_recv))
			if self.mode == "send":
				threading.Thread(target=self.keep_alive_listen).start()
				

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

				if(self.lock_read.acquire(timeout=timeout if timeout != None else -1)):
					#logging.info(self.socket.getsockname())
					s.settimeout(timeout)
					buffer,addr_recv = s.recvfrom(SIZE,MSG_PEEK)
					#logging.debug(":Conn:recv:{} | time: {}".format(buffer[:20],time.time()))
					tipo = buffer[0]

					if (tipo == 0): #recebeu data 
						last_seq = (self.last_seq + 1) % 256
						seq_recv = int.from_bytes(buffer[1:2],"big")
						if(target == tipo):
							self.last_seq = seq_recv 
							buffer,addr_recv = s.recvfrom(SIZE)
							flag = not flag

					elif (tipo == 1): # recebeu ack
						seq = self.seq
						seq_recv = int.from_bytes(buffer[1:2],"big")

						if(target == tipo):
							buffer,addr_recv = s.recvfrom(SIZE)
							flag = not flag

					elif (tipo == 2): # recebeu close
						seq = self.seq
						seq_recv = int.from_bytes(buffer[1:2],"big")
						buffer,addr_recv = s.recvfrom(SIZE)
						flag = not flag	
						logging.debug(":Conn:close received")
						self.alive = not self.alive

					else:
						logging.warning(":Conn: PACKET NOT IDENTIFED {}:{}".format(tipo,buffer))

					self.lock_read.release()
				else:
					raise socket.timeout
			return buffer,addr_recv
		
		except Exception as e:
			self.lock_read.release()
			raise e


	def keep_alive(self):
		#logging.info("OLA |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
		while self.alive:
			self.send(b'',b'\x01')
			#logging.info("send keep alive")
			time.sleep(KEEP_ALIVE)

	def keep_alive_listen(self):
		try:
			while self.alive:
				self.recv_buffer(1,TIMEOUT)
				#logging.info("recv keep alive")
		except timeout:
			logging.info("keep alive timeout")
			self.alive = not self.alive
		except Exception as e:
			logging.warning(":Conn: {}".format(e))



		

	# funtion that send a message and confirm reception by receiving an ack 
	# in case that the send fail the funtion tries again 
	# if alive is false return None
	# return the (response,endereço do no que enviou) or None
	def send_ack(self,mesg,tipo=b'\x00'):

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
				#logging.debug(":Conn:Recv Ack:{}".format(buffer))
				flag = not flag
				self.seq = (seq + 1) % 256
			except timeout:
				tries = tries + 1
				#logging.debug(":Conn:timeout tries: {}".format(tries))

		self.lock.release()

		return buffer,addr_recv

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

		if self.alive:
			buffer = []
			#logging.info("send data to {} buffer :{}".format(addr,mesg[:20]))
			s.sendto(mesg,addr)
			self.seq = (seq + 1) % 256


		self.lock.release()

		return buffer,addr_recv

	# function that recive mesg for the server
	def recv(self,size=SIZE):
		flag = True
		s = self.socket
		buffer = None
		addr = None

		if(self.alive):
			try:
				buffer,addr = self.recv_buffer(0,TIMEOUT_STREAM)
				buffer = buffer[2:]
		
			except Exception as e:
				logging.warning(":Conn: {}".format(e))

		return buffer

	# funtion used to listen to new connections
	# return a new connection
	def listen(s,connected = [],mode = "control"):
		flag = True
		addr = None
		ret_s = None
		seq = 1

		try:
			while (flag):
				s.settimeout(None)
				buffer,addr = s.recvfrom(SIZE,MSG_PEEK)
				if(buffer[0] == 3 and addr[0] not in connected):
					buffer,addr = s.recvfrom(SIZE)
					seq = buffer[1]
					flag = not flag
				else:
					buffer,addr = s.recvfrom(SIZE)


			ret_s = socket.socket(AF_INET,SOCK_DGRAM)
			ret_s.bind(("",0))
			msg = b'\x01' + seq.to_bytes(1,'big')
			ret_s.sendto(msg,addr)

			logging.debug("listen :connect to {}".format(addr))
		except IOError as e:
			logging.info("CONN:Listen bad socket processo de fecho {}".format(e))

		return Connection("recv",ret_s,addr,seq),addr

	def getAddress(self):
		return self.addr

	def close(self):
		self.lock.acquire()

		if(self.socket != None):
			self.socket.sendto(b'\x0200000000',self.addr)
			try:
				self.socket.sendto(b'',self.socket.getsockname())
			except Exception as e:
				logging.info("Exceçao :{}".format(e))
			self.socket.close()
		self.socket = None
		self.alive = False

		self.lock.release()

			
