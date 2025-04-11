from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

import random
import re
import json
import os

import rolldice

@register("Dice!", "Lacki", "一个简单的 Hello World 插件", "0.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
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
        expression = message_str.removeprefix(command)
        expression = expression.replace("x", "*").replace("X", "*")
        expression = expression.strip().lower()
        return expression
    
    @filter.command("rd")
    async def roll_dice(self, event: AstrMessageEvent):
        """roll dice"""
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        expression = self.parse_message(message_str)
        
        if not expression or expression=="":
            expression="1d100"
        elif expression.isnumeric():
            expression = "d" + expression
        
        try:
            result, explanation = rolldice.roll_dice(expression)
            logger.info(f"Result: {result}")
            logger.info(f"Explanation: {explanation}")
        except:
            result = None
            logger.error(f"Dice! Error: failed to parse: {expression}")

        if result:
            yield event.plain_result(f"message_str: {message_str}\n result: {result}\nExplanation: {explanation}") 
        else:
            yield event.plain_result(f"message_str: {message_str}\n expression: {expression}\n failed to parse") 



