'''
客户端
write by caiyiwu
'''
import pygame
import sys
import socket
import random
import configparser
from threading import Thread


class Client:
    def __init__(self):
        # 加载配置信息
        self.config_path = 'config.ini'
        config = configparser.ConfigParser()
        config.read(self.config_path)
        self.config = config['def']
        # 加载界面素材
        self.load_material()
        # 系统参数初始化
        self.current_scene = self.config['MENU_SCENE']  # 初始系统状态
        self.waiting_rival_join = True  # 等待对手进入房间
        self.combat_state = -1  # 人机对战模式为0，联机对战模式为1,初始化为-1
        self.rival_id = ''  # 对手的id
        self.my_punch = -1  # 己方出拳，0,1,2分别代表剪刀、石头、布
        self.rival_punch = -1  # 对手出拳
        self.rival_score = 0  # 对手得分
        self.my_score = 0  # 己方得分
        self.info = ''  # 提示信息
        self.client = None  # 客户端实例
        self.flag = 0

    def load_material(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('猜拳游戏')
        self.screen = pygame.display.set_mode(
            (int(self.config['INTERFACE_WIDTH']), int(self.config['INTERFACE_HEIGHT'])), 0, 32)
        # 确保客户端有此字体，否则无法正常显示中文
        self.font = pygame.font.SysFont('SimHei', 20)
        self.big_font = pygame.font.SysFont('SimHei', 40)
        # 加载图片资源
        self.scissors = pygame.image.load(self.config['SCISSORS_PATH'])
        self.rock = pygame.image.load(self.config['ROCK_PATH'])
        self.paper = pygame.image.load(self.config['PAPER_PATH'])
        self.man_machine_combat_button = pygame.image.load(self.config['MAN_MACHINE_COMBAT_BUTTON'])
        self.online_combat_button = pygame.image.load(self.config['ONLINE_COMBAT_BUTTON'])

    def send_error(self):
        '''
        联网情况下，发生异常主动通知服务器
        :return: 
        '''
        try:
            msg = self.config['ERROR']
            self.client.sendall(msg.encode('utf-8'))
        except:
            pass
        pygame.quit()
        sys.exit()

    def judge_punch(self, x, y):
        '''
        根据点击的坐标判断出拳类型
        :param x:
        :param y:
        :return: 1，2，3 or -1, -1 代表鼠标点击没有落在有效区域
        '''
        top = int(self.config['PUNCH_TOP'])
        scissors_left = int(self.config['SCISSORS_LEFT'])
        rock_left = int(self.config['ROCK_LEFT'])
        paper_left = int(self.config['PAPER_LEFT'])
        if top <= y <= self.scissors.get_height() + top:
            if scissors_left <= x <= self.scissors.get_width() + scissors_left:
                return 1
            elif rock_left <= x <= self.rock.get_width() + rock_left:
                return 2
            elif paper_left <= x <= self.paper.get_width() + paper_left:
                return 3
        return -1

    def judge_mode(self, x, y):
        '''
        根据点击的坐标判断游戏模式
        :param x:
        :param y:
        :return: 更改combat_state的同时，函数返回 True or False
        '''
        top = int(self.config['BUTTON_TOP'])
        first_button_left = int(self.config['FIRST_BUTTON_LEFT'])
        second_button_left = int(self.config['SECOND_BUTTON_LEFT'])
        if top <= y <= self.man_machine_combat_button.get_height() + top:
            if first_button_left <= x <= self.man_machine_combat_button.get_width() + first_button_left:
                # 代表人机模式
                self.combat_state = 0
                return True
            elif second_button_left <= x <= self.online_combat_button.get_width() + second_button_left:
                # 代表联机模式
                self.combat_state = 1
                return True
        return False

    def judge_winner(self):
        '''
        根据双方出拳类型来决定胜负
        :return: 平局0，胜利1，失败-1
        '''
        print(self.my_punch + '---' + self.rival_punch)
        tied_context, winner_context, loser_context = '这一轮平局', '这一轮你赢了', '这一轮你输了'
        self.info = ''
        if self.rival_punch == self.config['SCISSORS']:
            self.info = '对方出剪刀，'
            if self.my_punch == self.config['SCISSORS']:
                self.info += tied_context
            elif self.my_punch == self.config['ROCK']:
                self.my_score += 1
                self.info += winner_context
            elif self.my_punch == self.config['PAPER']:
                self.rival_score += 1
                self.info += loser_context
        elif self.rival_punch == self.config['ROCK']:
            self.info = '对方出石头，'
            if self.my_punch == self.config['ROCK']:
                self.info += tied_context
            elif self.my_punch == self.config['PAPER']:
                self.my_score += 1
                self.info += winner_context
            elif self.my_punch == self.config['SCISSORS']:
                self.rival_score += 1
                self.info += loser_context
        elif self.rival_punch == self.config['PAPER']:
            self.info = '对方出布，'
            if self.my_punch == self.config['PAPER']:
                self.info += tied_context
            elif self.my_punch == self.config['SCISSORS']:
                self.my_score += 1
                self.info += winner_context
            elif self.my_punch == self.config['ROCK']:
                self.rival_score += 1
                self.info += loser_context
        else:
            self.info = '请你出拳'

        if self.rival_score >= 2 or self.my_score >= 2:
            state = '赢得' if self.my_score == 2 else '输掉'
            self.info += '。三轮过后，你' + state + '比赛，再次点击返回主界面。'
            self.flag += 1
        print(self.info)

    def send_and_accpet_message(self, msg):
        '''
        与服务器通信
        :param msg: 
        :return: 
        '''
        try:
            my_punch = msg
            self.client.sendall(msg.encode('utf-8'))
            # 接受服务器的反馈数据
            while True:
                msg = self.client.recv(1024).decode('utf-8')
                # 收到游戏模式的选择
                if len(msg) >= 2:
                    # 去掉前缀
                    self.rival_id = msg[3:]
                    self.waiting_rival_join = True
                    self.current_scene = self.config['COMBAT_SCENE']
                # 收到当前对手还未进入房间的消息，更新到等待界面之后接着发REQ_CONN的请求
                elif msg == self.config['WAIT_RIVAL']:
                    self.waiting_rival_join = False
                    self.current_scene = self.config['WAIT_SCENE']
                    self.update_scene()
                    msg = self.config['REQ_CONN']
                    self.client.sendall(msg.encode('utf-8'))
                    continue
                # 收到对手的出拳类型
                elif msg == self.config['SCISSORS'] or msg == self.config['ROCK'] or msg == self.config['PAPER']:
                    self.rival_punch = msg
                    # 更改经过这一回合之后的分数情况
                    print(my_punch + "----" + msg)
                    self.judge_winner()
                break

        except:
            self.send_error()

    def click_event(self, x, y):
        try:
            # 在主界面
            if self.current_scene == self.config['MENU_SCENE']:
                # 选择联机模式，告知服务器
                if self.judge_mode(x, y) == True:
                    if self.combat_state == 1:
                        if self.client == None:
                            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            self.client.connect((self.config['HOST'], int(self.config['PORT'])))
                        msg = self.config['REQ_CONN']
                        thread = Thread(target=self.send_and_accpet_message, args=(msg,))
                        thread.start()
                    # 选择人机模式，在judge_mode中变更了状态即可
                    elif self.combat_state == 0:
                        self.current_scene = self.config['COMBAT_SCENE']
                        print('选择人机模式')

            elif self.current_scene == self.config['WAIT_SCENE']:
                msg = self.config['REQ_CONN']
                thread = Thread(target=self.send_and_accpet_message, args=(msg,))
                thread.start()
            # 在游戏界面
            elif self.current_scene == self.config['COMBAT_SCENE']:
                # 人机对战模式
                if self.combat_state == 0:
                    punch_id = self.judge_punch(x, y)
                    if punch_id != -1:
                        self.my_punch = str(punch_id)
                        # 电脑随机出拳
                        self.rival_punch = str(random.randint(1, 3))
                        self.judge_winner()
                # 联机对战模式
                else:
                    # 等待对手加入，无需额外处理
                    if self.waiting_rival_join == False:
                        pass
                    # 对手已经在房间，判断己方出拳类型
                    else:
                        punch_id = self.judge_punch(x, y)
                        if punch_id != -1:
                            # 向服务器端发送出拳类型
                            self.my_punch = str(punch_id)
                            msg = self.my_punch
                            thread = Thread(target=self.send_and_accpet_message, args=(msg,))
                            thread.start()

        except:
            self.send_error()

    def update_scene(self):

        if self.current_scene == self.config['MENU_SCENE']:
            # 第一个界面，展示两个模式的按钮
            self.screen.fill((255, 255, 255))
            self.screen.blit(self.man_machine_combat_button, (200, 350))
            self.screen.blit(self.online_combat_button, (500, 350))
            title_text = self.font.render('请选择对战模式', 1, (177, 177, 177))
            self.screen.blit(title_text, (420, 250))
            pygame.display.update()
        elif self.current_scene == self.config['WAIT_SCENE']:
            self.screen.fill((255, 255, 255))
            title_text = self.big_font.render('等待另一位玩家...', 1, (254, 177, 6))
            self.screen.blit(title_text, (380, 380))
            pygame.display.update()
        elif self.current_scene == self.config['COMBAT_SCENE']:
            # 说明经过有效三局比赛，清空状态，回到主界面
            # flag用于先显示比赛结果，再返回主界面这两个连贯过程
            if self.flag == 2:
                self.__init__()
            else:
                self.screen.fill((255, 255, 255))
                # 人机模式或者联机模式界面基本一致
                role = '电脑' if self.combat_state == 0 else '玩家'
                my_score = self.font.render("我的分数: " + str(self.my_score), 1, (0, 0, 0))
                rival_score = self.font.render("对手分数: " + str(self.rival_score), 1, (0, 0, 0))
                title_text = self.big_font.render('与' + role + '对战', 1, (0, 0, 0))
                info = self.font.render(self.info, 1, (0, 0, 0))
                self.screen.blit(title_text, (400, 100))
                self.screen.blit(info, (300, 500))
                self.screen.blit(my_score, (350, 200))
                self.screen.blit(rival_score, (550, 200))
                self.screen.blit(self.scissors, (150, 250))
                self.screen.blit(self.rock, (400, 250))
                self.screen.blit(self.paper, (650, 250))
                pygame.display.update()


if __name__ == '__main__':
    client = Client()
    # 轮流执行渲染图形界面、响应鼠标点击事件
    while True:
        client.update_scene()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.send_error()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                print(x, y)
                client.click_event(x, y)
