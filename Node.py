import socket, threading, sys
from Packet import Packet

class Node:
	top = {}
	def __init__(self,vizinhos,port = 12455):
		self.flag = True
		self.host =  socket.gethostname() #cant be local host 
		print("IP:",self.host)
		self.port = port
		self.vizinhos_all = vizinhos
		print("Todos vizinhos:",self.vizinhos_all)
		
		self.top[self.host] = []
		self.vizinhos = {}

		#tenta ligar se aos vizinhos(ve os que estao ativos)
		for i in vizinhos[1:]:
			s = socket.socket()
			try:
				s.connect((i,self.port))
				self.vizinhos[i] = s
				self.top[self.host].append(i)
				print("Vizinho Ativo:",i)
				threading.Thread(target=self.recv,args=(s,i)).start()
			except:
				s.close()
				print("node {} not active".format(i))

		self.send_LSA()
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
				threading.Thread(target=self.recv,args=(c,addr)).start()
				self.top[self.host].append((addr[0],1))
				self.send_LSA()
				self.status()
			else:
				c.close()

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
			else:
				print("Receive from {} data:{}".format(addr,data))

	def status(self):
		print("Vizinhos Ativos:",self.vizinhos.keys())
		print("Topologia:")
		for i in self.top:
			print("Node {}:{}".format(i,self.top[i]))

	def close(self):
		pass
		#self.s.close();


t1 = Node(sys.argv[1:])
#t1.send(bytes("ola","utf-8"),sys.argv[1],12451)