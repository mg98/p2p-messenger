import logging
import struct
import socket
import rsa
import base64

RSA_PREFIX = base64.standard_b64encode(b'-----BEGIN RSA PUBLIC KEY-----').decode("utf-8")
RSA_SUFFIX = base64.standard_b64encode(b'-----END RSA PUBLIC KEY-----').decode("utf-8")

def ip_to_num(ip):
	"""Convert IP address of sender as single number IP address of sender as single number."""
	return struct.unpack('>L', socket.inet_aton(ip))[0]


def num_to_ip(num) -> str:
	"""Convert number back to IP address."""
	return socket.inet_ntoa(struct.pack('>L', num))


def pub_key_to_peer_id(pub_key: rsa.PublicKey) -> str:
	"""Formats public key as peer id string."""

	pem = pub_key._save_pkcs1_pem()
	peer_id_bytes = base64.standard_b64encode(pem)
	peer_id = peer_id_bytes.decode('utf-8')
	print('Complete rsa: ', peer_id)
	return peer_id[len(RSA_PREFIX):-len(RSA_SUFFIX)]


def peer_id_to_pub_key(peer_id: str) -> rsa.PublicKey:
	"""Convert peer id string to public key."""

	logging.debug(f"Converting peer id string <{peer_id}> (length: {len(peer_id)}) to public key")

	peer_id = RSA_PREFIX + peer_id + RSA_SUFFIX
	peer_id_bytes = peer_id.encode('utf-8')
	pem = base64.standard_b64decode(peer_id_bytes)
	pub_key = rsa.PublicKey.load_pkcs1(pem)

	return pub_key


def remove_padding(padded_string: str, padding_char: str = "#") -> str:
	split_str = padded_string.split(padding_char)
	raw_str = split_str[0]
	return raw_str
