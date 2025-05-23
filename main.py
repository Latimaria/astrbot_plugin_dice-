from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig
# from astrbot.core.star.filter.event_message_type import EventMessageType
from astrbot.api.event.filter import *
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
                AiocqhttpMessageEvent
from astrbot.api.message_components import Poke,Plain
import astrbot.api.message_components as Comp
from astrbot.core.message.components import Plain, Image, At, Reply, Record, File, Node

import random
import re
import json
import os
import uuid
import datetime
import copy
import time

import rolldice

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__)) 
DATA_DIR = os.path.dirname(os.path.dirname(PLUGIN_DIR))
DICE_DATA_DIR = os.path.join(DATA_DIR, "astrbot_plugin_dice-")

USER_DIR = os.path.join(DICE_DATA_DIR, "users")
GROUP_DIR = os.path.join(DICE_DATA_DIR, "groups")
# LOG_DIR = os.path.join(DICE_DATA_DIR, "game_logs")
PC_COMMANDS = ["new", "tag", "show", "nn", "cpy", "del", "list", "clear"]
failll_keys = ["大失败", "(wink)", "99"]
EXPRESSION_MAX_TOKENS = 42

COMMANDS = ["rd", "rh", "jrrp", "ra", "draw", "log", "st", "群友cp", "poke"]
KEYWORDS = []
POKE_KEYWORDS = ["戳", "poke"]
# -- data
#      \___ user1 __ PC1 
#              \____ PC2

# class Character():
#     def __init__(self):
#         valid = False
#         name = None
#         owner = None
#         path = None
#     def store(self):
#         if not self.valid:
#             print("invalid character")
#             return None
def create_parents(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

def extract_outer_braces(text):
    results = []
    brace_level = 0
    start = None
    for i, char in enumerate(text):
        if char == '{':
            if brace_level == 0:
                start = i + 1  # skip the opening brace
            brace_level += 1
        elif char == '}':
            brace_level -= 1
            if brace_level == 0 and start is not None:
                results.append(text[start:i])
                start = None
    return results

def read_lines(file_path, max_lines=None):
    f = open(file_path, "r")
    if max_lines:
        lines = f.readlines(max_lines)
    else:
        lines = f.readlines()
    f.close()
    lines = [line.rstrip("\n") for line in lines]
    return lines
def read_last_n_lines(file_path, n, buffer_size=1024, count_empty=True):
    with open(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        end = f.tell()
        lines = []
        block = b''
        while end > 0 and len(lines) <= n:
            # Move the pointer back by buffer_size (or less if near the start)
            read_size = min(buffer_size, end)
            end -= read_size
            f.seek(end)
            block = f.read(read_size) + block
            lines = block.split(b'\n')
        
        if count_empty:
            lines = [line.decode('utf-8') for line in lines[-n:]]
        else:
            lines = [line.decode('utf-8') for line in lines[-n:] if line]
        return lines

def read_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
def write_json(filepath, data):
    create_parents(filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
def read_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()
def write_txt(filepath, data):
    create_parents(filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(data)
def append_txt(filepath, data):
    create_parents(filepath)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(data)

def string_to_deck(deck_str):
    deck = extract_outer_braces(deck_str)
    if len(deck) < 1:
        return "", []
    deck_name = deck[0]
    cards = deck[1:] if len(deck)>1 else []
    cards = [card.replace(r"\n", "\n") for card in cards]
    return deck_name, cards
def deck_to_string_to_deck(deck_name, cards):
    deck_str = "{"+ deck_name + "} "
    cards = ["{" + card.replace("\n", r"\n") + "}" for card in cards]
    deck_str += " ".join(cards)
    return deck_str

@register("Dice!", "Lacki", "一个简单的 Hello World 插件", "0.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        logger.info("decks:" + str(self.config.decks))
        self.decks = {}
        self.cp_texts = []
        self.load_decks()
        self.cooling_down = False
        self.cooling_end_time = 0

    def load_decks(self):
        logger.info("loading decks")
        if not self.config.decks:
            logger.info("NO decks")
            return
        for deck_str in self.config.decks:
            logger.info("deck: "+ deck_str)
            deck_name, cards = string_to_deck(deck_str)
            if deck_name == "":
                logger.info("invalid deck:\n "+ deck_str)
                continue
            if deck_name in self.decks and self.decks[deck_name] and self.decks[deck_name]!=[]:
                self.decks[deck_name] += cards
            else:
                self.decks[deck_name] = cards
        for cp_str in self.config.cp:
            logger.info("cp text: "+ cp_str)
            cp_str = cp_str.replace(r"\n", "\n")
            self.cp_texts.append(cp_str)
    
    # def add_deck(self, deck):
    #     deck_str = [card.replace("\n", r"\n") for card in deck]
    #     logger.info("add deck: "+ deck_str)
    #     deck = extract_outer_braces(deck_str)
    #     if len(deck) < 1:
    #         reply = "invalid deck\n "
    #         return reply
    #     deck_name = deck[0]
    #     deck = deck[1:] if len(deck)>1 else []
    #     if deck_name in self.decks and self.decks[deck_name] and self.decks[deck_name]!=[]:
    #         self.decks[deck_name] += deck
    #     else:
    #         self.decks[deck_name] = deck
    #     self.config.decks = "}{".join(self.decks)
    #     self.config.save_config()

    def _load_admins(self):
        """加载管理员列表"""
        try:
            with open(os.path.join('data', 'cmd_config.json'), 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
                return config.get('admins_id', [])
        except Exception as e:
            self.context.logger.error(f"加载管理员列表失败: {str(e)}")
            return []   
    def is_admin(self, user_id):
        """检查用户是否为管理员"""
        return str(user_id) in self.admins   

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        '''这是一个 hello world 指令''' # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''


    def parse_message(self, message_str, command="rd"):
        message = message_str.removeprefix(command)
        
        message = message.replace("x", "*").replace("X", "*")
        message = message.strip().lower()
        return message


    def roll_dice(self, expression, result_only=False):
        """roll dice"""
        result = None
        explanation = None
        
        if not expression or expression=="":
            expression="1d100"
        elif (not isinstance(expression, str)) or expression.isnumeric():
            expression = "d" + str(expression)
        
        try:
            result, explanation = rolldice.roll_dice(expression)
            logger.info(f"Result: {result}")
            logger.info(f"Explanation: {explanation}")
        except:
            logger.error(f"Dice! Error: failed to parse: {expression}")

        if result_only:
            return result
        return result, explanation, expression

    def roll_dice_with_message(self, message, command=None):
        result = None
        explanation = None
        if command:
            message = message.removeprefix(command)
        message = message.strip().lower()
        message = message.replace("x", "*")
        message_tokens = message.split(' ')
        num_tokens = min(len(message_tokens), EXPRESSION_MAX_TOKENS)
        for i in range(num_tokens, -1, -1):
            expression = ' '.join(message_tokens[:i])
            result, explanation, expression = self.roll_dice(expression)
            if result:
                reason = " ".join(message_tokens[i:])
                break
        return result, explanation, expression, reason
    def roll_dice_get_reply(self, message, command=None):
        result, explanation, expression, reason = self.roll_dice_with_message(message, command)
        if not result:
            return None, f"message_str: {message}\n failed to parse"
        reply = "由于 " + reason + ": \n"
        reply += f"{expression}=[{explanation}]={result} \n"
        reply += f"种出了{result}根小黄瓜"
        if result > 95:
            reply += ":)"
        elif result <= 5:
            reply += ":("
        return result, reply

    @filter.command("rd")
    async def rd(self, event: AstrMessageEvent):
        """roll dice"""
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        # expression = self.parse_message(message_str)
        result, dice_reply = self.roll_dice_get_reply(message_str, "rd")

        if result:
            reply = f"<{user_name}>的检定结果\n"
            reply += dice_reply
        else:
            reply = dice_reply
        
        yield event.plain_result(reply) 

    def roll_two(self, num):
        idx_1 = self.roll_dice(num, True)-1
        idx_2 = self.roll_dice(num-1, True)-1
        if idx_2 >= idx_1:
            idx_2 += 1
        return idx_1, idx_2
    @filter.command("群友cp")
    async def roll_cp(self, event: AstrMessageEvent):
        """qun you cp"""
        reply = ""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        if not group_id:
            reply = "not in a group"
            yield event.plain_result(reply) 
            return
        candidates = self.get_group_cp_candidates(group_id)
        if not (str(user_id)) in candidates:
            self.add_group_cp_candidate(group_id, user_id)
        num_candidates = len(candidates)
        # reply = f"num candidates: {num_candidates}\n"
        if num_candidates < 3:
            reply = "少于三人用过此指令！"
            yield event.plain_result(reply) 
            return
        
        # text = r"群友1:(群友1)\n群友2:(群友2)\n"
        text = self.draw_from_cp_texts()
        # text = r"This is (hello), but this is escaped \(hello), and again (hello)"
        # replacement = "WORLD"
        # idx_1, idx_2 = self.roll_two(num_candidates)
        idx_1, idx_2, idx_3 = random.sample(range(0,num_candidates), 3)
        user_id1 = candidates[idx_1]
        user_id2 = candidates[idx_2]
        user_id3 = candidates[idx_3]

        text = text.replace(r"\n", "\n")

        nickname1 = user_id1
        if event.get_platform_name() == "aiocqhttp":
            assert isinstance(event, AiocqhttpMessageEvent)
            stranger_info = await event.bot.api.call_action(
                'get_stranger_info', user_id=user_id1
            )
            nickname1 = stranger_info.get("nick", nickname1)

        nickname2 = user_id2
        if event.get_platform_name() == "aiocqhttp":
            assert isinstance(event, AiocqhttpMessageEvent)
            stranger_info = await event.bot.api.call_action(
                'get_stranger_info', user_id=user_id2
            )
            nickname2 = stranger_info.get("nick", nickname2)
        
        nickname3 = user_id3
        if event.get_platform_name() == "aiocqhttp":
            assert isinstance(event, AiocqhttpMessageEvent)
            stranger_info = await event.bot.api.call_action(
                'get_stranger_info', user_id=user_id3
            )
            nickname3 = stranger_info.get("nick", nickname3)

        # reply += f"idx: {idx_1}, {idx_2}\n"
        # reply += f"id: {user_id1}, {user_id2}\n"
        # reply += f"nick: {nickname1}, {nickname2}\n"

        text = re.sub(r'(?<!\\)\(群友1\)', nickname1, text)
        text = re.sub(r'(?<!\\)\(群友2\)', nickname2, text)
        text = re.sub(r'(?<!\\)\(群友3\)', nickname3, text)
        text = re.sub(r'(?<!\\)\（群友1\）', nickname1, text)
        text = re.sub(r'(?<!\\)\（群友2\）', nickname2, text)
        text = re.sub(r'(?<!\\)\（群友3\）', nickname2, text)
        reply += text
        yield event.plain_result(reply) 

    @filter.command("jrrp")
    async def jrrp(self, event: AstrMessageEvent):
        """jin ri ren pin"""
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        expression = "1d100"
        result = self.roll_dice(expression, True)

        if not result:
            reply = f"message_str: {message_str}\n expression: {expression}\n failed to parse"
            return 
        
        reply = f"{user_name} 今天遇到了{result}根小黄瓜！"
        if result <=5: 
            reply = f"{user_name} 今天遇到了{result}根死掉的小黄瓜！^^"
        elif result > 95: 
            reply += f"{user_name} 今天遇到了{result}根开心的小黄瓜"
        
        yield event.plain_result(reply) 

    @filter.command("rh")
    async def rh(self, event: AstrMessageEvent):
        """roll hidden"""
        user_name = event.get_sender_name()
        sender_id = event.get_sender_id()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        
        group_id = event.get_group_id()
        logger.info(message_chain)
        if group_id:
            reply = f"<{user_name}>于{group_id}的暗骰结果:\n"
        else:
            reply = f"<{user_name}>的暗骰结果:\n"

        # expression = self.parse_message(message_str)
        result, dice_reply = self.roll_dice_get_reply(message_str, "rh")
        reply += dice_reply

        client = event.bot 
        payloads = {
            "user_id": sender_id,
            "message": [
                {
                    "type": "text",
                    "data": {
                        "text": reply
                    }
                }
            ]
        }

        ret = await client.api.call_action("send_private_msg", **payloads)
        logger.info(f"Dice! rh: send_private_msg returned: {ret}")

    @filter.command("ra")
    async def ra(self, event: AstrMessageEvent):
        """roll access"""
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        message = self.parse_message(message_str, command="ra")

        messages = message.split(' ', 2) + ["", ""]
        
        target_str = messages[0]
        success = False
        if target_str.isnumeric():
            target = int(target_str)
        else:
            # TODO read stuff from character card
            target = 50
        
        dice = 100
        result = self.roll_dice(dice, True)
        reply = f"<{user_name}>的检定结果\n"
        failll = False
        for failll_key in failll_keys:
            if failll_key in messages:
                failll = True
                # message.replace(failll_key, "")
        if failll:
            result = 99
            explanation = ":)"

        reply += "由于 " + message + ": \n"
        reply += f"d{dice}={result}/{target} "
        if result:
            success = result < target
            # reply = f"success: {success}\nmessage_str: {message_str}\n result: {result}\nExplanation: {explanation}"
            if failll:
                reply += "大失败 :)"
            elif result > target:
                if result > 95:
                    reply += "大失败"
                else:
                    reply += "失败"
            else:
                if result <= 5:
                    eply += "大成功"
                elif result < target/5:
                    reply += "极限成功"
                elif result < target/2:
                    reply += "困难成功"
                else:
                    reply += "成功"
            
        else:
            reply = f"message_str: {message_str}\n failed to parse"
        
        yield event.plain_result(reply)
    
    def draw_from_deck(self, deck_name):
        deck = self.decks[deck_name]
        size = len(deck)
        if size==0:
            reply = "deck empty!"
            return reply
        result = self.roll_dice(size, True)
        if not result:
            reply = f"failed to roll: {size}"
            return reply
        drew = deck[result-1]
        return drew
    def draw_from_cp_texts(self):
        size = len(self.cp_texts)
        if size==0:
            reply = "no cp texts!"
            return reply
        result = self.roll_dice(size, True)
        if not result:
            reply = f"failed to roll: {size}"
            return reply
        drew = self.cp_texts[result-1]
        return drew
        

    @filter.command("draw")
    async def draw(self, event: AstrMessageEvent):
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
       
        message = self.parse_message(message_str, command="draw")
        if not message or message=="":
            reply = "please specify deck!"
            yield event.plain_result(reply)
            return
        
        # yield event.plain_result(message)
        tokens = message.strip().split(' ', 2)
        deck_name = tokens[0]
        if not deck_name in self.decks:
            reply = f"deck {deck_name} not exist!"
            yield event.plain_result(reply)
            return 
        
        reply = self.draw_from_deck(deck_name)
        reply.replace("\\n", "\n")
        yield event.plain_result(reply)

    def log_new(self, group_id, log_name=None):
        current_time = datetime.datetime.now()
        log_id = str(uuid.uuid4())
        group_log_path = self.get_group_log_path(group_id, log_id)
        write_txt(group_log_path, current_time.strftime("%c"))
        self.add_group_log_index(group_id, log_id, log_name)
        self.set_group_current_log(group_id, log_id)
        reply = "log created: " + log_id 
        return reply
    def log_end(self, group_id, log_id):
        current_time = datetime.datetime.now()
        group_log_path = self.get_group_log_path(group_id, log_id)
        if not os.path.exists(group_log_path):
            reply = "log not found"
            return reply
        append_txt(group_log_path, "\n\n" + current_time.strftime("%c"))
        # self.add_group_log_index(group_id, log_id, log_name)
        self.set_group_current_log(group_id, None)
        # reply = "log created: " + log_id 
        # TODO send log to user
        return reply
    def log_preview(self, group_id, log_id, log_name=None, num_lines=10):
        group_log_path = self.get_group_log_path(group_id, log_id)
        if not os.path.exists(group_log_path):
            reply = f"LOG {log_id} NOT FOUND"
            return reply
        preview = read_last_n_lines(group_log_path, num_lines)
        log_name = log_name if log_name else log_id
        reply = f"LAST {num_lines} LINES of {log_name}:\n-\n" + '\n'.join(preview)
        return reply

    @filter.command("log")
    async def log(self, event: AstrMessageEvent):
        message_str = event.message_str
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.debug(message_chain)
        message = self.parse_message(message_str, command="log")
        group_id = event.get_group_id()
        if not group_id or group_id == "":
            reply = "must use in a group"
            yield event.plain_result(reply)
            return
        tokens = message.strip().split(' ', 2) + ["", "", ""]
        if tokens[0] == "new":
            logger.debug("log new")
            reply = self.log_new(group_id)
        elif tokens[0] == "on":
            logger.debug("log on")
            reply = "log on"
        elif tokens[0] == "off":
            logger.debug("log off")
            reply = "log off"
        elif tokens[0] == "end":
            logger.debug("log end")
            log_id = self.find_group_current_log_id(group_id)
            reply = self.log_end(group_id, log_id)
            reply = "log end"
        elif tokens[0] == "view":
            logger.debug("log view")
            log_id = self.find_group_current_log_id(group_id)
            # yield event.plain_result(f"CURRENT LOG: {log_id}")
            logger.debug(f"CURRENT LOG: {log_id}")
            reply = self.log_preview(group_id, log_id)
            
        else:
            reply = "invalid command"
        yield event.plain_result(reply)

    @filter.command("pc")
    async def pc(self, event: AstrMessageEvent):
        """character card"""
        # yield event.plain_result("HERE")
        user_name = event.get_sender_name()
        user_id = event.get_sender_id()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.debug(message_chain)

        message = self.parse_message(message_str, command="pc")

        # yield event.plain_result(message)

        if not message or message=="":
            reply = "Character name is empty!"
            yield event.plain_result(reply)
            return
        
        # yield event.plain_result(message)
        tokens = message.strip().split(' ', 2)

        num = len(tokens)
        # yield event.plain_result(f"tokens {num}")

        command = None
        if tokens[0] in PC_COMMANDS:
            command = tokens[0]
            char_name = tokens[1] if len(tokens)>1 else None
            attrs = tokens[2] if len(tokens)>2 else None
        else:
            command = "new"
            char_name = tokens[0]
            attrs = tokens[1] if len(tokens)>1 else None
        
        logger.info(command)
        logger.info(char_name)
        logger.info(attrs)

        # yield event.plain_result(f"command {command} char_name {char_name}")
        ## "new", "tag", "show", "nn", "cpy", "del", "list", "clear"]
        if command == "new":
            reply = self.pc_new(user_id, char_name, attrs)
        elif command == "show":
            reply = self.pc_show(user_id, char_name)
        elif command == "tag":
            reply = self.pc_tag(user_id, char_name)
        else:
            reply = "Unknown command\n"
   
        yield event.plain_result(reply)

    # @filter.on_decorating_result()
    # async def on_decorating_result(self, event: AstrMessageEvent):
    #     result = event.get_result()
    #     message_str = result.get_plain_text()
    #     if self.IsError_filter:
    #         if '请求失败' in message_str:
    #             logger.info(message_str)
    #             event.stop_event() # 停止回复
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        current_time = datetime.datetime.now()

        group_id = event.get_group_id()
        current_log_path = self.find_group_current_logging_path(group_id)
        if not current_log_path:
            return
        user_name = event.get_sender_name()
        sender_id = event.get_sender_id()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        
        log = current_time.strftime("%c") + f" {user_name} ({sender_id}):\n"
        log = log + message_str + "\n"
        append_txt(current_log_path, log)


    ##########################################
    def get_user_folder(self, user_id):
        user_folder = os.path.join(USER_DIR, str(user_id))
        return user_folder
    def get_group_folder(self, group_id):
        group_folder = os.path.join(GROUP_DIR, str(group_id))
        return group_folder
    def get_group_log_path(self, group_id, log_id):
        group_folder = self.get_group_folder(group_id)
        log_root = os.path.join(group_folder, "LOGS")
        log_folder = os.path.join(log_root, str(log_id))
        return log_folder
    def get_group_cp_candidates_path(self, group_id):
        group_folder = self.get_group_folder(group_id)
        cp_candidates_file = os.path.join(group_folder, "ROLL_CP.txt")
        return cp_candidates_file
    def get_group_cp_candidates(self, group_id):
        cp_candidates_file = self.get_group_cp_candidates_path(group_id)
        if not os.path.exists(cp_candidates_file):
            return []
        cp_candidates = read_lines(cp_candidates_file)
        return cp_candidates
    def add_group_cp_candidate(self, group_id, user_id):
        cp_candidates_file = self.get_group_cp_candidates_path(group_id)
        new_line = str(user_id) + "\n"
        append_txt(cp_candidates_file, new_line)
    def get_user_log_path(self, user_id, log_id):
        user_folder = self.get_user_folder(user_id)
        log_root = os.path.join(user_folder, "LOGS")
        log_folder = os.path.join(log_root, str(log_id))
        return log_folder

    def get_user_characters(self, user_id):
        user_folder = self.get_user_folder(user_id)
        characters = []

        if not os.path.exists(user_folder):
            return characters

        for filename in os.listdir(user_folder):
            if filename.endswith(".json"):
                characters.append(filename.removesuffix(".json"))

        return characters
    
    def find_user_character_path(self, user_id, char_name):
        user_folder = self.get_user_folder(user_id)
        return os.path.join(user_folder, char_name + ".json")

    def find_user_character(self, user_id, char_name):
        character_path = self.find_user_character_path(user_id, char_name)
        if not character_path:
            reply = f"Dice!: character {char_name} not exist!\n"
            return None
        return read_json(character_path)
    def find_selected_name_path(self, user_id):
        user_folder = self.get_user_folder(user_id)
        return os.path.join(user_folder, "selected")
    def find_group_current_log_name_path(self, group_id):
        group_folder = self.get_group_folder(group_id)
        return os.path.join(group_folder, "current_log")
    def find_group_current_logging_path(self, group_id):
        current_log_id = self.find_group_current_log_id(group_id)
        current_log_path = self.get_group_log_path(group_id, current_log_id)
        if not os.path.exists(current_log_path):
            return None
        return current_log_path
    
    def get_group_logs_index_path(self, group_id):
        group_folder = self.get_group_folder(group_id)
        return os.path.join(group_folder, "logs_index.json")
    def find_group_logs(self, group_id):
        group_logs_index_path = self.get_group_logs_index_path(group_id)
        if not os.path.exists(group_logs_index_path):
            return {}
        return read_json(group_logs_index_path)
    def add_group_log_index(self, group_id, log_id, log_name=None):
        group_logs_index_path = self.get_group_logs_index_path(group_id)
        group_logs = self.find_group_logs(group_id)
        if log_id in group_logs:
            reply = f"log {log_id} already exist for group {group_id}"
            return reply
        group_logs[log_id] = log_name
        log_name = log_name if log_name else log_id
        write_json(group_logs_index_path, group_logs)
        return f"log {log_name} added for group {group_id}"
    def remove_group_log_from_index(self, group_id, log_id):
        group_logs_index_path = self.get_group_logs_index(group_id)
        group_logs = self.find_group_logs(group_id)
        if log_id not in group_logs:
            reply = f"log {log_id} not exist for group {group_id}"
            return reply
        log_name = group_logs.pop('key', None)
        log_name = log_name if log_name else log_id
        write_json(group_logs_index_path, group_logs)
        return f"log {log_name} removed for group {group_id}"
        
    def find_group_current_log_id(self, group_id):
        current_log_path = self.find_group_current_log_name_path(group_id)
        if not os.path.exists(current_log_path):
            return None
        log_id = read_txt(current_log_path)
        if log_id == "" or log_id == "None":
            return None
        return log_id
    def set_group_current_log(self, group_id, log_id):
        if not log_id:
            log_id = ""
        current_log_path = self.find_group_current_log_name_path(group_id)
        write_txt(current_log_path, log_id)
    
    def find_user_selected_character(self, user_id):
        selected_name_path = self.find_selected_name_path(user_id)
        if not os.path.exists(selected_name_path):
            return None
        char_name = read_txt(selected_name_path)
        if not char_name or char_name=="":
            return None
        character = self.find_user_character(user_id, char_name)
        return character
    def set_user_selected_character(self, user_id, char_name):
        selected_name_path = self.find_selected_name_path(user_id)
        if not char_name:
            char_name = ""
        write_txt(selected_name_path, char_name)
        return char_name

    def create_user_character(self, user_id, char_name):

        char_filepath = self.find_user_character_path(user_id, char_name)

        if os.path.exists(char_filepath):
            logger.error("char exists")
            reply = f"Dice!: character {char_name} exists!\n"
            return None, reply
        
        character = {"name": char_name,
                    "path": char_filepath,
                    "stats": {}}
            
        reply = f"character {char_name} created!\n"
        return character, reply

    def character_add_stats(self, character, stats_str):
        stats_str = stats_str.strip().replace(" ", ",")
        stats = stats_str.split(",")
        if not character["stats"]:
            character["stats"] = {}
        reply = "adding stats:\n"
        # Chinese chartacters: \u4e00-\u9fff
        # Hiragana: \u3040-\u309F
        # Katakana: \u30A0-\u30FF
        pattern = r"([\u4e00-\u9fff\u3040-\u309F\u30A0-\u30FFA-Za-z]+)(\d+)"
        for attr in stats:
            if ":" in attr:
                attr = attr.split(":")
                key = attr[0]
                value = attr[1]
                if value.isnumeric():
                    character["stats"][key] = value
                    reply = reply + f"{key}: {value}\n"
            else:
                matches = re.findall(pattern, attr)
                for key, value in matches:
                    character["stats"][key] = value
                    reply = reply + f"{key}: {value}\n"

            character[key] = value
        return character, reply
    
    def character_save_to_json(self, character, char_filepath=None):
        if not char_filepath:
            char_filepath = character["path"]
        logger.debug("char_filepath")
        logger.debug(char_filepath)
        logger.debug(str(os.path.dirname(char_filepath)))
        write_json(char_filepath, character)

    ####################################
    def pc_new(self, user_id, char_name, attrs=None):
        if not char_name:
            reply = "Character name is empty!"
            return reply
        char_path = self.find_user_character_path(user_id, char_name)
        if os.path.exists(char_path):
            logger.error("char exists")
            reply = f"Dice!: character {char_name} exists!\n"
            return reply
        
        character, reply = self.create_user_character(user_id, char_name)
        if not character:
            return reply
        
        if attrs:
            character, stats_reply = self.character_add_stats(character, attrs)
            reply += stats_reply
        
        max_hp = 0
        if "hp" in character["stats"]:
            max_hp = character["stats"]["hp"]
        if "max_hp" in character["stats"]:
            max_hp = character["stats"]["max_hp"]
        character["max_hp"] = max_hp

        max_san = 0
        if "san" in character["stats"]:
            max_san = character["stats"]["san"]
        if "max_san" in character["stats"]:
            max_san = character["stats"]["max_san"]
        character["max_san"] = max_san
        
        self.character_save_to_json(character)
        return reply

    def pc_show(self, user_id, char_name) :
        reply = "show character\n"
        character = self.find_user_character(user_id, char_name)
        if not character:
            reply = f"Dice!: character {char_name} not exist!\n"
            return reply
        name = character["name"]
        reply += f"NAME: {name}\n"
        max_hp = character["max_hp"]
        reply += f"MAX HP: {max_hp}\n"
        max_san = character["max_san"]
        reply += f"MAX SAN: {max_san}\n"
        reply += f"STATS:\n"
        for key in character["stats"]:
            value = character["stats"][key]
            reply += f"    {key}: {value}\n"
        return reply
    
    def pc_tag(self, user_id, char_name):
        character = self.find_user_character(user_id, char_name)
        if not character:
            reply = f"Dice!: character {char_name} not exist!\n"
            return reply
        selected_name_path = self.find_selected_name_path(user_id)
        write_txt(selected_name_path, char_name)
        reply = f"selected character: {char_name}"
        return reply

    @filter.command("pokepoke")
    async def pokepoke(self, event: AstrMessageEvent):
        '''chuochuo''' # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    def is_banned(self, event):
        sender_id = str(event.get_sender_id())
        group_id = event.message_obj.group_id if hasattr(event.message_obj, "group_id") else ""
        if sender_id in self.config.ban_user:
            logger.error(f"user {sender_id} is banned")
            return True
        if group_id in self.config.ban_group:
            logger.error(f"group {group_id} is banned")
            return True
    def is_banned_from_llm(self, event):
        sender_id = str(event.get_sender_id())
        group_id = event.message_obj.group_id if hasattr(event.message_obj, "group_id") else ""
        if sender_id in self.config.ban_llm_user:
            logger.error(f"user {sender_id} is banned from llm")
            return True
        if group_id in self.config.ban_llm_group:
            logger.error(f"group {group_id} is banned from llm")
            return True
    def ban_user(self, user_id):
        self.config.ban_user.append(str(user_id))
        self.config.save_config()
    def unban_user(self, user_id):
        self.config.ban_user.remove(str(user_id))
        self.config.save_config()
    def ban_user_from_llm(self, user_id):
        self.config.ban_llm_user.append(str(user_id))
        self.config.save_config()
    def unban_user_from_llm(self, user_id):
        self.config.ban_user.remove(str(user_id))
        self.config.ban_llm_user.remove(str(user_id))
        self.config.save_config()
    def ban_group(self, group_id):
        self.config.ban_group.append(str(group_id))
        self.config.save_config()
    def unban_group(self, group_id):
        self.config.ban_group.remove(str(group_id))
        self.config.save_config()
    def ban_group_from_llm(self, group_id):
        self.config.ban_llm_group.append(str(group_id))
        self.config.save_config()
    def unban_group_from_llm(self, group_id):
        self.config.ban_group.remove(str(group_id))
        self.config.ban_llm_ugroup.remove(str(group_id))
        self.config.save_config()

    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def handle_group_message(self, event: AstrMessageEvent):
        if self.is_banned(event):
            event.stop_event()
            # yield event.plain_result("Hello")
            return
        message_obj = event.message_obj # 获取消息对象
        message_str = message_obj.message_str # 消息文本内容
        self_id = event.get_self_id() # 机器人QQ号
        group_id = message_obj.group_id # 群号
        for command in COMMANDS:
            if message_str.startswith("." + command):
                # yield event.plain_result("command "+command)
                return
            if message_str.startswith("/"):
                # yield event.plain_result("command "+command)
                return
        # 检查消息开头是否有关键词
        if not self.config.poke:
            return
        
        if self.is_banned_from_llm(event):
            # yield event.plain_result("stop")
            event.stop_event()
            return
        
        for keyword in POKE_KEYWORDS:
            if keyword in message_str:
                # 确定戳一戳的次数 (有感叹号会触发更多戳戳)
                if re.match(rf'^{keyword}(！|!)$', message_str):
                        poke_times = random.randint(5, 10)
                else:
                    poke_times = random.randint(1, 3)

                # 提取消息中 @ 的用户
                messages = event.get_messages()
                target_user_id = next((str(seg.qq) for seg in messages if (isinstance(seg, Comp.At))), None)

                # 检查是否有 @ 的用户
                if target_user_id is None:
                    target_user_id = event.get_sender_id()
                # 检查受击人是否机器人本体
                if str(target_user_id) == str(self_id):
                    # yield event.plain_result(random.choice(self_poke_messages)) # self_poke_messages 为不能自己戳自己的话术列表
                    return
                
                # 检查是否在冷却期
                if self.cooling_down and time.time() < self.cooling_end_time:
                    # yield event.plain_result(random.choice(cooling_down_messages))
                    return
                
                # # 攻击前自嗨
                # yield event.plain_result(random.choice(received_commands_messages))

                # 发送戳一戳
                payloads = {"user_id": target_user_id, "group_id": group_id}
                for _ in range(poke_times):
                    try:
                        await event.bot.api.call_action('send_poke', **payloads)
                    except Exception as e:
                        pass

                # 进入冷却期
                self.cooling_down = True
                cooling_duration = random.randint(30, 60)
                self.cooling_end_time = time.time() + cooling_duration
                return


    @filter.event_message_type(filter.EventMessageType.ALL)
    async def getpoke(self, event: AstrMessageEvent):
        for comp in event.message_obj.message:
            if isinstance(comp, Poke):
                bot_id = event.message_obj.raw_message.get('self_id')
                sender_id = event.get_sender_id()
                group_id = event.get_group_id()
                logger.info("检测到戳一戳")
                poke_times = self.roll_dice("1d3", True)
                if comp.qq != bot_id and sender_id != bot_id:
                    logger.info(f"sender: {sender_id} bot {bot_id}")
                    payloads = {"user_id": comp.qq, "group_id": group_id}
                    try:
                        logger.info("HELLO")
                        # await event.bot.api.call_action('send_poke', **payloads)
                        logger.info("BYE")
                    except Exception as e:
                        pass
                    return
                
                message_chain = event.get_messages()
                nickname = sender_id
                if event.get_platform_name() == "aiocqhttp":
                    assert isinstance(event, AiocqhttpMessageEvent)
                    stranger_info = await event.bot.api.call_action(
                        'get_stranger_info', user_id=sender_id
                    )
                    nickname = stranger_info.get("nick", nickname)
                # yield event.plain_result(f"{nickname} 惊扰了 黄瓜精灵！") 
                bot_id = event.message_obj.raw_message.get('self_id')
                # if comp.qq != bot_id:
                #     return
                
                # 具体功能
                event.message_obj.message.insert(
                    0, Comp.At(qq=event.get_self_id(), name=event.get_self_id())
                )
                new_event = copy.copy(event)
                message_str = f"{nickname} 戳了戳你的头！"
                if event.session.message_type.name == 'GROUP_MESSAGE':
                    astrbot_config = self.context.get_config()
                    wake_prefix = astrbot_config["wake_prefix"]
                    if wake_prefix != []:
                        message_str = wake_prefix[0] + message_str
                new_event.message_obj.message.clear()
                new_event.message_obj.message.append( Plain(message_str) )
                new_event.message_obj.message_str = message_str
                new_event.message_str = message_str
                new_event.message_obj.message.insert(
                    0, At(qq=event.get_self_id(), name=event.get_self_id())
                )
                new_event.should_call_llm(True)
                self.context.get_event_queue().put_nowait(new_event)

                # logger.info("HERE")
                payloads = {"user_id": sender_id, "group_id": group_id}
                # for _ in range(poke_times):
                try:
                    logger.info("THERE")
                    await event.bot.api.call_action('send_poke', **payloads)
                    logger.info("AFTER")
                except Exception as e:
                    pass
                # return
                yield event.plain_result(f"{nickname} 惊扰了 黄瓜精灵！") 
