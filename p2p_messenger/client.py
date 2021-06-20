import socket
import yaml
from .config import Config
from p2p_messenger.protocol import *
from p2p_messenger import protocol

def ping():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('127.0.0.1', Config.default_port))
	s.send(protocol.PingMessage().bytes())

def post(msg: str):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('127.0.0.1', Config.default_port))
	s.send(protocol.PostMessage(msg).bytes())
