import time 
from Packet import Packet
import math

class TabelaEnc:
	def __init__(vizinhos):
		self.dicionario = {}
		for vizinho in vizinhos:
			self.dicionario[vizinho] = []

	def updateTempoHost(vizinho, host, timeTaken,timeInitial):
		novaLista = []
		for (server,timeTakenOld,timeInitialOld) in self.dicionario[vizinho]:
			if (server==host):
				if(timeInitial<=timeInitialOld):
					return False
				else:
					novaLista.append((host,timeTaken,timeInitial))
					return True
			else: novaLista.append((server,timeTakenOld,timeInitialOld))

		novaLista.append((host,timeTaken,timeInitial))
		return True

	def bestVizinho(host):
		bestTime = math.inf
		bestVizinho = None
		for vizinho in self.dicionario:
			for (server,timeTaken,timeInitial) in vizinho:
				if (server==host and bestTime==timeTaken):
					bestTime=timeTaken
					bestVizinho=vizinho
		return bestVizinho

	def recievePacket(vizinho,packet):
		(host,tempoI,tempos) = Packet.decode_CC(packet)   #todo update tempos
		timeTaken = time.time_ns()-tempoI

		return TabelaEnc.updateTempoHost(vizinho,host,timeTaken,tempoI)  #retorna true se for para dar flood




