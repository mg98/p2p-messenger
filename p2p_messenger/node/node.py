import socket
from threading import Thread
from time import sleep
import logging
import random
from .peer import Peer
from ..config import Config
from ..protocol import Header, Message, types

class Node:
	def __init__(self, port: int):
		"""Initiates a new node (have to call `run` to activate the node)."""

		self.host_addr = (socket.gethostbyname(socket.gethostname()), port)
		"""IP and port tuple of this node as addressable in the network."""

		self.neighbours: list[Peer] = []
		"""List of active connections to neighbour peers."""

		self.recv_pings: dict[str, tuple[str, int]] = {}
		"""Dictionary mapping message IDs of received pings to the address tuple of the respective sender."""

		self.neighbour_candidates: list[tuple[str, int]] = []

	def run(self, b_addr: tuple[str, int]):
		"""Runs a node listening for connections."""

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((socket.gethostname(), self.host_addr[1]))
		s.listen(Config.max_connections)

		bt = Thread(target=self.bootstrap, args=[b_addr])
		bt.start()

		logging.info('Listening on port %d...' % self.host_addr[1])

		try:
			while True:
				(client, addr) = s.accept()
				ct = Thread(target=self.reply, args=[client])
				ct.start()

		except KeyboardInterrupt:
			# teardown connections to neighbours
			logging.info('Disconnecting from peers...')
			for n in self.neighbours:
				n.send(Message(types.MsgType.BYE, self.host_addr))

	def bootstrap(self, addr: tuple[str, int]):
		"""Joins the network by sending a ping message to the given address."""

		logging.info('Attempting to bootstrap using %s:%s...' % addr)

		if addr == self.host_addr:
			logging.warn('Aborting bootstrap: Cannot bootstrap with yourself. Continuing as detached peer.')
			return

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect(addr)
		except ConnectionRefusedError:
			logging.warn('Bootstrapping failed. Continuing as detached peer.')
			return

		logging.debug('Sending message of type PING to %s:%d' % addr)
		s.send(Message(types.MsgType.PING, self.host_addr).bytes())

		# wait for some pongs
		sleep(3)
		logging.debug('Received neighbour candidates: {}'.format(self.neighbour_candidates))

		neighbour_addrs = random.sample(
			self.neighbour_candidates,
			Config.neighbours if len(self.neighbour_candidates) >= Config.neighbours else len(self.neighbour_candidates)
		)
		for addr in neighbour_addrs:
			self.neighbours.append(Peer(addr))
			logging.info('Connecting new neighbour (bootstrapping): {}'.format(addr))

		self.neighbour_candidates = []

	def reply(self, client: socket):
		"""Handles incoming requests."""

		header_bytes = client.recv(16)
		header = Header.from_bytes(header_bytes)

		payload = client.recv(header.length)
		msg = Message(header.msg_type, self.host_addr)
		msg.header = header
		msg.payload = str(payload, 'utf-8')

		logging.debug('Received message of type %s.' % msg.header.msg_type.name)

		if msg.header.msg_type == types.MsgType.PING:
			self.handle_ping(msg)
		elif msg.header.msg_type == types.MsgType.PONG:
			self.handle_pong(msg)
		elif msg.header.msg_type == types.MsgType.BYE:
			self.handle_bye(msg)

	def handle_ping(self, msg: Message):
		"""Handles incoming ping."""

		if msg.get_id() in self.recv_pings:
			logging.debug('Rejecting ping because message was already received.')
			return

		msg.header.ttl -= 1
		msg.header.hop_count += 1

		if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl:
			# forward ping to all neighbours
			logging.debug('Forwarding ping to %d neighbours.' % len(self.neighbours))
			for n in self.neighbours:
				n.send(msg)
			self.recv_pings[msg.get_id()] = msg.get_sender()

		peer = Peer(msg.get_sender())

		if len(self.neighbours) < Config.neighbours:
			# append to neighbours
			self.neighbours.append(peer)
			logging.info('Connecting new neighbour: {}'.format(peer.addr))

		# send pong to sender
		if len(self.neighbours) < Config.neighbours:
			peer.send(Message(types.MsgType.PONG, self.host_addr))

	def handle_pong(self, msg: Message):
		"""Handles incoming pong."""

		if len(self.neighbours) < Config.neighbours and msg.get_sender() != self.host_addr:
			self.neighbour_candidates.append(msg.get_sender())

		if msg.get_id() not in self.recv_pings:
			logging.debug('Rejecting pong because message id is unknown.')
			return

		msg.header.ttl -= 1
		msg.header.hop_count += 1

		if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(msg.get_sender())
			s.send(Message(types.MsgType.PONG, self.recv_pings[msg.get_id()]).bytes())

	def handle_bye(self, msg: Message):
		"""Handles incoming bye."""

		for n in self.neighbours:
			if n.addr == msg.get_sender():
				self.neighbours.remove(n)
				n.disconnect()
				break

