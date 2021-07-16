import os
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

		node = Node(port, address)
		node.start()

		try:
			while True:
				cmd = input('Command: ')
				cmd_parts = cmd.split(' ')
				if len(cmd_parts) == 0:
					print('Invalid command.')
					continue

				if cmd_parts[0] == 'neighbours':
					print('Inbound neighbours: ', node.inbound_neighbours)
					print('Outbound neighbours: ', node.outbound_neighbours)
				elif cmd_parts[0] == 'post':
					if len(cmd_parts) < 3:
						print('Invalid command. Usage: post <peer-id> <message>')
						continue
					peer_id = cmd_parts[1]
					payload = 'hallo'

					# TODO: Encrypt payload with "peer_id" (derive public key of it).
					node.post_msg(chat_msg=payload, peer_id=peer_id)
				else:
					print('Unknown command.')
		except Exception as e:
			logging.exception(e)
			try:
				node.shutdown()
			except Exception as e:
				logging.exception(e)
			finally:
				os._exit(1)


def clean_peer_id(peer_id):
	"""Removes quotes from peer id"""
	peer_id = peer_id.replace('"', '').replace("'", "")
	return peer_id


if __name__ == '__main__':
	Config.load()

	log_filename = 'logs/' + datetime.now().strftime('%Y-%m-%d_%H:%M:%S.log')
	# noinspection PyArgumentList
	logging.basicConfig(
		format='%(asctime)s [%(levelname)s] %(message)s [%(threadName)s]',
		datefmt='%Y-%m-%d %H:%M:%S',
		encoding='utf-8',
		level=logging.DEBUG,
		handlers=[
			logging.FileHandler(log_filename),
			logging.StreamHandler(stream=sys.stdout)
		]
	)

	Fire(CLI)
