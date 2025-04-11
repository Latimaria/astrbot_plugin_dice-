from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

import random
import re
import json
import os

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
        expression = message_str.removeprefix(command + ' ')
        expression = expression.replace("x", "*").replace("X", "*")
        return self.parse_expression(expression)
    
    def parse_expression(self, expression, event: AstrMessageEvent): # 1d100 * 2 + 3

        # pattern = re.compile(r"(?:(\d+)d(\d+))([*/+-]\d+)*")
        pattern = re.compile(r"\((\d*d\d+)\)([*/+-]\d+)*")
        matches = pattern.findall(expression)
        if not matches:
            logger.info(f"Dice! not able to parse expression: {expression}")
            yield event.plain_result(f"unable to parse expression: {expression}\n")
            return None

        # match_repeat = re.match(r"(\d+)?#(.+)", expression)
        # roll_times = 1
        # bonus_dice = 0
        # penalty_dice = 0

        result = f"expression: {expression}\n"
        for match in matches:
            result = result + f"match: {match}\n"
            
        yield event.plain_result(result)

        return None
    
        if match_repeat:
            roll_times = int(match_repeat.group(1)) if match_repeat.group(1) else 1
            expression = match_repeat.group(2)

            if expression == "p":
                penalty_dice = 1
                expression = "1d100"
            elif expression == "b":
                bonus_dice = 1
                expression = "1d100"

        results = []

        for _ in range(roll_times):
            parts = re.split(r"([+\-*])", expression)
            total = None 
            part_results = []
            calculation_expression = ""

            for i in range(0, len(parts), 2):
                expr = parts[i].strip()
                operator = parts[i - 1] if i > 0 else "+"

                if expr.isdigit():
                    subtotal = int(expr)
                    rolls = [subtotal]
                else:
                    match = re.match(r"(\d*)d(\d+)(k\d+)?([+\-*]\d+)?", expr)
                    if not match:
                        return None, f"格式错误 `{expr}`"

                    dice_count = int(match.group(1)) if match.group(1) else 1
                    dice_faces = int(match.group(2))
                    keep_highest = int(match.group(3)[1:]) if match.group(3) else dice_count
                    modifier = match.group(4)

                    if not (1 <= dice_count <= 100 and 1 <= dice_faces <= 1000):
                        return None, "骰子个数范围 1-100，面数范围 1-1000，否则非法！"

                    rolls = self._roll_dice(dice_count, dice_faces)
                    sorted_rolls = sorted(rolls, reverse=True)
                    selected_rolls = sorted_rolls[:keep_highest]

                    subtotal = sum(selected_rolls)

                    if modifier:
                        try:
                            subtotal = eval(f"{subtotal}{modifier}")
                        except:
                            return None, f"修正值 `{modifier}` 无效！"

                if total is None:
                    total = subtotal
                    calculation_expression = f"{subtotal}"
                else:
                    calculation_expression += f" {operator} {subtotal}"
                    if operator == "+":
                        total += subtotal
                    elif operator == "-":
                        total -= subtotal
                    elif operator == "*":
                        total *= subtotal
                if i == 0:
                    part_results.append(f"[{' + '.join(map(str, rolls))}]")
                else:
                    part_results.append(f" {operator} [{' + '.join(map(str, rolls))}]")

            if bonus_dice > 0 or penalty_dice > 0:
                base_roll = random.randint(1, 100)
                final_roll = self._roll_coc_bonus_penalty(base_roll, bonus_dice, penalty_dice)
                results.append(f"🎲 [**{final_roll}**] (原始: {base_roll})")
            else:
                results.append(f"🎲 {' '.join(part_results)} = {total}")

        return total, "\n".join(results)

    @filter.command("rd")
    async def handle_roll_dice(self, event: AstrMessageEvent):
        """roll dice"""
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        # yield event.plain_result(f"user_name: {user_name}, message_str: {message_str}") # 发送一条纯文本消息

        self.parse_expression(message_str, event)

