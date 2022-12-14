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

	def encode_FR(host): #Flood request
		array = bytearray(1 + 1 + len(host))
		array[0] = int(0)
		array[1] = len(host)
		ind = 2
		for i in host: #Puthost
			array[ind] = ord(i)
			ind += 1
		return array

	def decode_FR(packet): #Flood request
		length = packet[1]
		host = packet[2:2+length].decode("utf-8") #Ip do router original
		return host

	def encode_CC(name,ip,tempoI,tempos = []):
		array = bytearray(1 + 1 + len(name)+ 1 + len(ip))
		array[0] = int(1)
		array[1] = len(name)
		ind = 2
		for i in name: #Put IP host
			array[ind] = ord(i)
			ind += 1

		array[ind]= len(ip)
		ind += 1
		for i in ip:
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
		host = packet[2:2+length].decode("utf-8") #Nome do servidor original
		ind = 2+length
		length = packet[ind]
		ind += 1
		ip= packet[ind:ind+length].decode("utf-8") #Ip do router original
		ind+= length
		tempoI = int.from_bytes(packet[ind:ind+10],'big')
		tempos = []
		ind = ind + 10
		length = int.from_bytes(packet[ind:ind + 4],'big')
		ind = ind + 4
		for i in range(length): 
			tempos.append(int.from_bytes(packet[ind:ind+10],'big'))
			ind += 10
		return (host,ip,tempoI,tempos)

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

	def encode_STREAM(packet,tempoI): #Stream
		array = bytearray(1)	
		array[0] = int(3)
		tempoByteA = tempoI.to_bytes(10,'big')
		return array+tempoByteA+packet

	def decode_STREAM(packet): #Stream
		tempoI = int.from_bytes(packet[1:1+10],'big')
		return (packet[1+10:],tempoI)

	def encode_LD(): #Loop Detected
		array = bytearray(1)	
		array[0] = int(4)
		return array

if __name__ == '__main__':
	vizinhos = {}
	vizinhos["10.0.0.21"] = "ola"
	vizinhos["10.0.1.20"] = "ola"

	#pacote = Packet.encode_SA("bronze")
	#origem = Packet.decode_SA(pacote)
	#print("Origem:"+origem)
	#t = time.time_ns()
	#print(t)
	packet1 = Packet.encode_CC("Setefi",'127.0.0.1',123)
	packetStream = Packet.encode_STREAM(packet1,389021380921)
	(packet2,tempo) = Packet.decode_STREAM(packetStream)
	print(Packet.decode_CC(packet1))
	#(name,ip,tempoI,tempos) = Packet.decode_CC(packet)
	#print("yo")
	#print(packet)
	#print(Packet.decode_CC(packet))

	#packet = Packet.encode_LSA("n2",vizinhos) 

	#print(packet)

	#ret = Packet.decode_LSA(packet)
	#print(ret)