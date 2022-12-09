import time 
from Packet import Packet
import math
import logging
import threading 

class TabelaEnc:
	def __init__(self,vizinhos):
		self.lastWorking = None 
		self.dicionario = {}
		self.hosts = []
		self.lock = threading.RLock()
		for vizinho in vizinhos:
			self.dicionario[vizinho] = []

	def lockLock(self):
		self.lock.acquire()

	def unlockLock(self):
		self.lock.release()

	def updateTempoHost(self,vizinho, host,ip, timeTaken,timeInitial):
		print("updateTempoHost IP:",ip)
		novaLista = []
		self.lockLock()
		if host not in self.hosts: self.hosts.append(host)
		for (server,oldIp,timeTakenOld,timeInitialOld) in self.dicionario[vizinho]:
			if (server==host):
				if(timeInitial<=timeInitialOld): # se a mensagem for mais velha deita fora
					return False
			else: novaLista.append((server,oldIp,timeTakenOld,timeInitialOld))
		novaLista.append((host,ip,timeTaken,timeInitial))
		self.dicionario[vizinho] = novaLista

		if (self.bestVizinho(host)==vizinho):
			self.unlockLock()
			return True
		else:
			self.unlockLock()
			return False


	def bestVizinho(self,host):
		bestTime = math.inf
		bestVizinho = None

		self.lockLock()
		for vizinho in self.dicionario:
			for (server,ip,timeTaken,timeInitial) in self.dicionario[vizinho]:
				if (server==host and bestTime>timeTaken):
					bestTime=timeTaken
					bestVizinho=vizinho
		self.unlockLock()

		return bestVizinho


	def recievePacket(self,vizinho,packet):
		(host,ip,tempoI,tempos) = Packet.decode_CC(packet)   #todo update tempos
		timeTaken = time.time_ns()-tempoI
		print("recievePacket IP:",ip)
		return self.updateTempoHost(vizinho,host,ip,timeTaken,tempoI)  #retorna true se for para dar flood


	def addVizinho(self,vizinho):
		self.lockLock()
		if vizinho not in self.dicionario:
			self.dicionario[vizinho] = []
		else:
			print("add:Vizinho Repetido")
		self.unlockLock()


	def rmVizinho(self,vizinho): #TODO ao remover verificar se não existem mais entradas para o servidor, caso aconteça enviar msg de erro
		self.lockLock()
		if vizinho in self.dicionario:
			self.dicionario.pop(vizinho)
		else:
			print("rm:vizinho inexistente")
		self.unlockLock()


	def rmServerVizinho(self,serverDestino,vizinho): #Se retornar true então flood SBYE
		self.lockLock()
		if(self.bestVizinho(serverDestino)==None):
			return False #Se o servidor já não existir não faz nada

		tamanhoInicial = len(self.dicionario[vizinho])
		self.dicionario[vizinho][:] = ((server,ip,timeTakenOld,timeInitialOld) for (server,ip,timeTakenOld,timeInitialOld) in self.dicionario[vizinho] if server!=serverDestino)
		tamanhoFinal = self.dicionario[vizinho]
		self.unlockLock()

		if(tamanhoInicial == len(tamanhoFinal)):
			print("Tamanho inalterado")
		elif(tamanhoFinal==0): 
			return True #flood SBYE
		return False

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
	tempoInicial1 = time.time_ns()
	time.sleep(0.5)
	tempoInicial2 = time.time_ns()

	packet1 = Packet.encode_CC("Server",'127.5.2.2',tempoInicial1, [])
	packet2 = Packet.encode_CC("Server",'127.5.2.2',tempoInicial2, [])
	packet3 = Packet.encode_CC("Server",'127.2.8.4',tempoInicial1, [])

	print(tabela.recievePacket('127.0.0.1',packet1))
	time.sleep(0.5)
	print(tabela.recievePacket('127.0.0.2',packet1))
	print(tabela.bestVizinho('127.5.2.2'))
	tabela.print()
	print(tabela.recievePacket('127.0.0.2',packet3))
	tabela.rmServerVizinho('127.5.2.2','127.0.0.2')
	print("yo")
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