from enum import Enum

class MsgType(Enum):
	PING = 0x00
	PONG = 0x01
	POST = 0x02
