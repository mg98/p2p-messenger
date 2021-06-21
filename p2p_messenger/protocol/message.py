from . import types, header

class Message:
	"""Structure of a message including the protocol header and the payload."""

	def __init__(self, msg_type: types.MsgType, payload=''):
		self.header = header.Header(msg_type=msg_type, length=len(payload))
		self.payload = payload

	def __repr__(self) -> str:
		return format('%s%s|' % (str(self.header), self.payload))

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
		super().__init__(types.MsgType.PONG)


class PostMessage(Message):
	"""Convenience wrapper class for ping messages."""
	def __init__(self, msg: str):
		super().__init__(types.MsgType.POST, msg)
