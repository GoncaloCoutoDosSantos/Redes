
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
		return ret.encode("utf-8")

	def encode_LSA(addr,vizinhos_dic):
		vizinhos = vizinhos_dic.keys()
		packet = bytearray(6+ (len(vizinhos) * 5))
		packet[0] = 0 # Set mode LSA
		Packet.ip_to_byte(addr,packet,1) #Put IP host
		packet[5] = len(vizinhos)# Number of vizinhos
		ind = 6
		for i in vizinhos:
			Packet.ip_to_byte(i,packet,ind) # IP vizinhos
			ind = ind + 4
			packet[ind] = 1 #Set Custo
			ind = ind + 1
		return packet

	def decode_LSA(packet):
		#Packet LSA
		print("Receive LSA packet")
		host = Packet.byte_to_ip(packet[1:]) #Ip do router original
		vizinhos = []
		ind = 6
		for i in range(packet[5]): # Percorre lista dos ip dos vizinhos
			vizinhos.append((Packet.byte_to_ip(packet[ind:]),packet[ind + 4]))
			ind = ind + 5
		return (host,vizinhos)




if __name__ == '__main__':
	vizinhos = {}
	vizinhos["10.0.0.21"] = "ola"
	vizinhos["10.0.1.20"] = "ola"

	packet = Packet.encode_lsa("10.0.0.20",vizinhos) 

	print(packet)
	print(Packet.decode(packet))

