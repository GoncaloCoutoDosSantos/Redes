import socket, threading, sys
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time

class Node:
	top = {}
	def __init__(self,vizinhos,mode,port = 12456):
		self.mode = mode
		print("Mode:",self.mode)
		self.flag = True
		self.host =  socket.gethostname() #cant be local host 
		print("IP:",self.host)
		self.port = port
		self.vizinhos_all = vizinhos
		self.streams = []
		self.SAConfirmations = []
		print("Todos vizinhos:",self.vizinhos_all)
		
		#self.top[self.host] = []
		self.vizinhos = {}

		#tenta ligar se aos vizinhos(ve os que estao ativos)
		for i in vizinhos:
			s = socket.socket()
			try:
				s.connect((i,self.port))
				self.vizinhos[i] = s
				#self.top[self.host].append(i)
				print("Vizinho Ativo:",i)
				threading.Thread(target=self.recv,args=(s,i)).start()
			except:
				s.close()
				print("node {} not active".format(i))

		self.table = TabelaEnc(self.vizinhos.keys())
		self.table.print()

		#self.send_LSA()
		if self.mode=="server":
			self.send_CC()

		self.status()

		self.s = socket.socket()
		self.s.bind(("",port))

		#listen for new connections
		self.s.listen(5)
		while self.flag:
			c, addr = self.s.accept()
			print('Got connection from', addr)
			print("{} in {}:{}".format(addr[0],self.vizinhos_all,addr[0] in self.vizinhos_all))
			if(True):#addr[0] in self.vizinhos_all):
				self.vizinhos[addr[0]] = c
				self.table.addVizinho(addr[0])
				self.table.print()
				threading.Thread(target=self.recv,args=(c,addr[0])).start()
				#self.top[self.host].append((addr[0],1))
				#self.send_LSA()
				self.status()
			else:
				c.close()

	def send_SA(self,serverDestino):
		vizinho = self.table.bestVizinho(serverDestino)
		packet = Packet.encode_SA(serverDestino)
		self.vizinhos[vizinho].send(packet)

	def send_CC(self):
		packet = Packet.encode_CC(self.host,time.time_ns())
		for i in self.vizinhos:
			self.vizinhos[i].send(packet)

	def send_LSA(self):
		print("host"+str(self.host))
		packet = Packet.encode_LSA(self.host,self.vizinhos)
		for i in self.vizinhos:
				print(type(self.vizinhos[i]))
				self.vizinhos[i].send(packet)

	def send_flood(self,packet,addr = ""):
		for i in self.vizinhos:
			if i != addr:
				self.vizinhos[i].send(packet)

	#call to create treat to send
	def send_normal(self,msg,host,port):
		s = socket.socket()
		s.connect((host,port))
		s.send(msg)

	#threaed send
	def send(self,msg,host,port):
		threading.Thread(target=self.send_normal,args=(msg,host,port)).start()

	def recv(self,s,addr):
		while self.flag:
			data  = s.recv(1024)
			if(data[0] == 0):
				print("receive LSA from {}:".format(addr))
				ori,vizinhos = Packet.decode_LSA(data)
				print("Origem: {} | Vizinhos: {}".format(ori,vizinhos))
				
				if(not(ori in self.top) or self.top[ori] != vizinhos):
					self.top[ori] = vizinhos
					self.send_flood(data)
					self.status()
			elif (data[0] == 1):
				print("receive CC from {}:".format(addr))
				(host,tempoI,tempos) = Packet.decode_CC(data)
				print("Host: {} | TempoI: {} | Tempos: {}".format(host,tempoI,tempos)) 
				if host != self.host:
					t = time.time_ns()
					diff_t = t - tempoI
					if(self.table.updateTempoHost(addr,host,diff_t,tempoI)):
						self.send_flood(data,addr) 
				self.table.print()
			elif (data[0] == 2):
				print("receive CC from {}:".format(addr))
				addrDest = Packet.decode_SA(data)
				print("Endereço destino: {}".format(addrDest)) 
				#Verifica se já tem a stream
				for (server,entrada,saida) in self.streams:
					if(server==addrDest):
						saida = saida + [addr]
					else:
						vizinho = self.table.bestVizinho(addrDest)
						if(vizinho==None):
							#retorna mensagem de erro
							vizinho=None
						else:
							self.SAConfirmations = self.SAConfirmations + [addrDest]
							self.send_SA(addrDest)

			else:
				print("Receive from {} data:{}".format(addr,data))

	def status(self):
		print("Vizinhos Ativos:",self.vizinhos.keys())
		#print("Topologia:")
		#for i in self.top:
			#print("Node {}:{}".format(i,self.top[i]))

	def close(self):
		pass
		#self.s.close();


parser = argparse.ArgumentParser()
parser.add_argument("vizinhos",nargs="*")
parser.add_argument("-m","--mode",choices=["server","client"],default="client")

args = parser.parse_args()
#print(args.vizinhos,args.mode)


t1 = Node(args.vizinhos,args.mode)
#t1.send(bytes("ola","utf-8"),sys.argv[1],12451)