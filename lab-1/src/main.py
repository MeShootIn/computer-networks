import enum
from threading import Thread
import time

import matplotlib.pyplot as plt
import numpy as np

class MessageStatus(enum.Enum):
    FAIL = 0
    SUCCESS = 1

class Message:
    def __init__(self, id, status):
        self.id = id
        self.status = status

class MessageQueue:
    def __init__(self, probability):
        self.msg_queue = []
        self.probability = probability

    def has_message(self):
        if len(self.msg_queue) > 0:
            return True
        return False

    def get_message(self):
        if self.has_message():
            result = self.msg_queue[0]
            self.msg_queue.pop(0)
            return result

    def send_message(self, msg):
        if np.random.rand() < self.probability:
            msg.status = MessageStatus.FAIL
        self.msg_queue.append(msg)


class Connecter():
    def __init__(self, window_size, timeout, max_num_messages, p):
        self.max_num_messages = max_num_messages
        self.window_size = window_size
        self.timeout = timeout
        self.is_finished = False
        self.send_messages = MessageQueue(p)
        self.receive_messages = MessageQueue(p)
        self.num_send_messages = 0


class GoBackN_sender():
    def __init__(self, connect):
        self.connect = connect
    def send(self):
        c = self.connect
        current_id = 0
        last_answer_id = -1
        start_time = time.time()

        while last_answer_id < c.max_num_messages:
            if c.receive_messages.has_message():
                answer = c.receive_messages.get_message()
                if answer.id == (last_answer_id + 1) % c.window_size:
                    last_answer_id += 1
                    start_time = time.time()
                else:
                    current_id = last_answer_id + 1

            if time.time() - start_time > c.timeout:
                current_id = last_answer_id + 1
                start_time = time.time()

            if current_id < last_answer_id + c.window_size and current_id <= c.max_num_messages:
                msg = Message(current_id % c.window_size, MessageStatus.SUCCESS)
                c.send_messages.send_message(msg)
                current_id += 1
                c.num_send_messages+=1

        c.is_finished = True


class GoBackN_receiver():
    def __init__(self, connect):
        self.connect = connect
    def receive(self):
        c = self.connect
        expected_id = 0
        while not c.is_finished:
            if c.send_messages.has_message():
                current_msg = c.send_messages.get_message()

                if current_msg.status == MessageStatus.FAIL:
                    continue

                if current_msg.id == expected_id:
                    ans = Message(current_msg.id, MessageStatus.SUCCESS)
                    c.receive_messages.send_message(ans)
                    expected_id = (expected_id + 1) % c.window_size


class WndMsgStatus(enum.Enum):
    BUSY = 0
    NEED_REPEAT = 1
    CAN_BE_USED = 2

class WndNode:
    def __init__(self, id):
        self.status = WndMsgStatus.NEED_REPEAT
        self.time = 0
        self.id = id

class SelectiveRepeat_sender():
    def __init__(self, connect):
        self.connect = connect
    def send(self):
        c = self.connect
        wnd_nodes = [WndNode(i) for i in range(c.window_size)]
        answer_count = 0

        while answer_count < c.max_num_messages:
            if c.receive_messages.has_message():
                answer = c.receive_messages.get_message()
                answer_count += 1
                wnd_nodes[answer.id].status = WndMsgStatus.CAN_BE_USED

            current_time = time.time()
            for i in range(c.window_size):
                if wnd_nodes[i].id > c.max_num_messages:
                    continue

                send_time = wnd_nodes[i].time
                if current_time - send_time > c.timeout:
                    wnd_nodes[i].status = WndMsgStatus.NEED_REPEAT


            for i in range(c.window_size):
                if wnd_nodes[i].id > c.max_num_messages:
                    continue

                if wnd_nodes[i].status == WndMsgStatus.BUSY:
                    continue

                elif wnd_nodes[i].status == WndMsgStatus.NEED_REPEAT:
                    wnd_nodes[i].status = WndMsgStatus.BUSY
                    wnd_nodes[i].time = time.time()

                    msg = Message(i, MessageStatus.SUCCESS)
                    c.send_messages.send_message(msg)
                    c.num_send_messages+=1

                elif wnd_nodes[i].status == WndMsgStatus.CAN_BE_USED:
                    wnd_nodes[i].status = WndMsgStatus.BUSY
                    wnd_nodes[i].time = time.time()
                    wnd_nodes[i].id = wnd_nodes[i].id + c.window_size

                    if wnd_nodes[i].id > c.max_num_messages:
                        continue

                    msg = Message(i, MessageStatus.SUCCESS)
                    c.send_messages.send_message(msg)
                    c.num_send_messages+=1

        c.is_finished = True


class SelectiveRepeat_receiver():
    def __init__(self, connect):
        self.connect = connect
    def receive(self):
        c = self.connect
        while not c.is_finished:
            if c.send_messages.has_message():
                current_msg = c.send_messages.get_message()

                if current_msg.status == MessageStatus.FAIL:
                    continue

                answer = Message(current_msg.id, MessageStatus.SUCCESS)
                c.receive_messages.send_message(answer)


def start(protocol, window_size, max_num_messages, timeout, probability):
    connect = Connecter(window_size, timeout, max_num_messages, probability)
    if protocol == 'GoBackN':
        sender = GoBackN_sender(connect)
        receiver = GoBackN_receiver(connect)
        sender_th = Thread(target=sender.send)
        receiver_th = Thread(target=receiver.receive)
    elif protocol == 'SelectiveRepeat':
        sender = SelectiveRepeat_sender(connect)
        receiver = SelectiveRepeat_receiver(connect)
        sender_th = Thread(target=sender.send)
        receiver_th = Thread(target=receiver.receive)
    timer_start = time.time()
    sender_th.start()
    receiver_th.start()
    sender_th.join()
    receiver_th.join()
    timer_end = time.time()

    return timer_end - timer_start, connect.num_send_messages

def draw_plot(x, y_GBN, y_SR, label, x_name, y_name, img_save_dst):
    fig, ax = plt.subplots()
    ax.plot(x, y_GBN, label='Go-Back-N')
    ax.plot(x, y_SR, label='Selective Repeat')
    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    ax.legend()
    fig.savefig(img_save_dst + label + '.png')
    plt.clf()

def windowsize_plot(window_sizes, timeout, probability, max_num_messages, img_save_dst):
    num_GBN = []
    num_SR = []
    time_GBN = []
    time_SR = []
    for ws in window_sizes:
        print(ws)
        time, num = start('GoBackN', ws, max_num_messages, timeout, probability)
        num_GBN.append(num)
        time_GBN.append(time)

        time, num = start('SelectiveRepeat', ws, max_num_messages, timeout, probability)
        num_SR.append(num)
        time_SR.append(time)

    draw_plot(window_sizes, num_GBN, num_SR, 'GBN_SR_num_ws', 'Ширина окна', 'Число сообщений', img_save_dst)
    draw_plot(window_sizes, time_GBN, time_SR, 'GBN_SR_time_ws', 'Ширина окна', 'Время', img_save_dst)

def probability_plot(window_size, timeout, probabilities, max_num_messages, img_save_dst):
    num_GBN = []
    num_SR = []
    time_GBN = []
    time_SR = []
    for p in probabilities:
        print(p)
        time, num = start('GoBackN', window_size, max_num_messages, timeout, p)
        num_GBN.append(num)
        time_GBN.append(time)

        time, num = start('SelectiveRepeat', window_size, max_num_messages, timeout, p)
        num_SR.append(num)
        time_SR.append(time)

    draw_plot(probabilities, num_GBN, num_SR, 'GBN_SR_num_prob', 'Вероятность потери сообщения', 'Число сообщений', img_save_dst)
    draw_plot(probabilities, time_GBN, time_SR, 'GBN_SR_time_prob', 'Вероятность потери сообщения', 'Время', img_save_dst)


if __name__ == '__main__':
    img_save_dst = '../docs/images/'
    window_size = 15
    timeout = 0.3
    probability = 0.3
    max_num_messages = 100

    probability_plot(window_size, timeout, np.linspace(0.1, 0.9, 9), max_num_messages, img_save_dst)
    windowsize_plot([int(x) for x in np.linspace(5, 45, 9)], timeout, probability, max_num_messages, img_save_dst)
