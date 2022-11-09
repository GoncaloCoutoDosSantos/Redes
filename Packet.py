
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

	def encode_LSA(addr,vizinhos_dic):
		vizinhos = vizinhos_dic.keys()
		packet = bytearray(1 + 1 + len(addr) + 1 + (len(vizinhos) * 5))
		packet[0] = 0 # Set mode LSA
		packet[1] = len(addr)
		ind = 2
		for i in addr:
			packet[ind] = ord(i)
			ind = ind + 1

		packet[ind] = len(vizinhos)# Number of vizinhos
		ind = ind + 1
		for i in vizinhos:
			Packet.ip_to_byte(i,packet,ind) # IP vizinhos
			ind = ind + 4
			packet[ind] = 1 #Set Custo
			ind = ind + 1
		return packet

	def decode_LSA(packet):
		#Packet LSA
		print("Receive LSA packet")
		host = packet[2:2 + packet[1]].decode("utf-8")
		print(host)
		vizinhos = []
		ind = 2 + packet[1] + 1
		for i in range(packet[ind-1]): # Percorre lista dos ip dos vizinhos
			vizinhos.append((Packet.byte_to_ip(packet[ind:]),packet[ind + 4]))
			ind = ind + 5
		return (host,vizinhos)




if __name__ == '__main__':
	vizinhos = {}
	vizinhos["10.0.0.21"] = "ola"
	vizinhos["10.0.1.20"] = "ola"

	packet = Packet.encode_LSA("n2",vizinhos) 

	print(packet)

	ret = Packet.decode_LSA(packet)
	print(ret)

