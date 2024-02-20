import enum

import matplotlib.pyplot as plt
import numpy as np

class MessageType(enum.Enum):
    HAVE = 0
    READY_TO_EXCHANGE = 1
    NOT_READY_TO_EXCHANGE = 2
    EXCHANGE = 3

class Message:
    def __init__(self, sender, type, data):
        self.sender = sender
        self.type = type
        self.data = data

class Connecter():
    def __init__(self, receiver):
        self.receiver = receiver
        self.ready_to_exchange = False
    def send(self, msg):
        self.receiver.msg_queue.append(msg)
    def is_ready(self):
        return self.ready_to_exchange
    def ready(self):
        self.ready_to_exchange = True
    def not_ready(self):
        self.ready_to_exchange = False


class Tracker:
    def __init__(self):
        self.peers = dict() # file_id : пиры с файлом
    def connect_peer(self, peer):
        file_id = peer.hash_sum_file
        if self.peers.get(file_id) == None:
            peers_with_file = dict()
            self.peers[file_id] = [peer]
        else:
            peers_with_file = self.peers[file_id].copy()
            self.peers[file_id].append(peer)
        return peers_with_file


class Peer:
    def __init__(self, tracker, hash_sum_file, have, id):
        self.id = id
        self.hash_sum_file = hash_sum_file
        self.have_segments = [] # номера имеющихся сегментов
        self.need_segments = [i for i in range(hash_sum_file)]
        self.peer_last_exchange_id = None
        self.file = ['-']*hash_sum_file
        for h in have:
            self.add_data_to_file(h)
        self.tracker = tracker
        self.peers = [] # список пиров с нужными данными
        self.connections = dict() # peer_id : connecter
        self.msg_queue = []
        self.is_finished = False
        #print(self.id, self.file)

    def add_data_to_file(self, data):
        self.file[data[0]] = data[1]
        self.have_segments.append(data[0])
        self.need_segments.remove(data[0])

    def connect_tracker(self):
        self.peers = self.tracker.connect_peer(self)

    def connect_peer(self, other):
        if not self.is_connected(other.id):
            self.connections[other.id] = Connecter(other)
            self.send_have_msg(other)
            if not other.is_connected(self.id):
                other.connect_peer(self)
    def is_connected(self, other_id):
        if len(self.connections.keys()) > 0:
            return other_id in self.connections.keys()
        else:
            return False

    def send_message(self, other, msg):
        self.connections[other.id].send(msg)
    def send_have_msg(self, other):
        msg = Message(self, MessageType.HAVE, self.have_segments)
        self.send_message(other, msg)
    def send_rte_msg(self, other, get_segments):
        msg = Message(self, MessageType.READY_TO_EXCHANGE, get_segments)
        self.send_message(other, msg)
    def send_not_rte_msg(self, other):
        msg = Message(self, MessageType.NOT_READY_TO_EXCHANGE, None)
        self.send_message(other, msg)
    def send_exchange_msg(self, other, send_segments):
        msg = Message(self, MessageType.EXCHANGE, send_segments)
        self.send_message(other, msg)

    def receive_message(self):
        is_change_file = False
        if len(self.msg_queue) > 0:
            msg = self.msg_queue[0]
            self.msg_queue.pop(0)
            if msg.type == MessageType.HAVE:
                other_have = list(msg.data)
                get_segments = list(set(self.need_segments).intersection(other_have))
                if len(get_segments) > 0:
                    self.connections[msg.sender.id].ready()
                    self.send_rte_msg(msg.sender, get_segments[0])
                elif self.is_finished:
                    self.connections[msg.sender.id].ready()
                    self.send_rte_msg(msg.sender, None)
                else:
                    self.send_not_rte_msg(msg.sender)
            elif msg.type == MessageType.READY_TO_EXCHANGE and self.connections[msg.sender.id].is_ready():
                if msg.data != None:
                    self.send_exchange_msg(msg.sender, [msg.data, self.file[msg.data]])
            elif msg.type == MessageType.EXCHANGE:
                is_change_file = True
                self.add_data_to_file(msg.data)
                self.peer_last_exchange_id = msg.sender.id
                for p in self.peers:
                    self.send_have_msg(p)
                if len(self.need_segments) == 0:
                    self.is_finished = True
                else:
                    self.connections[msg.sender.id].not_ready()
                #print(self.id, self.file)
        return is_change_file

    def start(self):
        self.connect_tracker()
        for p in self.peers:
            self.connect_peer(p)


def coord_nodes(num):
    x, y = [], []
    max_num = 5
    angles = np.linspace(-np.pi - np.pi/2, np.pi/2 , num, endpoint=False)
    for a in np.roll(np.flip(angles),1):
        x.append(max_num * np.cos(a))
        y.append(max_num * np.sin(a))
    return x, y

def draw_tracker_connect(peers, x_coords, y_coords):
    for x, y, peer in zip(x_coords, y_coords, peers):
        plt.plot([x, 0], [y, 0], color='blue')
        tracker_info = [p.id for p in peer.peers]
        plt.annotate(str(peer.id)+' : '+str(tracker_info), (x-0.2, y+0.2))
        #plt.arrow(x, y, -x*0.8, -y*0.8, head_width=0.15 ,color='blue')
    plt.plot(x_coords, y_coords, 'go', label='peer')
    plt.plot(0, 0, 'ro', label='tracker')
    plt.xlim(-6, 6)
    plt.ylim(-5, 6)
    plt.legend()
    plt.show()

def draw_peers_connect(peers, x_coords, y_coords):
    for x, y, peer in zip(x_coords, y_coords, peers):
        j = peer.peer_last_exchange_id
        if j!=None:
            plt.plot([x, x_coords[j]], [y, y_coords[j]], color='blue')
        plt.annotate(str(peer.id)+' : '+ ''.join(peer.file), (x-0.2, y+0.2))
    plt.plot(x_coords, y_coords, 'go', label='peer')
    plt.plot(0, 0, 'ro', label='tracker')
    plt.xlim(-6,6)
    plt.ylim(-5,6)
    plt.legend()
    plt.show()

if __name__ == '__main__':
    tracker = Tracker()
    data = 'hello'
    num = len(data)
    peers = []
    for i in range(num):
        p = Peer(tracker, num, [[i,data[i]]], i)
        peers.append(p)
        p.start()
    x_coords, y_coords = coord_nodes(num)
    draw_tracker_connect(peers, x_coords, y_coords)
    draw_peers_connect(peers, x_coords, y_coords)
    num_finished = 0
    n = 0
    while(num_finished < num):
        num_finished = 0
        for p in peers:
            if p.receive_message():
                n+=1
            if p.is_finished:
                num_finished+=1
        if(n>=2):
            draw_peers_connect(peers, x_coords, y_coords)
            n = 0

