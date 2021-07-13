import socket
import struct
from threading import Thread
from time import sleep
import logging
import random
import rsa
from .peer import Peer
from ..config import Config
from ..protocol import Header, Message, types


class Node:
	def __init__(self, port: int):
		"""Initiates a new node (have to call `run` to activate the node)."""

		self.ip = socket.gethostbyname(socket.gethostname())
		"""Port of this node"""

		self.port = port
		"""Port of this node"""

		self.host_addr = (self.ip, self.port)
		"""IP and port tuple of this node as addressable in the network."""

		self.pub_key, self.private_key = rsa.newkeys(16)
		"""Public and private keys of this node for encrypted communication"""

		self.neighbours: list[Peer] = []
		"""List of active connections to neighbour peers."""

		self.recv_pings: dict[str, tuple[str, int]] = {}
		"""Dictionary mapping message IDs of received pings to the address tuple of the respective sender."""

		self.neighbour_candidates: list[tuple[str, int]] = []
		"""List of neighbour candidates from ping-pong discovery"""

	def run(self, b_addr: tuple[str, int]):
		"""Runs a node listening for connections."""

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((socket.gethostname(), self.port))
		s.listen(Config.max_connections)

		bt = Thread(target=self.bootstrap, args=[b_addr])
		bt.start()

		logging.info(f'Node with {self.pub_key} reachable at {self.ip} on port {self.port}...')

		try:
			while True:
				(client, addr) = s.accept()
				logging.debug(f'Accept connection from {addr}, socket {client}')
				ct = Thread(target=self.reply, args=[client])
				ct.start()

		except KeyboardInterrupt:
			# teardown connections to neighbours
			logging.info('Disconnecting from peers...')
			for n in self.neighbours:
				logging.debug(f'Disconnect from neighbour: {n}')
				n.send(Message(types.MsgType.BYE, self.host_addr))
			# wait for other peers to handle bye message
			sleep(1)
			s.shutdown(socket.SHUT_RDWR)
			s.close()

	def bootstrap(self, addr: tuple[str, int]):
		"""Joins the network by sending a ping message to the given address."""

		logging.info('Attempting to bootstrap using %s:%s...' % addr)

		if addr == self.host_addr:
			logging.warning('Aborting bootstrap: Cannot bootstrap with yourself. Continuing as detached peer.')
			return

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect(addr)
		except ConnectionRefusedError:
			logging.warning('Bootstrapping failed. Continuing as detached peer.')
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
			logging.info('Connecting new neighbour (bootstrapping): {}'.format(addr))
			self.neighbours.append(Peer(addr))

		self.neighbour_candidates = []
		logging.debug(f'Finished bootstrapping process for node with {self.pub_key}')

	def reply(self, client: socket):
		"""Handles incoming requests."""

		connected = True
		while connected:
			# TODO fix struct.error bug with zero bytes, occurs when
			#  - peers (all except bootstrapping peer) shutdown via ctrl+c (from all neighbours)
			#  - bootstrapping peer gets it from all the peers after some time
			header_bytes = client.recv(16)
			if len(header_bytes) == 0:
				logging.warning(f'Received zero bytes message. Closing socket: {client}')
				client.close()
				return
			header = Header.from_bytes(header_bytes)
			payload = client.recv(header.length)
			msg = Message(header.msg_type, self.host_addr)
			msg.header = header
			msg.payload = str(payload, 'utf-8')

			logging.debug('Received message of type %s.' % msg.header.msg_type.name)
			logging.debug(f'Message print out: {msg}')

			if msg.header.msg_type == types.MsgType.PING:
				self.handle_ping(msg)
			elif msg.header.msg_type == types.MsgType.PONG:
				self.handle_pong(msg)
			elif msg.header.msg_type == types.MsgType.BYE:
				self.handle_bye(msg)
				connected = False
		client.close()

	def handle_ping(self, msg: Message):
		"""Handles incoming ping."""

		if msg.get_id() in self.recv_pings:
			logging.debug('Rejecting ping because message was already received.')
			return

		msg.header.ttl -= 1
		msg.header.hop_count += 1

		if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl:
			# forward ping to all neighbours (except the neighbour that we got the ping from)
			num_of_neighbours = len(self.neighbours)-1
			logging.debug('Forwarding ping to %d neighbours.' % num_of_neighbours)
			for n in self.neighbours:
				# Do not send the ping back to where we got it from
				if n.addr is not msg.get_sender():
					logging.debug(f'Sender check passed: <{n.addr}> vs. <{msg.get_sender()}>')
					logging.debug(f'Forwarding ping to {n}')
					n.send(msg)
			self.recv_pings[msg.get_id()] = msg.get_sender()

		peer = Peer(msg.get_sender())

		if len(self.neighbours) < Config.neighbours:
			# append to neighbours
			logging.info('Connecting to new neighbour after ping: {}'.format(peer.addr))
			self.neighbours.append(peer)
			logging.debug(f'Current neighbours: {self.neighbours}')

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

		# Reverse path routing pongs
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
