from src.RtpPacket import RtpPacket 
from src.VideoStream import VideoStream
from Connection import Connection
from Packet import Packet
import time
import threading
import logging

class Server:

	def __init__(self,filename,port):
		self.stream = VideoStream(filename)
		self.c = Connection()
		ret = self.c.connect(("localhost",port)) 
		if(ret):
			threading.Thread(target=self.send_stream,args=()).start()

		else:
			logging.debug("Server: Connection Refuse")


	def send_stream(self):
		while(True):
			t = time.time_ns()
			self.c.send(self.frame())
			t = 0.05 - (time.time_ns() - t) / 1000000000 
			if(t > 0):
				time.sleep(t)

	def frame(self):
		data = self.stream.nextFrame()
		ret = None
		if data: 
			frameNumber = self.stream.frameNbr()
			ret = self.makeRtp(data, frameNumber)

		return ret

	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return Packet.encode_STREAM(rtpPacket.getPacket())
