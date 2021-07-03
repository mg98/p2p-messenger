from fire import Fire
import logging
from datetime import datetime
import sys
from . import node, Config

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


if __name__ == '__main__':
	Config.load()

	log_filename = 'logs/' + datetime.now().strftime('%Y-%m-%d_%H:%M:%S.log')
	logging.basicConfig(
		format='%(asctime)s [%(levelname)s] %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S',
		encoding='utf-8',
		level=logging.DEBUG,
		handlers=[
			#logging.FileHandler(log_filename),
			logging.StreamHandler(stream=sys.stdout)
		]
	)

	Fire(CLI)
