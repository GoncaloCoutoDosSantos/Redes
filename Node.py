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
GESTOR_FLOODS_SEGUIDOS_TIME = 1
GESTOR_TABLE_TIME = 4
TIMEUPDATESA = 4
IP_SERVER = '127.0.0.1'
PORTLOCAL = 12460
PORTSTREAMS = 13000
PORTCLIENTVIEW = 14000
FILENAME = './resources/movie.Mjpeg'
class Node:
	top = {}
	def __init__(self,vizinhos,mode,name,ip_server):
		self.mode = mode
		self.streams = []
		logging.info("Mode:{}".format(self.mode))
		self.flag = True
		self.host =  name if name != None else socket.gethostname() #cant be local host 
		logging.info("IP:{}".format(self.host))
		self.vizinhos_all = vizinhos
		logging.info("Todos vizinhos:{}".format(self.vizinhos_all))
		self.client = None
		#self.top[self.host] = []
		self.vizinhos = {}
		self.ip_server = ip_server


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
			self.streams.append(StreamManager(PORTSTREAMS,self.host,self.mode))
			self.server = Server(FILENAME,PORTSTREAMS)
			self.floodCC = True
			self.floodCCLock = threading.Lock()
			threading.Thread(target=self.__gestorDeFloodsSeguidos,args=()).start()

		self.status()

		threading.Thread(target=self.listener,args=()).start()
		threading.Thread(target=self.gestorDaTabelaEnc,args=()).start()
		threading.Thread(target=self.gestorUpdatePathSA,args=()).start()

	def __gestorDeFloodsSeguidos(self):
		while(self.flag):
			self.floodCCLock.acquire()
			if(self.floodCC):
				self.send_CC()
			self.floodCC = False
			self.floodCCLock.release()
			time.sleep(GESTOR_FLOODS_SEGUIDOS_TIME)

	def __connectToVizinho(self,vizinho,barrier):
		s = Connection()
		if s.connect((vizinho,PORTLOCAL)):
			self.vizinhos[vizinho] = s
			logging.debug("Vizinho Ativo:".format(vizinho))
			self.table.addVizinho(vizinho)
			threading.Thread(target=self.recv,args=(s,vizinho)).start()
			barrier.wait()
		else:
			#s.close()
			logging.debug("node {} not active".format(vizinho))
			barrier.wait()

			

	def __getStreamManagerOfHost(self,host):
		for streamManager in self.streams:
			if(streamManager.getHostName()==host):
				return streamManager
		return None
	
	def closeStreamManagersComingFromVizinho(self,vizinho):
		for streamManager in self.streams:
			if(streamManager.getRecivingStreamVizinho()==vizinho):
				streamManager.close()

	def gestorDaTabelaEnc(self):
		while(self.flag):
			for streamManager in self.streams:
				if(streamManager != None and streamManager.isRunning()):
					host = streamManager.getHostName()
					vizinho = streamManager.getRecivingStreamVizinho()
					(timeTaken,timeInitial) = streamManager.getTimeTaken()

					if(timeTaken!=-1 and vizinho!='127.0.0.1'):
						self.table.updateTempoHost(vizinho, host,self.table.getHostIp(host), timeTaken,timeInitial)
						self.table.print()
			time.sleep(GESTOR_TABLE_TIME)
	
	def gestorUpdatePathSA(self):
		while(self.flag):
			for streamManager in self.streams:
				if(streamManager != None and streamManager.getReceivedCC()==False and streamManager.getWaitingForCC() 
				and self.mode=="cliente ativo"):
					self.send_FR_Direct(streamManager.getHostName())
					time.sleep(GESTOR_TABLE_TIME)
				if( streamManager != None and streamManager.getRecivingStreamVizinho()!='127.0.0.1' 
				and (streamManager.isRunning() or (streamManager.getReceivedCC() and streamManager.getWaitingForCC()))):
					host = streamManager.getHostName()
					vizinhoAtual = streamManager.getRecivingStreamVizinho()
					if(vizinhoAtual !=None):
						vizinhoTable = self.table.bestVizinho(host)
						(_,_,timeTakenAtual,_) = self.table.getHostVizinhoEntry(vizinhoAtual, host)
						(_,_,timeTakenTable,_) = self.table.getHostVizinhoEntry(vizinhoTable, host)
						if(timeTakenTable + 10000 < timeTakenAtual and timeTakenTable + timeTakenAtual*0.2 < timeTakenAtual):
							self.send_SA(host)
					else:
						self.send_SA(host)
					if(streamManager.getReceivedCC()==True):
						streamManager.setWaitingForCC(False)
			time.sleep(GESTOR_TABLE_TIME)

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
					self.send_FR_initial()
					self.floodCC = True
				elif self.mode=="client" or self.mode == "cliente ativo":
					self.send_FR_initial()

				self.status()
			else:
				c.close()

	def send_SA(self,serverDestino, sendingAddress=None):
		vizinho = self.table.bestVizinho(serverDestino)
		streamManager = self.__getStreamManagerOfHost(serverDestino)

		if(streamManager!=None and streamManager.isRunning() and streamManager.getRecivingStreamVizinho()==vizinho):
			print("Stream path already up to date")
		elif(vizinho==None):
			logging.debug("Não há caminho conhecido para o servidor no SA")
		else:
			logging.debug("Send SA")
			packet = Packet.encode_SA(serverDestino)

			loopDetected = False #TODO isto está horrible	
			if(streamManager==None):
				threading.Thread(target=self.streams.append,args=(StreamManager(PORTSTREAMS,serverDestino,self.mode,sendingAddress),)).start()
			else:
				print("update reciving stream")
				
				if(sendingAddress!=None):
					loopDetected = streamManager.addSendingStream(sendingAddress)
				if(not loopDetected): streamManager.updateReicivingStream(self.mode)
			if(not loopDetected):self.send(vizinho,packet)
				



	def send_CC(self):
		logging.debug("Send CC")
		packet = Packet.encode_CC(self.host,self.ip_server,time.time_ns(),[])
		jobs = []
		for i in self.vizinhos:
			jobs.append(threading.Thread(target=self.send,args=(i,packet)))
		
		for job in jobs:
			job.start()


	def send_CC_thread(self):
		while self.flag:	
			self.send_CC()
			time.sleep(CC_TIME)

	def send_FR_initial(self):
		logging.debug("Send FR")
		hosts = self.table.getHosts()
		for host in hosts:
			self.send_FR(host)

	def send_FR(self,host):
		packet = Packet.encode_FR(host)
		vizinho = self.table.bestVizinho(host)
		if(vizinho != None):
			self.send(vizinho,packet)

	def send_FR_Direct(self,host):
		print("Send FR direct")
		print("host :",host)
		ip = self.table.getHostIp(host)
		print("ip: ",ip)
		if(ip!=None and ip != IP_SERVER):
			c = Connection()
			c.connect((ip,PORTLOCAL))
			c.close()
			
	


	def send_flood(self,packet,addr = ""):
		jobs = []
		for i in self.vizinhos:
			if i != addr:
				logging.info("send mesg Flood to {}".format(i))
				jobs.append(threading.Thread(target=self.send,args=(i,packet))) 
			else:
				logging.info("didn't send mesg Flood to {}".format(i))
		for job in jobs:
			job.start()
			

	def send(self,vizinho,packet):
		(buffer,addr_recv) = self.vizinhos[vizinho].send(packet)
		if(buffer != None):
			return True
		else:
			print("send")
			self.rm_Vizinho(vizinho)
			if(self.mode=='server'):
				self.floodCC = True
			else:
				for host in self.table.getHosts():	
					self.send_FR_Direct(host)
			logging.debug(self.status())
			return False

	def recv(self,s,addr):
		inflag = True
		while self.flag and inflag:
			data = s.recv(1024)
			
			if(data == None):
				if(self.flag):
					print("receive")
					self.rm_Vizinho(addr)
				inflag = False
			elif(data[0] == 0): # FR
				logging.info("receive FR from {}:".format(addr))
				host = Packet.decode_FR(data)
				if self.mode == "server":
					self.floodCCLock.acquire()
					self.floodCC = True
					self.floodCCLock.release()
				elif self.mode == "client" or self.mode == "cliente ativo":
					self.send_FR(host)

			elif (data[0] == 1): # CC
				(host,ip,tempoI,tempos) = Packet.decode_CC(data)
				streamManager = self.__getStreamManagerOfHost(host)
				if(streamManager!=None):
					streamManager.setReceivedCC(True)

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

				if(streamManager != None and streamManager.isRunning()):
					streamManager.addSendingStream(addr)
				else: #Se não possuir a stream
					self.send_SA(addrDest,addr)
			else:
				logging.warning("Receive warning from {} data:{}".format(addr,data))

		logging.info("Sai recv {}".format(addr))

	def rm_Vizinho(self,addr):
		
		logging.info("Revmover Vizinho {}".format(addr))

		if(addr in self.vizinhos):
			self.vizinhos[addr].close()
			self.vizinhos.pop(addr)
			self.table.rmVizinho(addr)
			print("Removed vizinho")
		else:
			logging.info("Erro vizinho ja removido")
		self.status()
		
		if self.mode == "server":
			self.send_CC()
		elif self.mode == "client":
			self.send_FR_initial()

	def status(self):
		logging.debug("Vizinhos Ativos:{}".format(self.vizinhos.keys()))
		self.table.print()
		logging.debug("\n\n----------------------------------------------------------------------")


	def off(self):
		self.flag = False
		for i in self.vizinhos:
			self.vizinhos[i].close()
			logging.info("Vizinho Desconectado: {}".format(i))
		self.s.close()
		c = Connection()
		c.connect(("",PORTLOCAL))
		c.close()
		for i in self.streams:
			i.close()
		print("done")

	def nodeInterface(self):
		while(self.flag):
			print("Comando:")
			comando = input()
			if(comando=="off"):
				self.off()
			if(comando=="stream"):				
				threading.Thread(target=self.stream,args=())
			elif(comando=="sa1" and (self.mode=='client' or self.mode == "cliente ativo")):
				self.mode = 'cliente ativo'
				self.send_SA('Server1')
			elif(comando=="sa2" and (self.mode=='client' or self.mode == "cliente ativo")):
				self.mode = 'cliente ativo'
				self.send_SA('Server2')
			elif(comando=="list" and (self.mode=='client' or self.mode == "cliente ativo")):
				self.mode = 'cliente ativo'
				hosts = self.table.getHosts()
				for i in hosts:
					print(i)
			elif(comando=="sa" and (self.mode=='client' or self.mode == "cliente ativo")):
				self.mode = 'cliente ativo'
				hosts = self.table.getHosts()
				print("Escolha servidor:")
				comando = input()
				if comando in hosts:
					self.send_SA(comando) 
				
			elif(comando=="cc" and self.mode=='server'):
				self.send_CC()
			elif(comando=="watch" and self.mode == "cliente ativo"):
				threading.Thread(target=self.iniciaClientView).start()
				for stream in self.streams:
					stream.addSendingStream('',PORTSTREAMS)

if __name__ == '__main__':
	logging.basicConfig(format='%(message)s',level=logging.DEBUG)#(format='%(levelname)s:%(message)s',level=logging.DEBUG)
	parser = argparse.ArgumentParser()
	parser.add_argument("vizinhos",nargs="*")
	parser.add_argument("-m","--mode",choices=["server","client"],default="client")
	parser.add_argument("-n","--name",default=None)
	parser.add_argument("-i","--ip",default=IP_SERVER)
	
	args = parser.parse_args()

	t1 = Node(args.vizinhos,args.mode,args.name,args.ip)
	t1.nodeInterface()


#print(args.vizinhos,args.mode)


#t1 = Node(args.vizinhos,args.mode)
#t1.send(bytes("ola","utf-8"),sys.argv[1],12451)
