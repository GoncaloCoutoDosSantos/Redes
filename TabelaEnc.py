import time 
from Packet import Packet
import math

class TabelaEnc:
	def __init__(self,vizinhos):
		self.dicionario = {}
		self.hosts = []
		for vizinho in vizinhos:
			self.dicionario[vizinho] = []

	def addVizinho(self,vizinho):
		if vizinho not in self.dicionario:
			self.dicionario[vizinho] = []
		else:
			print("Vizinho Repetido")

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

	def shutDownVizinho(self,vizinho): #usar quando o vizinho nao responde
		self.dicionario[vizinho] = []

	def print(self):
		print("Tabela de encaminhamento")
		for i in self.hosts:
			v = self.bestVizinho(i)
			print("Servidor {}: {} custo {}".format(i,v,self.dicionario[v]))


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


	tabela.shutDownVizinho('127.0.0.1')
	print(tabela.bestVizinho('127.5.2.2'))


	print(tabela.recievePacket('127.0.0.2',packet2))
	time.sleep(0.5)
	print(tabela.recievePacket('127.0.0.1',packet2))
	print(tabela.bestVizinho('127.5.2.2'))


	print(tabela.recievePacket('127.0.0.1',packet3))
	time.sleep(0.5)
	print(tabela.recievePacket('127.0.0.2',packet3))
	print(tabela.bestVizinho('127.2.8.4'))