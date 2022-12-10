import time

HEADER_SIZE = 12

#################################################################



#			TODO

# Erro quando perde acesso ao servidor mandar para tras a informar os outros nos 
# Novo packet referente a tabela de encaminhamento que informa outros nodos que ja nao conseguem chegar ao servidor por aquele nodo 
# Condiçao de paragem nao conseguje remover aquele path da tablea de encaminhamento devido a ela ja n existir



class Packet:
	def __init__():
		pass

	def ip_to_byte(ip,arr,ind = 0):
		ip = ip.split(".")
		for i in range(4):
			arr[ind + i] = int(ip[i])

	def byte_to_ip(arr):
		ret = ""
		ret = ret + str(arr[0])
		for i in range(1,4):
			ret = ret + "." + str(arr[i])
		return ret

	def encode_FR(): #Flood request
		array = bytearray(1)
		array[0] = int(0)
		return array

	def decode_FR(packet): #Flood request
		return packet[0]

	def encode_CC(addr,tempoI,tempos = []):
		array = bytearray(1 + 1 + len(addr))
		array[0] = int(1)
		array[1] = len(addr)
		ind = 2
		for i in addr: #Put IP host
			array[ind] = ord(i)
			ind += 1
		tempoByteA = tempoI.to_bytes(10,'big')
		tamanho = len(tempos).to_bytes(4,'big')
		temposByteA = []
		for i in tempos:
			temposByteA.append(i.to_bytes(10,'big'))
		return array+tempoByteA+tamanho+tempoByteA

	def decode_CC(packet):
		#print(packet)
		#print("Receive CC packet")
		length = packet[1]
		host = packet[2:2+length].decode("utf-8") #Ip do router original
		ind = 2+length
		tempoI = int.from_bytes(packet[ind:ind+10],'big')
		tempos = []
		ind = ind + 10
		length = int.from_bytes(packet[ind:ind + 4],'big')
		ind = ind + 4
		for i in range(length): 
			tempos.append(int.from_bytes(packet[ind:ind+10],'big'))
			ind += 10
		return (host,tempoI,tempos)

	def encode_SA(addr): #Stream ASK TODO para alem do addr tb precisas de outras informações como nome do conteudo
		array = bytearray(1 + 1 + len(addr))
		array[0] = int(2)
		array[1] = len(addr)
		ind = 2
		for i in addr: #Put IP host
			array[ind] = ord(i)
			ind += 1
		return array

	def decode_SA(packet): #Stream ASK
		length = packet[1]
		addr = packet[2:2+length].decode("utf-8") #Ip do router original
		return addr

	def encode_SBYE(addr): #Node with no acess to server addr
		array = bytearray(1 + 1 + len(addr))
		array[0] = int(3)
		array[1] = len(addr)
		ind = 2
		for i in addr: #Put IP host
			array[ind] = ord(i)
			ind += 1
		return array

	def decode_SBYE(packet): #Node with no acess to server addr
		length = packet[1]
		addr = packet[2:2+length].decode("utf-8") #Ip do router original
		return addr

	def encodeRTP(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
		"""Encode the RTP packet with header fields and payload."""
		timestamp = int(time())
		header = bytearray(HEADER_SIZE)
		header[0] = int(4)#version
		header[1] = int(pt)
		header[2] = int(extension)
		header[3] = int(seqnum)
		header[4] = int(cc)	
		header[5] = int(marker)
		header[6] = int(padding)
		header[7] = int(timestamp)
		header[8] = int(ssrc)
		self.payload = payload
		
	def decodeRTP(self, byteStream):
		"""Decode the RTP packet."""
		self.header = bytearray(byteStream[:HEADER_SIZE])
		self.payload = byteStream[HEADER_SIZE:]
	
	def version(self):
		"""Return RTP version."""
		return int(self.header[0] >> 6)

	def payloadType(self):
		"""Return payload type."""
		pt = self.header[1] & 127
		return int(pt)
		
	def seqNum(self):
		"""Return sequence (frame) number."""
		seqNum = self.header[2] << 8 | self.header[3]
		return int(seqNum)
	
	def timestamp(self):
		"""Return timestamp."""
		timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
		return int(timestamp)
	
	def getPayload(self):
		"""Return payload."""
		return self.payload
		
	def getRTPPacket(self):
		"""Return RTP packet."""
		return self.header + self.payload

if __name__ == '__main__':
	vizinhos = {}
	vizinhos["10.0.0.21"] = "ola"
	vizinhos["10.0.1.20"] = "ola"

	pacote = Packet.encode_SA("bronze")
	origem = Packet.decode_SA(pacote)
	print("Origem:"+origem)
	#t = time.time_ns()
	#print(t)
	#packet = Packet.encode_CC("Setefi",t)
	#print(packet)
	#print(Packet.decode_CC(packet))

	#packet = Packet.encode_LSA("n2",vizinhos) 

	#print(packet)

	#ret = Packet.decode_LSA(packet)
	#print(ret)

