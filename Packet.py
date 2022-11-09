
class Packet:
	def __init__():
	 	pass

	def ip_to_byte(ip,arr,ind = 0):
		ip = ip.split(".")
		for i in range(4):
			arr[ind + i] = int(ip[i])

	def encode_lsa(addr,vizinhos_dic):
		vizinhos = vizinhos_dic.keys()
		packet = bytearray(6+ (len(vizinhos) * 5))
		packet[0] = 0
		Packet.ip_to_byte(addr,packet,1)
		packet[5] = len(vizinhos)
		ind = 6
		for i in vizinhos:
			Packet.ip_to_byte(i,packet,ind)
			ind = ind + 4
			packet[ind] = 1
			ind = ind + 1
		return packet


vizinhos = {}
vizinhos["10.0.0.21"] = "ola"
vizinhos["10.0.1.20"] = "ola"

print(Packet.encode_lsa("10.0.0.20",vizinhos))

