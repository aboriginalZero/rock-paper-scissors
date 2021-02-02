'''
服务器端
write by caiyiwu
'''

import socket
from threading import Thread
import configparser


class Server:

    def __init__(self):
        # 加载配置信息
        self.config_path = 'config.ini'
        config = configparser.ConfigParser()
        config.read(self.config_path)
        self.config = config['def']
        # 初始化服务器
        self.address = (self.config['HOST'], int(self.config['PORT']))
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_socket.bind(self.address)
        self.listening_socket.listen(5)
        print('服务器已启动，等待用户连接.....')
        # 系统参数初始化
        self.paired_map = dict()    # 已配对的玩家映射表
        self.id2context = dict()    # 玩家ID与出拳内容映射表
        self.waiting_pool = list()  # 待配对池
        self.idx = 0                # 客户端连接编号
        self.id2client = dict()     # 编号与客户端socket映射表
        # 开启一个接受连接的守护线程
        self.recv_thread = Thread(target=self.accept_client)
        self.recv_thread.setDaemon(True)
        self.recv_thread.start()

    def accept_client(self):
        '''
        监听玩家请求
        :return:
        '''
        while True:
            client, _ = self.listening_socket.accept()
            # 暂时认为最多有这么多用户在线
            self.idx = (self.idx + 1) % 1000000007
            # 建立映射关系
            self.id2client[self.idx] = client
            # 为该玩家新起一个线程
            thread = Thread(target=self.accept_and_send_message, args=(self.idx,))
            thread.setDaemon(True)
            thread.start()

    def accept_and_send_message(self, id):
        '''
        与编号为id的客户端通信
        :param id: 服务器分配而来的编号
        :return:
        '''
        client = self.id2client[id]
        while True:
            msg = client.recv(1024).decode('utf-8')
            if msg == self.config['ERROR']:
                client.close()
                try:
                    rival_id = self.paired_map[id]
                    #TODO 此玩家挂掉，给他的对手一个提醒之后，把对手放入等待区匹配下一个对手，存在BUG
                    msg = '您的对手主动离开或掉线，请您稍等片刻，系统将为您分配新对手'
                    self.id2client[rival_id].sendall(msg.encode(encoding='utf-8'))
                    del self.paired_map[id]
                    del self.paired_map[rival_id]
                    del self.id2client[id]
                    self.waiting_pool.append(rival_id)
                    print('有一个客户端下线了')
                except:
                    # 后续更改处理
                    pass
                return
            # 玩家等待对手匹配
            elif msg == self.config['WAIT_RIVAL']:
                if id in self.paired_map.keys():
                    rival_id = self.paired_map[id]
                    msg = self.config['PREFIX'] + str(rival_id)
                    client.sendall(msg.encode(encoding='utf-8'))
            # 玩家发起连接请求
            elif msg == self.config['REQ_CONN']:
                # TODO 这块逻辑会有问题，无法应对玩家离开房间再次进来等情况
                # 用户选择联机模式之后才将id加入待分配池
                if id not in self.waiting_pool:
                    self.waiting_pool.append(id)
                # 如果后端分配好对手，则返回对手编号
                if id in self.paired_map.keys():
                    rival_id = self.paired_map[id]
                    msg = self.config['PREFIX'] + str(rival_id)
                    client.sendall(msg.encode(encoding='utf-8'))
                else:
                    # 玩家数不够造成的无法配对
                    if len(self.waiting_pool) == 1:
                        msg = self.config['WAIT_RIVAL']
                        client.sendall(msg.encode(encoding='utf-8'))
                    # 初次匹配通知玩家对手ID信息
                    else:
                        rival_id = self.waiting_pool.pop(0)
                        msg = self.config['PREFIX'] + str(id)
                        rival_client = self.id2client[rival_id]
                        rival_client.sendall(msg.encode(encoding='utf-8'))
                        self.paired_map[id] = rival_id
                        self.paired_map[rival_id] = id
                        msg = self.config['PREFIX'] + str(rival_id)
                        client.sendall(msg.encode(encoding='utf-8'))
                        print(str(id) + '号玩家与' + str(rival_id) + '号玩家匹配成功')

            # 玩家发来的是出拳类型，此时服务器作为终极代理帮助双方间接通信
            elif msg == self.config['SCISSORS'] or msg == self.config['ROCK'] or msg == self.config['PAPER']:
                self.id2context[id] = msg
                rival_id = self.paired_map[id]
                # 轮询等待对手出拳结果
                while rival_id not in self.id2context:
                    continue

                client.sendall(self.id2context[rival_id].encode(encoding='utf-8'))
                # 一轮通信完及时删除该轮信息
                del self.id2context[rival_id]


if __name__ == '__main__':
    server = Server()
    while True:
        cmd = input("""--------------------------
                        输入1:查看当前对战房间数量
                        输入2:查看当前等待分配玩家数量
                        输入3:关闭服务端
                        """)
        if cmd == '1':
            print('--------------------------')
            print('当前对战房间数量：', int(len(server.paired_map) / 2))
        elif cmd == '2':
            print('--------------------------')
            print('当前等待分配玩家数量：', len(server.waiting_pool))
        elif cmd == '3':
            exit()
