#!/usr/bin/env python3

from fire import Fire
from . import node, client, Config

class CLI(object):
	"""A simple P2P messenger."""

	def node(self, port = None, b = None):
		"""Runs the node."""

		if port is None: port = Config.default_port

		if b:
			if isinstance(b, int): address = ('127.0.0.1', b)
			else: address = tuple(b.split(':', maxsplit=1))
		else: address = Config.bootstrap_peer

		node.run(port, address)

	def ping(self):
		"""Pings local server."""
		client.ping()

	def post(self, msg: str):
		"""Posts chat message."""
		client.post(msg)


if __name__ == '__main__':
	Config.load()
	Fire(CLI)
