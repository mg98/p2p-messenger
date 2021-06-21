import struct
import time
import hashlib
import binascii
import socket
from . import types, utils
from ..config import Config

# =======================================================
# Protocol header:
# 0                         16                        32
# +------------+------------+------------+------------+
# |   Version  |  Msg Type  |     TTL    |  Hop Count |
# +------------+------------+------------+------------+
# |        Sender Port      |      Payload length     |
# +------------+------------+------------+------------+
# |             Original Sender IP Address            |
# +------------+------------+------------+------------+
# |                     Message ID                    |
# +------------+------------+------------+------------+
# =======================================================
class Header:
	"""Structure of the protocol header included in the first 16 bytes of every message."""

	sequence_id = 0
	"""
	This value is part of the message id hash input and gets incremented continuously.
	This is crucial for when multiple messages of the same type get created at the same time.
	"""

	def __init__(
		self,
		version = Config.prot_version,
		msg_type: types.MsgType = None,
		ttl = Config.prot_default_ttl,
		hop_count = 0,
		port = Config.default_port,
		length = 0,
		ip = socket.gethostbyname(socket.gethostname()),
		message_id = None
	):
		self.version = version
		self.msg_type = msg_type
		self.ttl = ttl
		self.hop_count = hop_count
		self.port = port
		self.length = length
		self.ip = ip
		self.message_id = message_id

	def __repr__(self) -> str:
		return '|{}|{}|{}|{}|{}|{}|{}|{}|'.format(
			self.version,
			str(self.msg_type)[len('MsgType.'):],
			self.ttl,
			self.hop_count,
			self.port,
			self.length,
			self.ip,
			binascii.hexlify(self.message_id).decode('utf-8')
		)

	def gen_message_id(self) -> bytes:
		"""Creates a new unique message id for this header."""
		hash_input = str(self.ip) + str(self.port) + str(time.time() + Header.sequence_id)
		Header.sequence_id += 1
		hash_value = hashlib.sha1(hash_input.encode('utf-8')).hexdigest()[:8]
		return binascii.unhexlify(hash_value)

	def bytes(self) -> bytes:
		"""Returns header as bytes. A message id will be generated if value was not already set."""
		return struct.pack(
			'!BBBBHHI4s',
			self.version,
			self.msg_type.value,
			self.ttl,
			self.hop_count,
			self.port,
			self.length,
			utils.ip_to_num(self.ip),
			self.message_id if self.message_id else self.gen_message_id()
		)

	@staticmethod
	def from_bytes(header_bytes):
		"""Instantiates a new Header from bytes."""
		(version, msg_type_val, ttl, hop_count, port, length, ip_num, message_id) = struct.unpack('!BBBBHHI4s', header_bytes)
		return Header(
			version=version,
			msg_type=types.MsgType(msg_type_val),
			ttl=ttl,
			hop_count=hop_count,
			port=port,
			length=length,
			ip=utils.num_to_ip(ip_num),
			message_id=message_id
		)
