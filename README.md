## 猜拳游戏

### 一、系统功能概览

#### 基础功能

* 设计并实现了一个单机模式下人机对战的猜拳游戏，支持在三局两胜规则下，提示玩家最终胜负的结论。

#### 进阶功能

* 将该系统改成网络版本，支持人机对战、联机对战两种游戏模式。

### 二、系统依赖与部署

* 编程语言：`Python 3.6`
* 简单图形库：`pygame 1.9.6`（仅客户端需要）
* 网络通信：`socket`
* 多线程：`threading`

服务器端运行`sever`目录下的 `server.py`；客户端运行`client`目录下的`client.py`。

### 三、系统功能实现

#### 服务器端

##### 已实现功能

1. 支持查看当前对战房间数量
2. 支持查看当前等待分配玩家数量
3. 支持主动关闭服务器

##### 执行流程说明

服务器端在内存中常驻一个用于监听客户端连接请求的socket，当有新玩家连接到服务器时，为其开启一个新的socket，分配一个唯一ID，并添加进待配对池。若系统中没有其他玩家，则令当前玩家处于忙等状态，待系统中进入其他玩家，经过配对得到其唯一对手，之后服务器作为中继代理帮助双方间接通信出拳内容。

#### 客户端

##### 已实现功能

1. 支持玩家自由选择人机对战或联机对战两种游戏模式
2. 给玩家实时反馈当前对战状况（用对战双方得分体现）
3. 在一局比赛（两/三轮有效出拳）结束之后，提示玩家最终胜负，系统主动回到主界面

##### 执行流程说明

客户端实时循环执行渲染图形界面、响应鼠标点击事件。

* 在联机对战模式下

  开启一个新线程及时响应鼠标点击事件向服务器发送信息，并根据服务器的反馈更新系统状态，进而更新图形界面。

* 在人机对战模式下

  相较于联网模式，客户端无需联网环境也可进行游戏。

通过定义3个状态来划分系统变更情况：

1. `current_scene`：取值范围为`[menuScene, waitScene, combatScene]`分别代表当前系统处于主界面、等待界面、对战界面。
2. `combat_state`：初始化为 -1，0代表人机对战，1代表联机对战。
3. `waiting_rival_join`：表示联机模式下对手是否进入房间，False代表等待用户加入，True代表用户已加入。

系统状态变更伪代码如下：

```python
# 获取鼠标点击位置
(x, y) = get_mouse_position()
if current_scene == 'menuScene':
    	# 选择人机对战模式
    	if (x, y) in man_machine_combat:
            combat_scene = 0
            current_scene = 'combatScene'
		# 选择联机对战模式
        elif (x, y) in online_combat:
            combat_scene = 1
            # 与服务器建立连接，等待服务器分配对手
            send_and_accpet_message()
            # 成功配对
            if success_pair():
				current_scene = 'waitScene'
                waiting_rival_join = False
            else:
                current_scene = 'combatScene'
                waiting_rival_join = True
elif current_scene == 'waitScene':
    # 忙等服务器分配对手
    while success_pair() == False:
        continue
    current_scene = 'combatScene'
    waiting_rival_join = True
elif current_scene == 'combatScene':
    # 人机对战
    if combat_state == 0:
        # 获取电脑出拳结果，并判断这轮输赢
        (nx, ny) = get_pc_punch()
        judge_winner((x,y), (nx,ny))
	# 联机对战
    elif combat_sate == 1:
        # 等待对手进入房间，忙等即可
        if waiting_rival_join == False:
            pass
        # 经由服务器获取对手出拳结果，并判断这轮输赢
        else:
            (nx, ny) = get_rival_punch()
            judge_winner((x,y), (nx,ny))    
```

系统界面根据系统状态变更而更新，逻辑一致，不再赘述。

### 四、不足之处

目前发现系统存在以下BUG尚未解决：

1. 联机模式下，对战双方游戏结束退回到主界面时，服务器端没有及时清理对应的系统信息，造成之后再一次选择联网模式出错。

   > 由于在联机模式下，服务器仅作为一个中继代理，因此无法知道对战双方何时结束退出。可以在服务器端保留一份双方对战信息，满足对战结束条件时，清理双方在服务器端的信息，如从已配对列表中移出等操作。

2. 服务器端还未运行之前，客户端运行并选择联机模式时会直接闪退。

   > 设置请求时间5s，如果在5s内还没有连接上服务器，提醒用户“当前网络存在问题，请优先考虑人机模式”。

3. 待排查......

未来可以添加的功能：

1. 做好容错处理。考虑客户端一方异常、双方异常、服务器异常等特殊情况发生时，给用户以友好提示，而不是程序直接闪退或黑屏。
2. 添加对战双方的聊天功能。用以提升游戏体验。