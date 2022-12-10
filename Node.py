import socket, threading, sys
from socket import AF_INET,SOCK_DGRAM
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time
import logging
from StreamManager import StreamManager
from Server import Server
from Client import Client
from Connection import Connection

CC_TIME = 30
IP_SERVER = '127.0.0.1'
PORTLOCAL = 12460
PORTSTREAMS = 13000
PORTCLIENTVIEW = 14000
FILENAME = './resources/movie.Mjpeg'
class Node:
	top = {}
	def __init__(self,vizinhos,mode):
		self.mode = mode
		self.streams = []
		logging.info("Mode:{}".format(self.mode))
		self.flag = True
		self.host =  socket.gethostname() #cant be local host 
		logging.info("IP:{}".format(self.host))
		self.vizinhos_all = vizinhos
		logging.info("Todos vizinhos:{}".format(self.vizinhos_all))
		self.client = None
		#self.top[self.host] = []
		self.vizinhos = {}


		#tenta ligar se aos vizinhos(ve os que estao ativos)
		self.table = TabelaEnc([])
		for i in vizinhos:
			s = Connection()
			if s.connect((i,PORTLOCAL)):
				self.vizinhos[i] = s
				logging.debug("Vizinho Ativo:".format(i))
				self.table.addVizinho(i)
				threading.Thread(target=self.recv,args=(s,i)).start()
			else:
				#s.close()
				logging.debug("node {} not active".format(i))


		#self.send_LSA()
		if self.mode=="server":
			threading.Thread(target=self.send_CC_thread,args=()).start()
			threading.Thread(target=self.iniciaStreamManager,args=(self.host,'localhost')).start()
			self.server = Server(FILENAME,PORTSTREAMS)
			threading.Thread(target=self.iniciaClientView).start()
			for stream in self.streams:
				print("yooo1")
				stream.addSendingStream('localhost',PORTCLIENTVIEW)
				print("yooo2")

		self.status()

		threading.Thread(target=self.listener,args=()).start()

	def iniciaClientView(self):
		self.client= Client(FILENAME,PORTCLIENTVIEW)

	def iniciaStreamManager(self,hostname,address):
		self.streams.append(StreamManager(PORTSTREAMS,hostname,address))

	def listener(self):
		self.s = socket.socket(AF_INET,SOCK_DGRAM)
		self.s.bind(("",PORTLOCAL))

		while self.flag:
			c, addr = Connection.listen(self.s)
			logging.info('Got connection from {}'.format(addr))
			logging.debug("{} in {}:{}".format(addr[0],self.vizinhos_all,addr[0] in self.vizinhos_all))
			if(True):#addr[0] in self.vizinhos_all):
				self.vizinhos[addr[0]] = c
				self.table.addVizinho(addr[0])
				threading.Thread(target=self.recv,args=(c,addr[0])).start()
				if self.mode=="server":
					self.send_CC()
				elif self.mode=="client":
					self.send_FR()

				self.status()
			else:
				c.close()

	def send_SA(self,serverDestino):
		vizinho = self.table.bestVizinho(serverDestino)

		if(vizinho==None):
			logging.debug("Não há caminho conhecido para o servidor no SA")
			#TODO send fr to server
			#esperar por resposta (cc)
		else:
			logging.debug("Send SA")
			packet = Packet.encode_SA(serverDestino)
			if(self.send(vizinho,packet)):
				self.streams.append(StreamManager(PORTSTREAMS,serverDestino,vizinho))
				#TODO Adiciona o socket do client
			#else espera por cc



	def send_CC(self):
		logging.debug("Send CC")
		packet = Packet.encode_CC(self.host,IP_SERVER,time.time_ns(),[])
		jobs = []
		for i in self.vizinhos:
			jobs.append(threading.Thread(target=self.send,args=(i,packet)))
		
		for job in jobs:
			print("sup {}".format(time.time_ns()))
			job.start()


	def send_CC_thread(self):
		while self.flag:	
			self.send_CC()
			time.sleep(CC_TIME)

	def send_FR(self):
		logging.debug("Send FR")
		packet = Packet.encode_FR()
		hosts = self.table.getHosts()
		logging.debug(hosts)
		vs = []
		for i in hosts:
			v = self.table.bestVizinho(i)
			if v not in vs:
				logging.debug("best vizinho {}".format(v))
				vs.append(v)
				self.send(v,packet)

	def send_flood(self,packet,addr = ""):
		for i in self.vizinhos:
			if i != addr:
				logging.info("send mesg Flood to {}".format(i))
				self.send(i,packet)
			else:
				logging.info("didn't send mesg Flood to {}".format(i))

	def send(self,i,packet):
		(buffer,addr_recv) = self.vizinhos[i].send(packet)
		if(buffer != None):
			return True
		else:
			self.rm_Vizinho(i)
			if(self.mode!='server'):
				#TODO mandar mensagem direta ao servidor
				print("Envia FR direto ao servidor")
			return False

	def recv(self,s,addr):
		inflag = True
		while self.flag and inflag:
			data = s.recv(1024)
			
			if(data == None):
				self.rm_Vizinho(addr)
				inflag = False
			elif(data[0] == 0): # FR
				logging.info("receive FR from {}:".format(addr))
				mesg = Packet.decode_FR(data)
				if self.mode == "server":
					self.send_CC()
				elif self.mode == "client":
					self.send_FR()

			elif (data[0] == 1): # CC
				logging.info("receive CC from {}:".format(addr))
				if(self.table.recievePacket(addr,data)):
					self.send_flood(data,addr) 
				else:
					logging.debug("No flood")
				self.status()

			elif (data[0] == 2): #TODO test SA
				logging.info("receive SA from {}:".format(addr))
				addrDest = Packet.decode_SA(data)
				logging.info("Endereço destino: {}".format(addrDest)) 
				#Verifica se já tem a stream
				hasStream = False
				for streamManager in self.streams:
					if(streamManager.getHostName()==addrDest):
						streamManager.addSendingStream(addr)
						hasStream = True
				if(not hasStream): #Se não possuir a stream
					vizinho = self.table.bestVizinho(addrDest)
					if(vizinho==None): #TODO fr ao servidor
						pass
					else: #Caso contrário vai pedir ao nodo mais rapido
						self.send_SA(addrDest)
						#Esperar por resposta??
			else:
				logging.warning("Receive warning from {} data:{}".format(addr,data))

		logging.info("Sai recv {}".format(addr))

	def rm_Vizinho(self,addr):
		self.vizinhos.pop(addr)
		self.table.rmVizinho(addr)
		self.status()
		if self.mode == "server":
			self.send_CC()
		elif self.mode == "client":
			self.send_FR()

	def status(self):
		logging.debug("Vizinhos Ativos:{}".format(self.vizinhos.keys()))
		self.table.print()
		logging.debug("\n\n----------------------------------------------------------------------")


	def off(self):
		for i in self.vizinhos:
			self.vizinhos[i].close()
			logging.info("Vizinho Desconectado: ",i)
		self.s.close()

	def nodeInterface(self):
		while(self.flag):
			print("Comando:")
			comando = input()
			if(comando=="off"):
				self.off()
				self.flag = not self.flag
			if(comando=="stream"):				
				threading.Thread(target=self.stream,args=())
			elif(comando=="sa" and self.mode!='server'):
				self.send_SA('Server')
			elif(comando=="cc" and self.mode=='server'):
				self.send_CC()


if __name__ == '__main__':
	logging.basicConfig(format='%(message)s',level=logging.DEBUG)#(format='%(levelname)s:%(message)s',level=logging.DEBUG)
	parser = argparse.ArgumentParser()
	parser.add_argument("vizinhos",nargs="*")
	parser.add_argument("-m","--mode",choices=["server","client"],default="client")
	
	args = parser.parse_args()

	t1 = Node(args.vizinhos,args.mode)
	t1.nodeInterface()


#print(args.vizinhos,args.mode)


#t1 = Node(args.vizinhos,args.mode)
#t1.send(bytes("ola","utf-8"),sys.argv[1],12451)
