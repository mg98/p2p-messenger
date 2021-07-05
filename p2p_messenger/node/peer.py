import logging
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
		logging.debug("Sending message of type %s to %s:%d" % (msg.header.msg_type.name, self.addr[0], self.addr[1]))
		self.socket.send(msg.bytes())

	def disconnect(self):
		logging.debug("Disconnecting %s:%d" % self.addr)
		self.socket.shutdown(socket.SHUT_RDWR)
		self.socket.close()
