from p2p_messenger.protocol.message import Message
import socket

class Peer:
	def __init__(
		self,
		addr: tuple[str, int],
		s: socket.socket = None
	):
		self.addr = addr

		if s: self.socket = s
		else:
			# establish socket connection
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.connect(self.addr)

	def send(self, msg: Message):
		self.socket.send(msg.bytes())

	def disconnect(self):
		self.socket.shutdown(socket.SHUT_RDWR)
		self.socket.close()
