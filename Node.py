import socket, threading, sys
from socket import AF_INET,SOCK_DGRAM
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time
import logging
from Connection import Connection

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
		for i in vizinhos:
			s = Connection()
			if s.connect((i,self.port)):
				self.vizinhos[i] = s
				logging.debug("Vizinho Ativo:".format(i))
				threading.Thread(target=self.recv,args=(s,i)).start()
			else:
				#s.close()
				logging.debug("node {} not active".format(i))

		self.table = TabelaEnc(self.vizinhos.keys())

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
		if(vizinho==None):
			logging.debug("Não há caminho conhecido para o servidor no SA")
		else:
			logging.debug("Send SA")
			packet = Packet.encode_SA(serverDestino)
			self.send(vizinho,packet)

	def send_CC(self):
		logging.debug("Send CC")
		packet = Packet.encode_CC(self.host,time.time_ns())
		for i in self.vizinhos:
			self.send(i,packet)

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
		try:
			self.vizinhos[i].send(packet)
		except:
			self.rm_Vizinho(i)


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
				logging.debug("Endereço destino: {}".format(addrDest)) 
				#Verifica se já tem a stream
				hasStream = False
				if self.mode=="server":
					logging.debug("Stream sent")
				else:
					for (server,entrada,saida) in self.streams: 
						if(server==addrDest): #Se tiver a stream vai começar a enviar
							saida = saida + [addr]
							hasStream = True
							print("Stream sent")
					if(not hasStream): #Se não possuir a stream
						vizinho = self.table.bestVizinho(addrDest)
						if(vizinho==None): #Caso não haja caminho para a stream flood SBYE TODO atenção a este caso porque deve ser só redondante
							self.send_SBYE(addrDest)
						else: #Caso contrário vai pedir ao nodo mais rapido
							self.SAConfirmations = self.SAConfirmations + [(addr,addrDest)]
							self.send_SA(addrDest)
							print("Esperar resposta")
							#Esperar por resposta??

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


	def nodeInterface(self):
		while(self.flag):
			print("Comando:")
			comando = input()
			if(comando=="off"):
				self.off()
				self.flag = not self.flag
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
