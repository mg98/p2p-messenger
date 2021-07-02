import yaml

class Config:
	"""
	Static class holding configuration values loaded from `config.yml`.
	"""

	default_port = 1337
	"""Default port for the node to listen."""

	neighbours = 5

	max_connections = 5
	"""Maximum number of concurrent connections for a single node."""

	prot_version = 1
	"""Version of the protocol this client uses to send messages."""

	prot_default_ttl = 5
	"""TTL value used when creating messages."""

	bootstrap_peer = ('127.0.0.1', 1337)
	"""Tuple of ip and port of a running node used for bootstrapping into the network."""

	@classmethod
	def load(cls):
		"""Load configuration values from `config.yml` and update values in class."""
		with open('./config.yml', 'r') as f:
			config = yaml.safe_load(f)
			cls.default_port = config['default_port']
			cls.neighbours = config['neighbours']
			cls.max_connections = config['max_connections']
			cls.prot_version = config['protocol']['version']
			cls.prot_default_ttl = config['protocol']['ttl']
			cls.bootstrap_peer = (config['bootstrap']['ip'], config['bootstrap']['port'])
