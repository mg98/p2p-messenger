from . import types, header

class Message:
	"""Structure of a message including the protocol header and the payload."""

	def __init__(self, msg_type: types.MsgType, payload=''):
		self.header = header.Header(msg_type, payload)
		self.payload = payload

	def __repr__(self) -> str:
		return format('Header: %s, Payload: %s' % (str(self.header), self.payload))

	def bytes(self) -> bytes:
		"""Returns message as bytes."""
		return self.header.bytes() + bytes(self.payload.encode('utf-8'))

class PingMessage(Message):
	"""Convenience wrapper class for ping messages."""
	def __init__(self):
		super().__init__(types.MsgType.PING)

class PongMessage(Message):
	"""Convenience wrapper class for ping messages."""
	def __init__(self):
		super().__init__(types.MsgType.Pong)

class PostMessage(Message):
	"""Convenience wrapper class for ping messages."""
	def __init__(self, message: str):
		super().__init__(types.MsgType.POST, message)
