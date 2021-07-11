from fire import Fire
import logging
from datetime import datetime
import sys
from . import Config
from .node import Node


class CLI(object):
	"""A simple P2P messenger."""

	@staticmethod
	def node(port=None, b=None):
		"""Runs the node."""

		if port is None:
			port = Config.default_port

		if b:
			if isinstance(b, int):
				address = (Config.default_ip_addr, b)
			else:
				b_ip, b_port = tuple(b.split(':', maxsplit=1))
				b_port = int(b_port)
				address = (b_ip, b_port)
		else:
			address = Config.bootstrap_peer
		logging.debug('Address: %s', address)
		Node(port).run(address)


if __name__ == '__main__':
	Config.load()

	log_filename = 'logs/' + datetime.now().strftime('%Y-%m-%d_%H:%M:%S.log')
	# noinspection PyArgumentList
	logging.basicConfig(
		format='%(asctime)s [%(levelname)s] %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S',
		encoding='utf-8',
		level=logging.DEBUG,
		handlers=[
			logging.FileHandler(log_filename),
			logging.StreamHandler(stream=sys.stdout)
		]
	)

	Fire(CLI)
