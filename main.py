from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig

import random
import re
import json
import os
import uuid

import rolldice

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) 
DATA_DIR = os.path.join(ROOT_DIR, "data") 
PC_COMMANDS = ["new", "tag", "show", "nn", "cpy", "del", "list", "clear"]
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
@register("Dice!", "Lacki", "一个简单的 Hello World 插件", "0.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        logger.info("decks:" + str(self.config.decks))
        self.decks = {}
        self.load_decks()

    def load_decks(self):
        logger.info("loading decks")
        if not self.config.decks:
            logger.info("NO decks")
            return
        for deck_str in self.config.decks:
            logger.info("deck: "+ deck_str)
            deck = extract_outer_braces(deck_str)
            if len(deck) < 1:
                logger.info("invalid deck:\n "+ deck_str)
                continue
            deck_name = deck[0]
            deck = deck[1:] if len(deck)>1 else []
            if deck_name in self.decks and self.decks[deck_name] and self.decks[deck_name]!=[]:
                self.decks[deck_name] += deck
            else:
                self.decks[deck_name] = deck
            

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


    def roll_dice(self, expression):
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

        return result, explanation 

    @filter.command("rd")
    async def rd(self, event: AstrMessageEvent):
        """roll dice"""
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        expression = self.parse_message(message_str)
        result, explanation = self.roll_dice(expression)

        if result:
            reply = f"message_str: {message_str}\n result: {result}\nExplanation: {explanation}"
        else:
            reply = f"message_str: {message_str}\n expression: {expression}\n failed to parse"
        
        yield event.plain_result(reply) 

    @filter.command("jrrp")
    async def jrrp(self, event: AstrMessageEvent):
        """jin ri ren pin"""
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        expression = "1d100"
        result, explanation = self.roll_dice(expression)

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

        expression = self.parse_message(message_str)
        result, explanation = self.roll_dice(expression)

        if result:
            reply = f"rh from group {group_id}:\n message_str: {message_str}\n result: {result}\nExplanation: {explanation}"
        else:
            reply = f"rh from group {group_id}:\nmessage_str: {message_str}\n expression: {expression}\n failed to parse"
        
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

        messages = message.split(' ')
        
        target_str = messages[0]
        success = False
        if target_str.isnumeric():
            target = int(target_str)
        else:
            # TODO read stuff from character card
            target = 50
        
        result, explanation = self.roll_dice(100)
            
        if result:
            success = result < target
            reply = f"success: {success}\nmessage_str: {message_str}\n result: {result}\nExplanation: {explanation}"
        else:
            reply = f"message_str: {message_str}\n failed to parse"
        
        yield event.plain_result(reply)
    
    def draw_from_deck(self, deck_name):
        deck = self.decks[deck_name]
        size = len(deck)
        if size==0:
            reply = "deck empty!"
            return reply
        result, explanation = self.roll_dice(size)
        if not result:
            reply = f"failed to roll: {size}"
            return reply
        drew = deck[result-1]
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




    ##########################################
    def get_user_folder(self, user_id):
        user_folder = os.path.join(DATA_DIR, str(user_id))
        return user_folder

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
        with open(character_path, "r", encoding="utf-8") as f:
            character = json.load(f)
        return character

    def find_selected_name_path(self, user_id):
        user_folder = self.get_user_folder(user_id)
        return os.path.join(user_folder, "selected")
    
    def find_user_selected_character(self, user_id, char_name):
        user_folder = self.get_user_folder(user_id)
        selected_name_path = os.path.join(user_folder, "selected")
        if not os.path.exists(selected_name_path):
            return None
        with open(selected_name_path, "r", encoding="utf-8") as f:
            char_name = f.read().strip()
        character = self.find_user_character(user_id, char_name)
        return character

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
        create_parents(char_filepath)
        logger.debug(str(os.path.dirname(char_filepath)))
        with open(char_filepath, "w", encoding="utf-8") as f:
            json.dump(character, f, ensure_ascii=False)

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
        create_parents(selected_name_path)
        with open(selected_name_path, "w", encoding="utf-8") as f:
            f.write(char_name)
        reply = f"selected character: {char_name}"
        return reply

