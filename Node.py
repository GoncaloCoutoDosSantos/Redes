import socket, threading, sys

class Node:
	def __init__(self,vizinhos,port = 12451):
		self.flag = True
		self.host = vizinhos[0] #cant be local host 
		print("IP:",self.host)
		self.port = port
		self.vizinhos_all = vizinhos[1:]
		print("Todos vizinhos:",self.vizinhos_all)
		
		self.vizinhos = {}

		#tenta ligar se aos vizinhos(ve os que estao ativos)
		for i in vizinhos[1:]:
			s = socket.socket()
			try:
				s.connect((i,self.port))
				self.vizinhos[i] = s
				print("Vizinho Ativo:",i)
				threading.Thread(target=self.recv,args=(s,i)).start()
			except:
				s.close()
				print("node {} not active".format(i))

		print("Vizinhos Ativos:",self.vizinhos.keys())

		self.s = socket.socket()
		self.s.bind((self.host,port))

		#listen for new connections
		self.s.listen(5)
		while self.flag:
			c, addr = self.s.accept()
			print('Got connection from', addr)
			print("{} in {}:{}".format(addr[0],self.vizinhos_all,addr in self.vizinhos_all))
			if(addr[0] in self.vizinhos_all):
				self.vizinhos[addr] = c
				threading.Thread(target=self.recv,args=(c,addr)).start()
				print("Vizinhos Ativos:",self.vizinhos.keys())
			else:
				c.close()


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
			print("receive data from {}:{}".format(addr,data))

	def close(self):
		self.s.close();


t1 = Node(sys.argv[1:])
#t1.send(bytes("ola","utf-8"),sys.argv[1],12451)