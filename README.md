# P2P Messenger

[![PDoc](http://img.shields.io/badge/pdoc-reference-blue.svg)](https://mg98.github.io/p2p-messenger/)
[![License](https://img.shields.io/github/license/mg98/p2p-messenger)](./LICENSE)

## About

This project came about as a group assignment for the lecture **"Peer-to-Peer Systems"** at the Humboldt University of Berlin.
The goal of this project was to create a decentralized application where users would be able to securely exchange messages in a peer-to-peer network.

## Requirements

- Python 3

## Getting Started

1. Create and activate a virtual environment, e.g. 
   ```bash
   conda create --name p2p-messenger python=3.9
   conda activate p2p-messenger
   ```
2. Install dependencies using `pip3 install -r requirements.txt`.
3. Run a node using `python -m p2p_messenger node -port=1337`. This node will be used as the bootstrapping peer.
4. In a second, separate terminal run a second node using `python -m p2p_messenger node -b="127.0.1.1:1337" -port=1338`. You may want to change the bootstrapping peer ip address in `-b` as it is dependent on your host machine.
5. In the first terminal find the `[INFO] Node with peer ID <peer_id>` log message and copy the peer ID.
6. In the second terminal, you can send a message from the second node to the first node using `python -m p2p_messenger post <peer_id> Hello node`. Replace the `<peer_id>` in the command accordingly.
7. In the first terminal you should see a `[INFO] Message content: <Hello node>` log message.

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
