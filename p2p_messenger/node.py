from p2p_messenger.protocol import message
import socket
from .config import Config
from .protocol import Header, Message

def run():
	"""Runs a node listening for connections."""
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((socket.gethostname(), Config.default_port))
	s.listen(Config.max_connections)
	print("Listening on port %d" % Config.default_port)
	while True:
		(client, addr) = s.accept()
		header_bytes = client.recv(16)
		header = Header.from_bytes(header_bytes)
		payload = client.recv(header.length)
		msg = Message(header.msg_type)
		msg.header = header
		msg.payload = str(payload, 'utf-8')
		print(msg)



