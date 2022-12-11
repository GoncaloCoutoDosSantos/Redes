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
		for vizinho in vizinhos:
			self.dicionario[vizinho] = []

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
	# 	o flood é necessário caso o vizinho (que enviou transmitiu o CC) seja o mais rápido para o servidor adicionado
	def __updateTempoHost(self,vizinho, host,ip, timeTaken,timeInitial):
		novaLista = [] #Criar uma nova lista que vai repor a antiga
		self.lockLock()
		if host not in self.hosts: self.hosts.append(host) #Se o servidor não pertencer á lista de hosts então é adicionado

		for (server,oldIp,timeTakenOld,timeInitialOld) in self.dicionario[vizinho]: #iterar todos servidores do vizinho
			if (server==host): #Se o servidor estiver presente na lista de servidores
				if(timeInitial<=timeInitialOld): # caso a mensagem seja mais antiga ignora
					return False
				#Se a mensagem for mais nova, o servidor vai ser atualizar a entrada
			else: novaLista.append((server,oldIp,timeTakenOld,timeInitialOld)) #Adiciona o servidor já existente há nova lista (sem alterações)

		novaLista.append((host,ip,timeTaken,timeInitial)) #Adiciona/atualiza nova entrada do servidor á lista
		self.dicionario[vizinho] = novaLista #Atualiza a lista de servidores do vizinho

		bestVizinho = self.bestVizinho(host) #Calcula melhor vizinho para o servidor
		self.unlockLock()

		if (bestVizinho==vizinho): #Caso este vizinho seja o mais rápido então flood de CC
			return True
		else:
			return False

	# -------------------------------------------------------------------------------------------------------------------------------------------
	# Resumo: Atualiza a tabela de encaminhamento conforme o pacote CC
	#   É devolvido True se for necessario dar flood á mensagem CC caso contrário é devolvido False
	def recievePacket(self,vizinho,packet):
		(host,ip,tempoI,tempos) = Packet.decode_CC(packet) #Descodificar pacote
		timeTaken = time.time_ns()-tempoI	#Calcular o tempo que a mensagem demorou a chegar desde que o servidor a enviou
		return self.__updateTempoHost(vizinho,host,ip,timeTaken,tempoI)  #retorna true se for para dar flood

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
		else:
			print("add:Vizinho Repetido")
		self.unlockLock()


	# -------------------------------------------------------------------------------------------------------------------------------------------
	# Resumo: Remove vizinho e as suas entradas do dicionario de servidores
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

	packet1 = Packet.encode_CC("ServerName",'IP ADDRESS',tempoInicial1, [])
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