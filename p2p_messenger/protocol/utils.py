import logging
import struct
import socket
import rsa


def ip_to_num(ip):
	"""Convert IP address of sender as single number IP address of sender as single number."""
	return struct.unpack('>L', socket.inet_aton(ip))[0]


def num_to_ip(num) -> str:
	"""Convert number back to IP address."""
	return socket.inet_ntoa(struct.pack('>L', num))


def pub_key_to_peer_id(pub_key: rsa.PublicKey, padding_char: str = "#") -> str:
	"""Formats public key as peer id string with 32 characters"""
	n = str(pub_key.n)
	e = str(pub_key.e)
	if len(n) > 16 or len(e) > 16:
		logging.error(f'Public key does not fit into 32 characters: n <{n}>, e <{e}>')
	else:
		padding = padding_char * (16 - len(n))
		n += padding
		assert len(n) <= 16
		padding = padding_char * (16 - len(e))
		e += padding
		assert len(e) <= 16
	return n+e


def peer_id_to_pub_key(peer_id: str) -> rsa.PublicKey:
	"""Convert peer id string to public key"""
	logging.debug(f"Converting peer id string <{peer_id}> (length: {len(peer_id)}) to public key")
	assert len(peer_id) >= 32
	n = int(remove_padding(peer_id[:16]))
	e = int(remove_padding(peer_id[16:32]))
	return rsa.PublicKey(n, e)


def remove_padding(padded_string: str, padding_char: str = "#") -> str:
	split_str = padded_string.split(padding_char)
	raw_str = split_str[0]
	return raw_str
