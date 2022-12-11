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

CC_TIME = 100
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

		threadsConnectVizinhos = []
		barrier = threading.Barrier(len(vizinhos)+1)
		for i in vizinhos:
			threadsConnectVizinhos.append(threading.Thread(target=self.__connectToVizinho,args=(i,barrier)))
			
		for job in threadsConnectVizinhos:
			job.start()

		barrier.wait()

		#self.send_LSA()
		if self.mode=="server":
			threading.Thread(target=self.send_CC_thread,args=()).start()
			self.streams.append(StreamManager(PORTSTREAMS,self.host,'localhost'))
			self.server = Server(FILENAME,PORTSTREAMS)

		self.status()

		threading.Thread(target=self.listener,args=()).start()

	def __connectToVizinho(self,vizinho,barrier):
		s = Connection()
		if s.connect((vizinho,PORTLOCAL)):
			self.vizinhos[vizinho] = s
			logging.debug("Vizinho Ativo:".format(vizinho))
			self.table.addVizinho(vizinho)
			threading.Thread(target=self.recv,args=(s,vizinho)).start()
		else:
			#s.close()
			logging.debug("node {} not active".format(vizinho))
		barrier.wait()

	def __getStreamManagerOfHost(self,host):
		for streamManager in self.streams:
			if(streamManager.getHostName()==host):
				return streamManager
		return None

	def iniciaClientView(self):
		self.client= Client(FILENAME,PORTSTREAMS)

	def listener(self):
		self.s = socket.socket(AF_INET,SOCK_DGRAM)
		self.s.bind(("",PORTLOCAL))

		while self.flag:
			c, addr = Connection.listen(self.s,self.vizinhos.keys())
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

		streamManager = self.__getStreamManagerOfHost(serverDestino)
		if(streamManager!=None and streamManager.getVizinho()==vizinho):
			print("Stream path already up to date")
		elif(streamManager!=None and streamManager.getVizinho()==vizinho): #Então encontra-se na situação ideal e SA não é necessario
			print("SA not necessary so it was not sent")
		elif(vizinho==None):
			logging.debug("Não há caminho conhecido para o servidor no SA")
			#TODO send fr to server
			#esperar por resposta (cc)
		else:
			logging.debug("Send SA")
			packet = Packet.encode_SA(serverDestino)
			if(self.send(vizinho,packet)):
				if(streamManager==None):
					self.streams.append(StreamManager(PORTSTREAMS,serverDestino,vizinho))
				else:
					streamManager.updateReicivingStream()
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
		jobs = []
		for i in self.vizinhos:
			if i != addr:
				logging.info("send mesg Flood to {}".format(i))
				jobs.append(threading.Thread(target=self.send,args=(i,packet)))
			else:
				logging.info("didn't send mesg Flood to {}".format(i))
		for job in jobs:
			print("sup {}".format(time.time_ns()))
			job.start()
			

	def send(self,i,packet):
		(buffer,addr_recv) = self.vizinhos[i].send(packet)
		if(buffer != None):
			return True
		else:
			self.rm_Vizinho(i)
			print("ola")
			if(self.mode!='server'):
				#TODO mandar mensagem direta ao servidor
				print("Envia FR direto ao servidor")
			logging.debug(self.status())
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

			elif (data[0] == 2):
				logging.info("receive SA from {}:".format(addr))
				addrDest = Packet.decode_SA(data)
				logging.info("Endereço destino: {}".format(addrDest)) 
				#Verifica se já tem a stream
				streamManager = self.__getStreamManagerOfHost(addrDest)
				if(streamManager != None):
					streamManager.addSendingStream(addr)
				else: #Se não possuir a stream
					self.send_SA(addrDest)
					streamManager = self.__getStreamManagerOfHost(addrDest)
					if(streamManager != None):
						streamManager.addSendingStream(addr)
					else: 
						print("Error on receive SA")
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
			logging.info("Vizinho Desconectado: {}".format(i))
		self.s.close()
		self.flag = not self.flag
		print("done")

	def nodeInterface(self):
		while(self.flag):
			print("Comando:")
			comando = input()
			if(comando=="off"):
				self.off()
			if(comando=="stream"):				
				threading.Thread(target=self.stream,args=())
			elif(comando=="sa" and self.mode=='client'):
				self.send_SA('Server')
			elif(comando=="cc" and self.mode=='server'):
				self.send_CC()
			elif(comando=="watch" and self.mode=='client'):
				threading.Thread(target=self.iniciaClientView).start()
				for stream in self.streams:
					stream.addSendingStream('',PORTSTREAMS)

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
