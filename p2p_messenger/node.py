import socket
from threading import Thread
from time import sleep
import logging
import random
from .config import Config
from .protocol import Header, Message, types

host_addr: tuple[str, int] = None
"""IP and port tuple of this node as addressable in the network."""

neighbours: list[socket.socket] = []
"""List of active connections to neighbour peers."""

recv_pings: dict[str, tuple[str, int]] = {}
"""Dictionary mapping message IDs of received pings to the address tuple of the respective sender."""

neighbour_candidates: list[tuple[str, int]] = []

def run(port: int, b_addr: tuple[str, int]):
	"""Runs a node listening for connections."""
	global host_addr
	host_addr = (socket.gethostbyname(socket.gethostname()), port)

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((socket.gethostname(), port))
	s.listen(Config.max_connections)

	bt = Thread(target=bootstrap, args=[b_addr])
	bt.start()

	logging.info("Listening on port %d..." % port)
	while True:
		(client, addr) = s.accept()
		ct = Thread(target=reply, args=[client])
		ct.start()

def bootstrap(addr: tuple[str, int]):
	"""Joins the network by sending a ping message to the given address."""
	global neighbour_candidates

	logging.info("Attempting to bootstrap using %s:%s..." % addr)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.connect(addr)
	except ConnectionRefusedError:
		logging.warn('Bootstrapping failed. Continuing as detached peer.')
		return

	s.send(Message(types.MsgType.PING, host_addr).bytes())
	s.close()

	sleep(3)
	logging.debug('Received neighbour candidates: {}'.format(neighbour_candidates))

	neighbours = random.sample(
		neighbour_candidates,
		Config.neighbours if len(neighbour_candidates) >= Config.neighbours else len(neighbour_candidates)
	)
	neighbour_candidates = []

	logging.debug('Selected neighbours: {}'.format(neighbours))


def reply(client: socket):
	"""Handles incoming requests."""

	header_bytes = client.recv(16)
	header = Header.from_bytes(header_bytes)

	payload = client.recv(header.length)
	msg = Message(header.msg_type, host_addr)
	msg.header = header
	msg.payload = str(payload, 'utf-8')

	logging.debug('Received message of type %s.' % msg.header.msg_type.name)

	if msg.header.msg_type == types.MsgType.PING:
		handle_ping(msg)
	elif msg.header.msg_type == types.MsgType.PONG:
		handle_pong(msg)

	client.close()

def handle_ping(msg: Message):
	"""Handles incoming ping."""

	if msg.get_id() in recv_pings:
		logging.debug('Rejecting ping because message was already received.')
		return

	msg.header.ttl -= 1
	msg.header.hop_count += 1

	if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl:
		for n in neighbours: n.send(msg.bytes())
		recv_pings[msg.get_id()] = msg.get_sender()

	# Pong!
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(msg.get_sender())
	s.send(Message(types.MsgType.PONG, host_addr).bytes())
	s.close()

def handle_pong(msg: Message):
	"""Handles incoming pong."""

	if len(neighbours) < Config.neighbours:
		neighbour_candidates.append(msg.get_sender())

	if msg.get_id() not in recv_pings:
		logging.debug('Rejecting pong because message id is unknown.')
		return

	msg.header.ttl -= 1
	msg.header.hop_count += 1

	if msg.header.ttl > 0 and msg.header.hop_count <= Config.prot_max_ttl:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(msg.get_sender())
		s.send(Message(types.MsgType.PONG, recv_pings[msg.get_id()]).bytes())
		s.close()

