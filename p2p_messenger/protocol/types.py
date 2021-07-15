from enum import Enum


class MsgType(Enum):
	PING = 0x00
	PONG = 0x01
	BYE = 0x02
	JOIN = 0x03
	QUERY = 0x10
	QHIT = 0x11
	POST = 0x12
