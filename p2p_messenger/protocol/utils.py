import struct
import socket


def ip_to_num(ip):
	"""Convert IP address of sender as single number IP address of sender as single number."""
	return struct.unpack('>L', socket.inet_aton(ip))[0]


def num_to_ip(num) -> str:
	"""Convert number back to IP address."""
	return socket.inet_ntoa(struct.pack('>L', num))
