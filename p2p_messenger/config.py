import yaml


class Config:
	"""
	Static class holding configuration values loaded from `config.yml`.
	"""

	default_ip_addr = '127.0.0.1'
	"""Default IP address for the node."""

	default_port = 1337
	"""Default port for the node to listen."""

	neighbours = 5
	"""Minimum number of neighbours for a single node."""

	max_connections = 10
	"""Maximum number of concurrent connections for a single node."""

	prot_version = 1
	"""Version of the protocol this client uses to send messages."""

	prot_default_ttl = 5
	"""TTL value used when creating messages."""

	prot_max_ttl = 7
	"""Maximum allowed TTL of messages."""

	bootstrap_peer = (default_ip_addr, default_port)
	"""Tuple of ip and port of a running node used for bootstrapping into the network."""

	@classmethod
	def load(cls):
		"""Load configuration values from `config.yml` and update values in class."""
		with open('./config.yml', 'r') as f:
			config = yaml.safe_load(f)
			cls.default_ip = config['default_ip']
			cls.default_port = config['default_port']
			cls.neighbours = config['neighbours']
			cls.max_connections = config['max_connections']
			cls.prot_version = config['protocol']['version']
			cls.prot_default_ttl = config['protocol']['ttl']
			cls.prot_max_ttl = config['protocol']['max_ttl']
			cls.bootstrap_peer = (config['bootstrap']['ip'], config['bootstrap']['port'])
