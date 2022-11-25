import socket, threading, sys
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time

class Node:
	top = {}
	def __init__(self,vizinhos,mode,port = 12452):
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

		#self.send_LSA()
		if self.mode=="server":
			threading.Thread(target=self.send_CC_thread,args=()).start()

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
				threading.Thread(target=self.recv,args=(c,addr[0])).start()

				if self.mode=="server":
					self.send_CC()
				elif self.mode=="client":
					self.send_HELLO()

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
			self.send(i,packet)

	def send_CC_thread(self):
		while self.flag:
			print("send CC")	
			self.send_CC()
			time.sleep(60)

	def send_HELLO(self):
		print("Send Hello")
		packet = Packet.encode_HELLO()
		hosts = self.table.getHosts()
		print(hosts)
		vs = []
		for i in hosts:
			v = self.table.bestVizinho(i)
			if v not in vs:
				print(v)
				vs.append(v)
				self.send(v,packet)

	def send_flood(self,packet,addr = ""):
		for i in self.vizinhos:
			if i != addr:
				print("send mesg to {}".format(i))
				self.send(i,packet)
			else:
				print("didn't send to {}".format(i))

	def send(self,i,packet):
		try:
			self.vizinhos[i].send(packet)
		except:
			self.rm_Vizinho(i)


	def recv(self,s,addr):
		inflag = True
		while self.flag and inflag:
			data = []
			try:
				data = s.recv(1024)
			except:pass
			
			if(len(data) == 0):
				self.rm_Vizinho(addr)
				inflag = False
			elif(data[0] == 0):
				print("receive Hello from {}:".format(addr))
				mesg = Packet.decode_HELLO(data)
				if self.mode == "server":
					self.send_CC()
				elif self.mode == "client":
					self.send_HELLO()

			elif (data[0] == 1):
				print("receive CC from {}:".format(addr))
				(host,tempoI,tempos) = Packet.decode_CC(data)
				print("Host: {} | TempoI: {} | Tempos: {}".format(host,tempoI,tempos)) 
				if host != self.host:
					t = time.time_ns()
					diff_t = t - tempoI
					if(self.table.updateTempoHost(addr,host,diff_t,tempoI)):
						self.send_flood(data,addr) 
					else:
						print("No flood")
				self.status()
			elif (data[0] == 2):
				print("receive CC from {}:".format(addr))
				addrDest = Packet.decode_SA(data)
				print("Endereço destino: {}".format(addrDest)) 
				#Verifica se já tem a stream
				for (server,entrada,saida) in self.streams: 
					if(server==addrDest): #Se tiver a stream vai começar a enviar
						saida = saida + [addr]
					else: #Se não possuir a stream
						vizinho = self.table.bestVizinho(addrDest)
						if(vizinho==None): #Caso não haja caminho para a stream devolve erro
							#retorna mensagem de erro
							vizinho=None
						else: #Caso contrário vai pedir ao nodo
							self.SAConfirmations = self.SAConfirmations + [(addr,addrDest)]
							self.send_SA(addrDest)

			else:
				print("Receive from {} data:{}".format(addr,data))
		print("Sai recv {}".format(addr))

	def rm_Vizinho(self,addr):
		self.vizinhos.pop(addr)
		self.table.rmVizinho(addr)
		self.status()
		if self.mode == "server":
			self.send_CC()
		elif self.mode == "client":
			self.send_HELLO()

	def status(self):
		print("Vizinhos Ativos:",self.vizinhos.keys())
		#print("Topologia:")
		#for i in self.top:
			#print("Node {}:{}".format(i,self.top[i]))
		self.table.print()
		print("\n\n----------------------------------------------------------------------")

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
