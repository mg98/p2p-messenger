from enum import Enum


class MsgType(Enum):
	PING = 0x00  # Discovery of the network
	PONG = 0x01  # Response to a PING message
	BYE = 0x02  # Departure from network
	JOIN = 0x03  # Request to build neighbour relation, payload is sender peer id
	QUERY = 0x10  # Search for recipient, payload is recipient peer id (which is also the public key)
	QHIT = 0x11  # Response to query with recipient address in sender field
	POST = 0x12  # Chat message
