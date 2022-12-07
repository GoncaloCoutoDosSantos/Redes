import socket, threading, sys
from Packet import Packet
from TabelaEnc import TabelaEnc 
import argparse
import time

class Node:
	top = {}
	def __init__(self,vizinhos,mode,port = 12459):
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

		threading.Thread(target=self.listener,args=()).start()


	def listener(self):
		self.s = socket.socket()
		self.s.bind("",self.port)

		#listen for new connections
		self.s.listen(5)

		
		if(self.mode!='server'): #TODO tirar daqui Se nao for servidor pedir stream
			self.send_SA('Server')
		while self.flag:
			c, addr = self.s.accept()
			print('Got connection from', addr)
			print("{} in {}:{}".format(addr[0],self.vizinhos_all,addr[0] in self.vizinhos_all))
			if(True):#addr[0] in self.vizinhos_all):
				self.vizinhos[addr[0]] = c
				self.table.addVizinho(addr[0])
				threading.Thread(target=self.recv,args=(c,addr[0])).start()

				if(self.mode!='server'): #TODO tirar daqui Se nao for servidor pedir stream
					self.send_SA('Server')
				if self.mode=="server":
					self.send_CC()
				elif self.mode=="client":
					self.send_FR()

				self.status()
			else:
				c.close()

	def send_SA(self,serverDestino):
		print("Send SA")
		vizinho = self.table.bestVizinho(serverDestino)
		if(vizinho==None):
			print("Não há caminho conhecido para o servidor")
			return
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
			time.sleep(30)

	def send_FR(self):
		print("Send FR")
		packet = Packet.encode_FR()
		hosts = self.table.getHosts()
		print(hosts)
		vs = []
		for i in hosts:
			v = self.table.bestVizinho(i)
			if v not in vs:
				print(v)
				vs.append(v)
				self.send(v,packet)

	def send_SBYE(self,serverIndisponivel): #TODO test
		print("Send SBYE")
		packet = Packet.encode_SBYE(serverIndisponivel)
		for i in self.vizinhos:
			self.send(i,packet)

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
				print("receive FR from {}:".format(addr))
				mesg = Packet.decode_FR(data)
				if self.mode == "server":
					self.send_CC()
				elif self.mode == "client":
					self.send_FR()

			elif (data[0] == 1):
				print("receive CC from {}:".format(addr))
				(host,tempoI,tempos) = Packet.decode_CC(data)
				print("Host: {} | TempoI: {} | Tempos: {}".format(host,tempoI,tempos)) 
				if host != self.host:
					t = time.time_ns()
					diff_t = closet - tempoI
					if(self.table.updateTempoHost(addr,host,diff_t,tempoI)):
						self.send_flood(data,addr) 
					else:
						print("No flood")
				self.status()
			elif (data[0] == 2): #TODO test
				print("receive SA from {}:".format(addr))
				addrDest = Packet.decode_SA(data)
				print("Endereço destino: {}".format(addrDest)) 
				#Verifica se já tem a stream
				hasStream = False
				if self.mode=="server":
					print("Stream sent")
					return
				for (server,entrada,saida) in self.streams: 
					if(server==addrDest): #Se tiver a stream vai começar a enviar
						saida = saida + [addr]
						hasStream = True
						print("Stream sent")
						break
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
				print("receive SBYE from {}:".format(addr))
				serverToRemove = Packet.decode_FR(data)
				if(self.table.rmServerVizinho(serverToRemove,addr)): #rmServerVizinho deteta se é necessario enviar SBYE
					self.send_SBYE(addrDest)
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
			self.send_FR()

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

	def off(self):
		for i in self.vizinhos:
			self.vizinhos[i].close()
			print("Vizinho Desconectado: ",i)


	def on(self):
		for i in self.vizinhos_all:
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


	def nodeInterface(self):
		while(self.flag):
			print("Comando:")
			comando = input()
			if(comando=="off"):
				self.off()
			elif(comando=="on"):
				self.on()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("vizinhos",nargs="*")
	parser.add_argument("-m","--mode",choices=["server","client"],default="client")

	args = parser.parse_args()

	t1 = Node(args.vizinhos,args.mode)
	t1.nodeInterface()




#print(args.vizinhos,args.mode)


#t1 = Node(args.vizinhos,args.mode)
#t1.send(bytes("ola","utf-8"),sys.argv[1],12451)
