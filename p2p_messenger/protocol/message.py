from . import types, header


class Message:
	"""Structure of a message including the protocol header and the payload."""

	def __init__(self, msg_type: types.MsgType, sender: tuple[str, int], msg_id=None, payload=''):
		"""Initiate a new message."""
		self.header = header.Header(msg_type=msg_type, ip=sender[0], port=sender[1], length=len(payload), message_id=msg_id)
		self.payload = payload

	def __repr__(self) -> str:
		return format('%s%s|' % (str(self.header), self.payload))

	def bytes(self) -> bytes:
		"""Returns message as bytes."""
		return self.header.bytes() + bytes(self.payload.encode('utf-8'))

	def get_id(self) -> str:
		"""Returns message id from header."""
		return self.header.message_id

	def get_sender(self) -> tuple[str, int]:
		"""Returns sender (ip, port) tuple of this message."""
		return self.header.ip, self.header.port
