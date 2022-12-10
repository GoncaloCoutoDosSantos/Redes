from src.RtpPacket import RtpPacket 
from src.VideoStream import VideoStream
from Connection import Connection
import time
import threading
import logging

class Server:

	def __init__(self,filename,port):
		self.stream = VideoStream(filename)
		self.c = Connection()
		ret = c.connect(("localhost",port)) 
		if(ret):
			threading.Thread(target=self.send_stream,args=()).start()

		else:
			logging.debug("Server: Connection Refuse")

		return ret


	def send_stream(seff):
		while(True):
			time.sleep(0.05)
			self.c.send(self.frame())

	def frame(self):
		data = self.stream.nextFrame()

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
		
		return rtpPacket.getPacket()
