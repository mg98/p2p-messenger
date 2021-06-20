#!/usr/bin/env python3

from fire import Fire
from . import node, client

class CLI(object):
	"""A simple P2P messenger."""

	def node(self):
		"""Runs the node."""
		node.run()

	def ping(self):
		"""Pings local server."""
		client.ping()

	def post(self, msg: str):
		"""Posts chat message."""
		client.post(msg)


if __name__ == '__main__':
	Fire(CLI)
