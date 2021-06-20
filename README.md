# P2P Messenger

[![PDoc](http://img.shields.io/badge/pdoc-reference-blue.svg)](https://mg98.github.io/p2p-messenger/)
[![License](https://img.shields.io/github/license/mg98/p2p-messenger)](./LICENSE)

## About

This project came about as a group assignment for the lecture **"Peer-to-Peer Systems"** at the Humboldt University of Berlin.
The goal of this project was to create a decentralized application where users would be able to securely exchange messages in a peer-to-peer network.

## Requirements

- Python 3

## Getting Started

1. Install dependencies using `pip3 install -r requirements.txt`.
2. Run a node using `python3 -m p2p_messenger node`.
3. In a separate terminal, you can ping your node using `python3 -m p2p_messenger ping` or send a message using `python3 -m p2p_messenger post --msg='Hello node'`.

## Technical Specification

### Protocol

The protocol is based on TCP and is structured by a header of 16 bytes following a payload of variable length. The payload may as well be empty.

**Protocol Header:**

```
0                         16                        32
+------------+------------+------------+------------+
|   Version  |  Msg Type  |     TTL    |  Hop Count |
+------------+------------+------------+------------+
|        Sender Port      |      Payload Length     |
+------------+------------+------------+------------+
|             Original Sender IP Address            |
+------------+------------+------------+------------+
|                     Message ID                    |
+------------+------------+------------+------------+
```
