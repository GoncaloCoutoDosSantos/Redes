import time 
from Packet import Packet
import math
import logging
import threading 

class TabelaEnc:
	def __init__(self,vizinhos):
		self.dicionario = {}
		self.hosts = []
		self.lock = threading.RLock()
		self.hasSend = {}
		for vizinho in vizinhos:
			self.dicionario[vizinho] = []
			self.hasSend[vizinho] = []

	def lockLock(self):
		self.lock.acquire()

	def unlockLock(self):
		self.lock.release()



	# -------------------------------------------------------------------------------------------------------------------------------------------
	# Resumo: Atualiza a tabela de encaminhamento conforme os dados da mensagem CC
	# 	A entrada para o servidor pelo vizinho é atualizada/adicionada caso:
	#		 -O servidor não esteja presente na lista de servidores do vizinho (caso 1)
	#		 -A mensagem CC recebida for mais recente do que a presente na entrada já presente (caso 2)
	# 	Caso o servidor não esteja presente na lista de hosts então vai ser adicionado
	#   É devolvido True se for necessario dar flood á mensagem CC caso contrário é devolvido False
	# 	o flood é necessário quando o timeInitial da mensagem seja o mais recente (e único) de todas as entradas para o host
	def updateTempoHost(self,vizinho, host,ip, timeTaken,timeInitial, updateEntries= False):
		self.lockLock()
		if host not in self.hosts: self.hosts.append(host) #Se o servidor não pertencer á lista de hosts então é adicionado
	
		maisRecente = self.adicionaEntrada(vizinho, host,ip, timeTaken,timeInitial,updateEntries)
		appended = (host not in self.hasSend[vizinho])
		if(appended):
			self.hasSend[vizinho].append(host)

		self.unlockLock()

		if (maisRecente):
			return True
		else:
			return False

	def adicionaEntrada(self,vizinho, host,ip, timeTaken,timeInitial,updateEntries):
		flood = True
		self.lockLock()

		new = True
		for (hostOld,ipOld,timeTakenOld,timeInitialOld) in self.dicionario[vizinho]:
			if(hostOld==host):
				new = False
		if(new):
			self.dicionario[vizinho].append((host,ip, timeTaken,timeInitial))
		else:
			novos = 0
			for vizinhoTemp in self.dicionario:
				for (server,oldIp,timeTakenOld,timeInitialOld) in self.dicionario[vizinhoTemp]:
					if (server==host):
						if(timeInitialOld<timeInitial):
							if(vizinhoTemp==vizinho):
								self.dicionario[vizinhoTemp].remove((server,oldIp,timeTakenOld,timeInitialOld))
								self.dicionario[vizinhoTemp].append((host,ip, timeTaken,timeInitial))
							elif(timeTakenOld<timeTaken and updateEntries):
								self.dicionario[vizinhoTemp].remove((server,oldIp,timeTakenOld,timeInitialOld))
								self.dicionario[vizinhoTemp].append((server,oldIp,timeTaken+100000,timeInitialOld))
						else:
							novos+=1
			if(novos>=2):
				flood= False		
		self.unlockLock()
		return flood
	# -------------------------------------------------------------------------------------------------------------------------------------------
	# Resumo: Atualiza a tabela de encaminhamento conforme o pacote CC
	#   É devolvido True se for necessario dar flood á mensagem CC caso contrário é devolvido False
	def recievePacket(self,vizinho,packet):
		(host,ip,tempoI,tempos) = Packet.decode_CC(packet) #Descodificar pacote
		print("Host cc= "+ str(host))
		timeTaken = time.time_ns()-tempoI	#Calcular o tempo que a mensagem demorou a chegar desde que o servidor a enviou
		return self.updateTempoHost(vizinho,host,ip,timeTaken,tempoI, True)  #retorna true se for para dar flood

	# -------------------------------------------------------------------------------------------------------------------------------------------
	# Resumo: Calcula o melhor vizinho para um dado host
	#   Devolve o melhor vizinho
	# 	Se não houver nenhum vizinho para o host devolve None
	def bestVizinho(self,host):
		bestTime = math.inf
		bestVizinho = None
		
		self.lockLock()
		for vizinho in self.dicionario: #Iterar todos os vizinhos
			for (server,ip,timeTaken,timeInitial) in self.dicionario[vizinho]: #Iterar todos os servidores de cada vizinho
				if (server==host and bestTime>timeTaken): #Se o servidor do vizinho corresponder ao fornecido e seja o melhor até ao momento atualizar
					bestTime=timeTaken
					bestVizinho=vizinho
		self.unlockLock()
		return bestVizinho


	# -------------------------------------------------------------------------------------------------------------------------------------------
	# Resumo: Adiciona novo vizinho como chave no dicionario de servidores
	def addVizinho(self,vizinho):
		self.lockLock()
		if vizinho not in self.dicionario:
			self.dicionario[vizinho] = []
			self.hasSend[vizinho] = []
		else:
			print("add:Vizinho Repetido")
		self.unlockLock()


	# -------------------------------------------------------------------------------------------------------------------------------------------
	# Resumo: Remove vizinho e as suas entradas do dicionario de servidores
	def rmVizinho(self,vizinho): #TODO ao remover verificar se não existem mais entradas para o servidor, caso aconteça enviar msg de erro
		self.lockLock()
		if vizinho in self.dicionario:
			self.dicionario.pop(vizinho)
			self.hasSend.pop(vizinho)
		else:
			print("rm:vizinho inexistente")
		self.unlockLock()

	def getHostIp(self,host):
		self.lockLock()
		for vizinho in self.dicionario: #Iterar todos os vizinhos
			for (server,ip,timeTaken,timeInitial) in self.dicionario[vizinho]: #Iterar todos os servidores de cada vizinho
				if(server==host):
					self.unlockLock()
					return ip
		self.unlockLock()
		return None

	def getHostVizinhoEntry(self,vizinho, host): #Se retornar true então flood SBYE
		self.lockLock()
		for (server,oldIp,timeTakenOld,timeInitialOld) in self.dicionario[vizinho]:
			if(server == host):
				self.unlockLock()
				return (server,oldIp,timeTakenOld,timeInitialOld)
		self.unlockLock()
		return None

	def getHosts(self):
		return self.hosts


	def print(self):
		logging.debug("Tabela de encaminhamento")
		logging.debug("{}".format(self.dicionario))
		"""
		for i in self.hosts:
			v = self.bestVizinho(i)
			logging.debug("Servidor {}: {} custo {}".format(i,v,self.dicionario[v]))
		"""


if __name__ == '__main__':
	tabela = TabelaEnc(['127.0.0.1','127.0.0.2','127.0.0.3'])
	#tempoInicial1 = time.time_ns()
	#time.sleep(0.5)
	#tempoInicial2 = time.time_ns()
	tabela.updateTempoHost("127.0.0.1", "host","ip", 10,1)
	tabela.updateTempoHost("127.0.0.1", "host","ip", 10,1)
	tabela.updateTempoHost("127.0.0.2", "host","ip", 20,1)
	tabela.updateTempoHost("127.0.0.1", "host","ip", 10,2)
	pass

"""
	tabela.rmVizinho('127.0.0.1')
	print(tabela.bestVizinho('127.5.2.2'))


	print(tabela.recievePacket('127.0.0.2',packet2))
	time.sleep(0.5)
	print(tabela.recievePacket('127.0.0.1',packet2))
	print(tabela.bestVizinho('127.5.2.2'))


	print(tabela.recievePacket('127.0.0.1',packet3))
	time.sleep(0.5)
	print(tabela.recievePacket('127.0.0.2',packet3))
	print(tabela.bestVizinho('127.2.8.4'))
"""