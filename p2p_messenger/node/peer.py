import logging
from p2p_messenger.protocol.message import Message
import socket
from ..protocol import utils


class Peer:
	def __init__(
		self,
		addr: tuple[str, int],
		peer_id: str = None,
		s: socket.socket = None
	):
		self.peer_id = peer_id
		self.pub_key = utils.peer_id_to_pub_key(self.peer_id) if peer_id else None
		self.addr = addr

		if s:
			self.socket = s
		else:
			# establish socket connection from node to a peer
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.connect(self.addr)
			logging.debug(f"Established peer connection to node {self.peer_id} with address: {self.addr}")
			logging.debug(f"Socket printout: {self.socket}")

		self.sock_name = self.socket.getsockname()
		self.peer_name = self.socket.getpeername()

	def __repr__(self) -> str:
		return format('Peer connection %s, socket printout %s' % (str(self.addr), self.socket))

	def send(self, msg: Message):
		logging.debug("Sending message of type %s to %s:%d" % (msg.header.msg_type.name, self.addr[0], self.addr[1]))
		logging.debug(f"Message printout: {msg}")
		logging.debug(f"Socket printout: {self.socket}")
		self.socket.send(msg.bytes())

	def disconnect(self):
		logging.debug("Disconnecting %s:%d" % self.addr)
		logging.debug(self.socket)
		try:
			self.socket.shutdown(socket.SHUT_RDWR)
			self.socket.close()
		except OSError as e:
			logging.warning(e)
