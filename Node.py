import socket, threading, sys
from socket import AF_INET,SOCK_DGRAM
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time
import logging
from Connection import Connection
from tkinter import Tk
from Client import Client
from ServerWorker import ServerWorker
from RelayNode import RelayNode

CC_TIME = 30

class Node:
	top = {}
	def __init__(self,vizinhos,mode,port = 12459):
		self.mode = mode
		logging.info("Mode:{}".format(self.mode))
		self.flag = True
		self.host =  socket.gethostname() #cant be local host 
		logging.info("IP:{}".format(self.host))
		self.port = port
		self.vizinhos_all = vizinhos
		self.streams = []
		self.SAConfirmations = []
		logging.info("Todos vizinhos:{}".format(self.vizinhos_all))
		
		#self.top[self.host] = []
		self.vizinhos = {}


		#tenta ligar se aos vizinhos(ve os que estao ativos)
		self.table = TabelaEnc([])
		for i in vizinhos:
			s = Connection()
			if s.connect((i,self.port)):
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

		self.status()

		threading.Thread(target=self.listener,args=()).start()


	def listener(self):
		self.s = socket.socket(AF_INET,SOCK_DGRAM)
		self.s.bind(("",self.port))

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

		sent = False
		while(not sent):
			if(vizinho==None):
				logging.debug("Não há caminho conhecido para o servidor no SA")
				self.send_SBYE(serverDestino)
				sent = True
			else:
				logging.debug("Send SA")
				packet = Packet.encode_SA(serverDestino)
				sent=self.send(vizinho,packet)

	def send_CC(self):
		logging.debug("Send CC")
		packet = Packet.encode_CC(self.host,time.time_ns())
		jobs = []
		for i in self.vizinhos:
			jobs.append(threading.Thread(target=self.send,args=(i,packet)))
		
		for job in jobs:
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

	def send_SBYE(self,serverIndisponivel): #TODO test
		logging.debug("Send SBYE")
		packet = Packet.encode_SBYE(serverIndisponivel)
		for i in self.vizinhos:
			self.send(i,packet)

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
				(host,tempoI,tempos) = Packet.decode_CC(data)
				logging.debug("Host: {} | TempoI: {} | Tempos: {}".format(host,tempoI,tempos)) 
				if host != self.host:
					t = time.time_ns()
					diff_t = t - tempoI
					if(self.table.updateTempoHost(addr,host,diff_t,tempoI)):
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

				
				if self.mode=="server":#inicializa serverworker
					try:
						SERVER_PORT = 4000
					except:
						print("Unocupied Server Port\n")
					rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					rtspSocket.bind(('', SERVER_PORT))
					rtspSocket.listen(5)        

					# Receive client info (address,port) through RTSP/TCP session
					clientInfo = {}
					clientInfo['rtspSocket'] = rtspSocket.accept()
					threading.Thread(target=ServerWorker(clientInfo).run(),args=())  
				else:
					for (server,[entrada],saida,conteudo) in self.streams: #junta-se a outro stream
						if(server==addrDest): #Se tiver a stream vai começar a enviar
							# TODO arranjar maneira de juntar ao threading, acho q é inicializar a thread com variaveis self. que alterar quando precisas
							saida = saida + [addr]
							hasStream = True
							logging.info("Stream sent")
					if(not hasStream): #Se não possuir a stream
						vizinho = self.table.bestVizinho(addrDest)
						
						if(vizinho==None): #Caso não haja caminho para a stream flood SBYE TODO atenção a este caso porque deve ser só redondante
							self.send_SBYE(addrDest)
						else: #Caso contrário vai pedir ao nodo mais rapido
							self.SAConfirmations = self.SAConfirmations + [(addr,addrDest)]
							self.send_SA(addrDest)
							logging.info("Esperar resposta")
							#Esperar por resposta??
							#Criar RelayNode
							try:
								OVERLAY_PORT = 4000
							except:
								print("Unocupied Server Port\n")
							#Client side rtsp socket
							rtspCSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
							rtspCSocket.bind(('', OVERLAY_PORT))
							rtspCSocket.listen(5)     
							#Server side rtsp socket
							rtspSSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
							rtspSSocket.bind(('', OVERLAY_PORT+1))
							rtspSSocket.listen(5)  
							# Receive client info (address,port) through RTSP/TCP session

							clientInfo = {}
							clientInfo['rtspSocket'] = rtspCSocket.accept()
							serverInfo = {}
							serverInfo['rtspSocket'] = rtspSSocket.accept()
							#TODO adicionar ao RelayNode outras informações na inicialização como nome do conteudo, endereços de entrada e saida ...
							threading.Thread(target=RelayNode(clientInfo,serverInfo).run(),args=())
							logging.info("Criado RelayNode")


			elif (data[0] == 3): #TODO test
				logging.info("receive SBYE from {}:".format(addr))
				serverToRemove = Packet.decode_FR(data)
				if(self.table.rmServerVizinho(serverToRemove,addr)): #rmServerVizinho deteta se é necessario enviar SBYE
					self.send_SBYE(addrDest)

			else:
				logging.warning("Receive from {} data:{}".format(addr,data))

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

	def stream(self):
		#TODO aqui precisas de começar a mandar a primeira msg SA
		print("Choose RtpPort(n tem safeguard):")
		rtpPort = input()
		hosts = self.table.getHosts
		nextNode = False
		'''
		print("Choose Streaming Server:")
		for i in hosts:
			print("Server{}: {}",i,hosts[i])
		while(not nextNode):
			print("Input:")
			choice = int(input())
			if(choice >= 0 and choice<len(hosts)):
				nextNodeAddr = self.table.bestVizinho(hosts[int(input())])
				nextNode = True
		'''
		nextNodeAddr=self.table.bestVizinho(self.host)
		print("Choose Streaming Port(n tem safeguard):")
		
		serverPort = input()

		root = Tk()
		fileName = "movie.Mjpeg"

		# Create a new client
		app = threading.Thread(target=Client(root, nextNodeAddr, serverPort, rtpPort, fileName),args=()) 
		app.master.title("RTPClient")	
		root.mainloop()

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
