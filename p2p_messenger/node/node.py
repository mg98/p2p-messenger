import socket
from threading import Thread
from time import sleep
import logging
import random
from typing import Optional

import rsa
from .peer import Peer
from ..config import Config
from ..protocol import Header, Message, types, utils


class Node:
	def __init__(self, port: int):
		"""Initiates a new node (have to call `run` to activate the node)."""

		self.ip = socket.gethostbyname(socket.gethostname())
		"""IP of this node"""

		self.port = port
		"""Port of this node"""

		self.host_addr = (self.ip, self.port)
		"""IP and port tuple of this node as addressable in the network."""

		self.pub_key, self.private_key = rsa.newkeys(16)
		"""Public and private keys of this node for encrypted communication"""

		self.peer_id = utils.pub_key_to_peer_id(self.pub_key)
		"""Peer ID for this node."""

		self.inbound_neighbours: list[Peer] = []
		"""List of active inbound connections from neighbour peers."""

		self.outbound_neighbours: list[Peer] = []
		"""List of active outbound connections to neighbour peers."""

		self.recv_pings: dict[str, tuple[str, int]] = {}
		"""Dictionary mapping message IDs of received pings to the address tuple of the respective sender."""

		self.recv_queries: dict[str, tuple[str, int]] = {}
		"""Dictionary mapping public keys of received queries to the address tuple of the respective sender."""

		self.sent_pings: list[str] = []
		"""List of message IDs of sent pings."""

		self.sent_queries: list[str] = []
		"""List of message IDs of sent queries."""

		self.neighbour_candidates: list[tuple[str, int]] = []
		"""List of neighbour candidates from ping-pong discovery."""

		self.recipient_id_map: dict[str, Optional[tuple[str, int]]] = {}
		"""Dictionary mapping peer ids to the address tuple of the recipient"""

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
			for n in self.outbound_neighbours:
				logging.debug(f'Disconnect from neighbour: {n}')
				n.send(Message(types.MsgType.BYE, self.host_addr))  # signal neighbor to close its connection
				n.disconnect()  # close own outgoing connection to neighbour
			# wait for other peers to handle bye message
			sleep(1)
			s.shutdown(socket.SHUT_RDWR)
			s.close()

	def bootstrap(self, addr: tuple[str, int]):
		"""Joins the network by sending a ping message to the given address."""

		# send ping to bootstrapping peer
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
		ping_msg = Message(types.MsgType.PING, self.host_addr)
		self.sent_pings.append(ping_msg.get_id())
		s.send(ping_msg.bytes())
		logging.debug(f'Message print out: {ping_msg}')

		# wait for some pongs
		sleep(3)
		logging.debug('Received neighbour candidates: {}'.format(self.neighbour_candidates))

		neighbour_addrs = random.sample(
			self.neighbour_candidates,
			Config.neighbours if len(self.neighbour_candidates) >= Config.neighbours else len(self.neighbour_candidates)
		)
		for addr in neighbour_addrs:
			# TODO use a join method with exchange of peer_ids in order to build symmetrical neighbour relations
			logging.info('Connecting new neighbour (bootstrapping): {}'.format(addr))
			self.outbound_neighbours.append(Peer(addr))  # add peer id to Peer
		logging.debug(f'Current neighbours: {self.outbound_neighbours}')

		self.neighbour_candidates = []
		logging.debug(f'Finished bootstrapping process for node with {self.pub_key}')

		# TODO Send a test message to bootstrapping peer? But we need the peer id somehow

	def join(self, addr):
		"""Initiates the process of building a neighbour relation with a peer."""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(addr)
		s.settimeout(3)
		join_msg = Message(msg_type=types.MsgType.JOIN, sender=self.host_addr, payload=self.peer_id)
		logging.debug(f"Message printout: {join_msg}")
		s.send(join_msg.bytes())
		try:
			peer_id = s.recv(1024).decode('utf-8')[:32]
			# mapping from Peer.socket.getpeername() to peer id
			self.outbound_neighbours.append(Peer(addr=addr, peer_id=peer_id, s=s))
			return True
		except Exception as e:
			logging.warning(f"Handle join function failed. ({e})")

		# Join failed, close socket
		try:
			s.shutdown(socket.SHUT_RDWR)
			s.close()
		except OSError as e:
			logging.warning(e)
		return False

	def post_msg(self, chat_msg: str, peer_id: str):
		"""Posts message"""
		def send_msg():
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(self.recipient_id_map[peer_id])
			# TODO encrypt chat message
			post_msg = Message(types.MsgType.POST, self.host_addr, payload=chat_msg)
			logging.debug(f'Sending message of type POST to {self.recipient_id_map[peer_id]}')
			logging.debug(f'Message printout: {post_msg}')
			s.send(post_msg.bytes())

		# We already know the recipient, open connection and send message
		if not self.recipient_id_map[peer_id]:
			# We do not know the recipient's address, do a query
			num_of_neighbours = len(self.outbound_neighbours)
			logging.debug('Sending query to %d neighbours.' % num_of_neighbours)
			query_msg = Message(types.MsgType.QUERY, self.host_addr, payload=peer_id)
			logging.debug(f'Message printout: {query_msg}')
			self.recipient_id_map[peer_id] = None
			for n in self.outbound_neighbours:
				n.send(query_msg)

		# wait for query hit
		sleep(3)
		if self.recipient_id_map[peer_id]:
			send_msg()
			return
		else:
			logging.warning(f'Failed to send the message. Did not find recipient {peer_id}')

	def reply(self, client: socket):
		"""Handles incoming requests."""

		connected = True
		while connected:
			# TODO fix struct.error bug with zero bytes, occurs when
			#  - peers (all except bootstrapping peer) shutdown via ctrl+c (from all neighbours, inbound connections)
			#  - bootstrapping peer gets it from all the peers after some time
			#  --> probably need to be able to identify neighbours with connections to close them properly during BYE
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
			elif msg.header.msg_type == types.MsgType.JOIN:
				connected = self.handle_join(msg, client)
			elif msg.header.msg_type == types.MsgType.JACC:
				connected = self.handle_jacc(msg, client)
			elif msg.header.msg_type == types.MsgType.BYE:
				self.handle_bye(msg)
				connected = False
			elif msg.header.msg_type == types.MsgType.QUERY:
				self.handle_query(msg)
			elif msg.header.msg_type == types.MsgType.QHIT:
				self.handle_query_hit(msg)
			elif msg.header.msg_type == types.MsgType.POST:
				self.handle_post(msg)
				# TODO think about this, do we keep this open or do we only process one msg per inbound connection?
				#  is it possible from the sender's side to use the same socket to send multiple post msgs?
				#  and how would we signal the end of the communication?
				connected = False
		client.close()

	def handle_ping(self, msg: Message):
		"""Handles incoming ping."""
		if msg.get_id() in self.recv_pings:
			logging.debug('Rejecting ping because message was already received.')
			return
		elif msg.get_sender() == self.host_addr:
			logging.debug('Rejecting ping because we are the original sender of the message.')
			return

		# TODO this just saves the original sender of the ping instead of the neighbour that we got the msg from
		self.recv_pings[msg.get_id()] = msg.get_sender()
		msg.header.ttl -= 1
		msg.header.hop_count += 1

		if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl and self.outbound_neighbours:
			# forward ping to all neighbours (except the neighbour that we got the ping from)
			num_of_neighbours = len(self.outbound_neighbours)
			logging.debug('Forwarding ping to at most %d neighbours.' % num_of_neighbours)
			for n in self.outbound_neighbours:
				# Do not send the ping back to where we got it from
				if n.addr is not msg.get_sender():
					# TODO we should actually compare with the peer id from the ingoing neighbour connection
					logging.debug(f'Sender check passed: neighbour <{n.addr}> vs. sender <{msg.get_sender()}>')
					logging.debug(f'Forwarding ping to {n}')
					n.send(msg)
			logging.debug(f'Add {msg.get_id()}:{msg.get_sender()} to list of received pings')

		# send pong to sender
		# TODO we should know from which direct node we got the ping in order to send back the pong
		#  msg.get_sender() is address of the original sender, not necessarily the node that sent it our way
		if len(self.outbound_neighbours) < Config.max_connections:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sender = msg.get_sender()
			s.connect(sender)
			pong_msg = Message(msg_type=types.MsgType.PONG, sender=self.host_addr, msg_id=msg.get_id())
			logging.debug('Sending message of type PONG to %s:%d' % sender)
			logging.debug(f'Message printout: {pong_msg}')
			s.send(pong_msg.bytes())
		else:
			logging.debug(f"Not sending back PONG message because: {len(self.outbound_neighbours)} outbound neighbours >= {Config.max_connections} max connections")

		# TODO can we ensure that neighbour connection after ping is symmetrical?
		#  what if this peer builds a neighbour connection to the other peer
		#  but the peer does not choose this peer out of its neighbour candidates?
		#  maybe we need a handshake after all
		if len(self.outbound_neighbours) < Config.neighbours:
			# TODO we really should know the peer id/ pub key of the sender and add it to Peer
			peer = Peer(msg.get_sender())
			# append to neighbours
			logging.info('Connecting to new neighbour after ping: {}'.format(peer.addr))
			self.outbound_neighbours.append(peer)
			logging.debug(f'Current neighbours: {self.outbound_neighbours}')

	def handle_pong(self, msg: Message):
		"""Handles incoming pong."""

		if len(self.outbound_neighbours) < Config.max_connections and msg.get_sender() != self.host_addr:
			if msg.get_sender() not in self.neighbour_candidates:
				self.neighbour_candidates.append(msg.get_sender())
			else:
				logging.warning(f"Sender {msg.get_sender()} already sent a pong")

		if msg.get_id() in self.sent_pings:
			logging.debug('Received pong for my ping.')
			return
		elif msg.get_id() not in self.recv_pings:
			logging.debug(f'Rejecting pong because message id {msg.get_id()} is unknown.')
			logging.debug(f'Sent pings: {self.sent_pings}')
			logging.debug(f'Received pings: {self.recv_pings.keys()}')
			return

		msg.header.ttl -= 1
		msg.header.hop_count += 1

		# Reverse path routing pongs
		if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl:
			# TODO route pong back via neighbour connection instead of opening a new socket
			#  which would in turn creates a new socket on the other side and start a separate reply thread
			#  and is only used once
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(self.recv_pings[msg.get_id()])
			s.send(Message(types.MsgType.PONG, msg.get_sender()).bytes())

	def handle_join(self, msg: Message, client: socket.socket):
		"""Handles incoming join."""
		if len(self.outbound_neighbours) < Config.max_connections:
			try:
				client.send(self.peer_id.encode('utf-8'))  # Send my id to the requesting node
				sender_peer_id = msg.payload[:32]
				# mapping from client.getpeername() to peer id
				self.inbound_neighbours.append(Peer(addr=msg.get_sender(), peer_id=sender_peer_id, s=client))
			except Exception as e:
				logging.warning(f'Handle join function failed while building inbound connection. ({e})')
				return False
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(msg.get_sender())
			s.settimeout(3)
			try:
				jacc_msg = Message(types.MsgType.JACC, self.host_addr, payload=self.peer_id)
				logging.debug('Sending message of type JACC to %s:%d' % msg.get_sender())
				logging.debug(f'Message printout: {jacc_msg}')
				s.send(jacc_msg.bytes())
				peer_id = s.recv(1024).decode('utf-8')[:32]
				if peer_id == sender_peer_id:
					# mapping from Peer.socket.getpeername() to peer id
					self.outbound_neighbours.append(Peer(addr=msg.get_sender(), peer_id=sender_peer_id, s=s))
					return True
			except Exception as e:
				logging.warning(f'Handle join function failed while building outbound connection. ({e})')

			# Join failed, clean up
			try:
				s.shutdown(socket.SHUT_RDWR)
				s.close()
			except OSError as e:
				logging.warning(e)
		return False

	def handle_jacc(self, msg: Message, client: socket.socket):
		try:
			client.send(self.peer_id.encode('utf-8'))  # Send my id to the requesting node
			sender_peer_id = msg.payload[:32]
			# mapping from client.getpeername() to peer id
			self.inbound_neighbours.append(Peer(addr=msg.get_sender(), peer_id=sender_peer_id, s=client))
		except Exception as e:
			logging.warning(f'Handle join function failed while building inbound connection. ({e})')
			return False

	def handle_bye(self, msg: Message):
		"""Handles incoming bye."""

		for n in self.outbound_neighbours:
			if n.addr == msg.get_sender():
				# this closes the outgoing connection
				self.outbound_neighbours.remove(n)
				n.disconnect()
				break

	def handle_query(self, msg: Message):
		"""Handles incoming query."""
		if msg.get_id() in self.recv_queries:
			logging.debug('Rejecting query because message was already received.')
			return
		elif msg.get_sender() == self.host_addr:
			logging.debug('Rejecting query because we are the original sender of the message.')
			return
		# TODO this just saves the original sender of the query instead of the neighbour that we got the msg from
		self.recv_queries[msg.get_id()] = msg.get_sender()

		# Compare recipient public key with own public key, if no match forward to neighbours
		recipient_pub_key = utils.peer_id_to_pub_key(msg.payload)
		if recipient_pub_key.n == self.pub_key.n and recipient_pub_key.e == self.pub_key.e:
			# TODO sends query hit directly to sender, in reality we should do reverse path routing
			#  find out from which neighbour we got it the query and route it back to them
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sender = msg.get_sender()
			s.connect(sender)
			qhit_msg = Message(types.MsgType.QHIT, self.host_addr, payload=self.peer_id)
			logging.debug('Sending message of type QHIT to %s:%d' % sender)
			logging.debug(f'Message printout: {qhit_msg}')
			s.send(qhit_msg.bytes())
		else:
			msg.header.ttl -= 1
			msg.header.hop_count += 1
			if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl and self.outbound_neighbours:
				# forward query to all neighbours (except the neighbour that we got the query from)
				num_of_neighbours = len(self.outbound_neighbours)
				logging.debug('Forwarding query to at most %d neighbours.' % num_of_neighbours)
				for n in self.outbound_neighbours:
					# Do not send the query back to where we got it from
					if n.addr is not msg.get_sender():
						# TODO we should actually compare with the peer id from the ingoing neighbour connection
						logging.debug(f'Sender check passed: neighbour <{n.addr}> vs. sender <{msg.get_sender()}>')
						logging.debug(f'Forwarding query to {n}')
						n.send(msg)
				logging.debug(f'Add {msg.get_id()}:{msg.get_sender()} to list of received queries')

	def handle_query_hit(self, msg: Message):
		"""Handles incoming query hit."""
		# Case 1: we are the sender
		# Start a connection to the recipient and start posting messages
		peer_id = msg.payload[:32]
		if peer_id in self.recipient_id_map:
			self.recipient_id_map[peer_id] = msg.get_sender()
			logging.debug(f'Update recipient id to address mapping: {peer_id}<-{msg.get_sender()}')
			return

		# Case 2: we are not the sender, reverse path routing to sender
		if msg.get_id() not in self.recv_queries:
			logging.debug('Rejecting query hit because message id is unknown.')
			return

		msg.header.ttl -= 1
		msg.header.hop_count += 1

		# Reverse path routing query hit
		if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl:
			# TODO route query hit back via neighbour connection instead of opening a new socket
			#  which in turn creates a new socket on the other side and starts a separate reply thread
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(self.recv_queries[msg.get_id()])
			s.send(msg.bytes())

	def handle_post(self, msg: Message):
		"""Handles incoming post."""
		n = int(msg.payload[:16])
		e = int(msg.payload[16:32])
		recipient_pubkey = rsa.PublicKey(n, e)
		if n != self.pub_key.n or e != self.pub_key.e:
			logging.error(f"Public key mismatch: recipient {recipient_pubkey} vs. own {self.pub_key}")
			return
		msg_content = msg.payload[32:]
		# TODO Decrypt message, fails if there are not enough bytes
		logging.info(f"Message content: <{msg_content}>")
