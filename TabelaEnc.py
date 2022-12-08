import time 
from Packet import Packet
import math
import logging

class TabelaEnc:
	def __init__(self,vizinhos):
		self.lastWorking = None 
		self.dicionario = {}
		self.hosts = []
		for vizinho in vizinhos:
			self.dicionario[vizinho] = []


	def updateTempoHost(self,vizinho, host, timeTaken,timeInitial):
		novaLista = []
		if host not in self.hosts: self.hosts.append(host)
		for (server,timeTakenOld,timeInitialOld) in self.dicionario[vizinho]:
			if (server==host):
				if(timeInitial<=timeInitialOld): # se a mensagem for mais velha deita fora
					return False
			else: novaLista.append((server,timeTakenOld,timeInitialOld))
		novaLista.append((host,timeTaken,timeInitial))
		self.dicionario[vizinho] = novaLista
		if (self.bestVizinho(host)==vizinho):
			return True
		else: return False


	def bestVizinho(self,host):
		bestTime = math.inf
		bestVizinho = None
		for vizinho in self.dicionario:
			for (server,timeTaken,timeInitial) in self.dicionario[vizinho]:
				if (server==host and bestTime>timeTaken):
					bestTime=timeTaken
					bestVizinho=vizinho
		return bestVizinho


	def recievePacket(self,vizinho,packet):
		(host,tempoI,tempos) = Packet.decode_CC(packet)   #todo update tempos
		timeTaken = time.time_ns()-tempoI

		return self.updateTempoHost(vizinho,host,timeTaken,tempoI)  #retorna true se for para dar flood


	def addVizinho(self,vizinho):
		if vizinho not in self.dicionario:
			self.dicionario[vizinho] = []
		else:
			print("add:Vizinho Repetido")


	def rmVizinho(self,vizinho): #todo ao remover verificar se não existem mais entradas para o servidor, caso aconteça enviar msg de erro
		if vizinho in self.dicionario:
			self.dicionario.pop(vizinho)
		else:
			print("rm:vizinho inexistente")


	def rmServerVizinho(self,serverDestino,vizinho): #Se retornar true então flood SBYE
		if(self.bestVizinho(serverDestino)==None):
			return False #Se o servidor já não existir não faz nada

		tamanhoInicial = len(self.dicionario[vizinho])
		self.dicionario[vizinho][:] = ((server,timeTakenOld,timeInitialOld) for (server,timeTakenOld,timeInitialOld) in self.dicionario[vizinho] if server!=serverDestino)
		tamanhoFinal = self.dicionario[vizinho]
		
		if(tamanhoInicial == len(tamanhoFinal)):
			print("Tamanho inalterado")
		elif(tamanhoFinal==0): 
			return True #flood SBYE
		return False

	def getHosts(self):
		return self.hosts


	def print(self):
		logging.debug("Tabela de encaminhamento")
		for i in self.hosts:
			v = self.bestVizinho(i)
			logging.debug("Servidor {}: {} custo {}".format(i,v,self.dicionario[v]))


if __name__ == '__main__':
	tabela = TabelaEnc(['127.0.0.1','127.0.0.2','127.0.0.3'])
	tempoInicial1 = time.time_ns()
	time.sleep(0.5)
	tempoInicial2 = time.time_ns()

	packet1 = Packet.encode_CC('127.5.2.2',tempoInicial1, [])
	packet2 = Packet.encode_CC('127.5.2.2',tempoInicial2, [])
	packet3 = Packet.encode_CC('127.2.8.4',tempoInicial1, [])

	print(tabela.recievePacket('127.0.0.1',packet1))
	time.sleep(0.5)
	print(tabela.recievePacket('127.0.0.2',packet1))
	print(tabela.bestVizinho('127.5.2.2'))

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