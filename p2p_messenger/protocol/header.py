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

	def __init__(self, msg_type: types.MsgType, payload = ''):
		self.version = Config.prot_version
		self.msg_type = msg_type
		self.ttl = Config.prot_default_ttl
		self.hop_count = 0
		self.port = 1337
		self.length = len(payload)
		self.ip = socket.gethostbyname(socket.gethostname())
		self.message_id = self.gen_message_id()

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
		"""Creates new message id for this header using current timestamp."""
		hash_input = str(self.ip) + str(self.port) + str(time.time())
		hash_value = hashlib.sha1(hash_input.encode('utf-8')).hexdigest()[:8]
		return binascii.unhexlify(hash_value)

	def bytes(self) -> bytes:
		"""Returns header as bytes."""
		return struct.pack(
			'!BBBBHHI4s',
			self.version,
			self.msg_type.value,
			self.ttl,
			self.hop_count,
			self.port,
			self.length,
			utils.ip_to_num(self.ip),
			self.message_id
		)

	@staticmethod
	def from_bytes(header_bytes):
		"""Instantiates a new Header from bytes."""
		(version, msg_type_val, ttl, hop_count, port, length, ip_num, message_id) = struct.unpack('!BBBBHHI4s', header_bytes)
		header = Header(types.MsgType(msg_type_val))
		header.version = version
		header.ttl = ttl
		header.hop_count = hop_count
		header.port = port
		header.length = length
		header.ip = utils.num_to_ip(ip_num)
		header.message_id = message_id
		return header
