# plugins/p_groupManager/features/admin/p_kicksb.py

import logging
import re
import time
from api.send import send_group_msg
from api.get import get_group_member_info
from api.set import set_group_kick

logger = logging.getLogger("p_privileged_manager")

def get_kick_target_id(raw_message):
    # 匹配 CQ 码
    cq_match = re.search(r'\[CQ:at,qq=(\d+),name=.*?\]', raw_message)
    if cq_match:
        return int(cq_match.group(1))  # 转换为整数
    
    command_match = re.search(r'%踢(?:人|出)\s*(\d+)', raw_message)
    if command_match:
        return int(command_match.group(1))  # 转换为整数

    logger.warning(f"[ 群管插件 ] 不合规指令: {raw_message}")
    return None

async def on_message_admin(self, message, bot_role):
    raw_message = message.get('raw_message', '')
    group_id = message.get('group_id', '未知群ID')
    user_id = message['sender']['user_id']
    response_message = ""
    
    if raw_message.startswith('%踢人') or raw_message.startswith('%踢出'):
        
        try:
            if not self.bot.is_group_admin(group_id, user_id):
                if not self.bot.is_admin(user_id):
                    logger.info("[ 群管插件 ] 拒绝非特权用户在群踢人！")
                    return

            if bot_role != 1:
                logger.info("[ 群管插件 ] 机器人不是该群群管！")
                response_message = f"{self.bot.bot_nickname}还不是本群群管(；′⌒`)"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return
        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析踢人前置条件时出现错误: {e}")
            return
        
        try:
            kick_target_id_str = get_kick_target_id(raw_message)
        except Exception as e:
            logger.error(f"[ 群管插件 ] 执行 get_kick_target_id 时出错: {str(e)}")
            return

        if kick_target_id_str is None:
            logger.warning("[ 群管插件 ] 踢出对象 ID 获取失败！")
            return
        
        try:
            kick_target_id = int(kick_target_id_str)
        except ValueError:
            logger.warning(f"[ 群管插件 ] 踢出对象 ID `{kick_target_id_str}` 无法转换为整数！")
            return
        
        try:
            is_in_group = self.bot.is_target_in_group(kick_target_id, group_id)
            logger.debug(f"目标用户 {kick_target_id} {is_in_group} 群 {group_id} 中")

            if not is_in_group:
                logger.warning("[ 群管插件 ] 目标用户不在本群！")
                response_message = f"目标用户 {kick_target_id} 不在本群(¬_¬\")"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return
        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析踢出目标 是否为该群用户 时出现错误: {e}")

        try:
            if kick_target_id == user_id:
                logger.warning("[ 群管插件 ] 某人尝试踢出自己！")
                response_message = f"禁止自娱自乐(╬▔皿▔)╯"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return
        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析踢出目标 是否为其自己 时出现错误: {e}")
            
        try:
            if kick_target_id == self.bot.bot_id:
                logger.warning("[ 群管插件 ] 某人尝试让机器人踢出自己！")
                response_message = "坏蛋！"
                response_message1 = "大坏蛋！o(≧口≦)o"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                time.sleep(0.5)
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                time.sleep(0.5)
                send_group_msg(self.bot.base_url, group_id, response_message1, self.bot.token)
                return

        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析踢出目标 是否为其自己 时出现错误: {e}")

        try:
            is_admin = self.bot.is_group_admin(group_id, kick_target_id)
            logger.debug(f"目标用户 {kick_target_id} 是本群管理吗？返回: {is_admin}")

            if is_admin:
                logger.warning(f"[ 群管插件 ] 目标用户 {kick_target_id} 是本群管理，无法踢出。")
                response_message = f"目标用户 {kick_target_id} 是本群管理，无法踢出┑(￣Д ￣)┍"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return
        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析踢出目标 是否为该群管理 时出现错误: {e}")

        try:
            # 获取管理员信息
            admin_info = get_group_member_info(self.bot.base_url, group_id, user_id, False, self.bot.token)
            if not isinstance(admin_info, dict) or admin_info.get('status') != 'ok' or admin_info.get('retcode') != 0:
                logger.error("[ 群管插件 ] 获取管理员信息失败或格式不正确")
                return

            admin_nickname = admin_info['data']['nickname']

            # 获取被踢目标信息
            target_user_info = get_group_member_info(self.bot.base_url, group_id, kick_target_id, False, self.bot.token)
            logger.debug(f"获取被踢目标信息: {target_user_info}")  # 添加此行

            if not isinstance(target_user_info, dict) or target_user_info.get('status') != 'ok' or target_user_info.get('retcode') != 0:
                logger.error("[ 群管插件 ] 获取被踢目标信息失败或格式不正确")
                return

            target_user_nickname = target_user_info['data']['nickname']

            logger.warning(f"[ 群管插件 ][ 管理踢人事件 ] 管理员 {admin_nickname} ( {user_id} ) 尝试将用户 {target_user_nickname} ( {kick_target_id} ) 踢出群聊 {group_id}。")

            set_group_kick(self.bot.base_url, group_id, kick_target_id, False, self.bot.token)

            response_message = f"用户 {target_user_nickname} ( {kick_target_id} ) 因触犯天条，被管理踢出"
            send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)

        except Exception as e:
            logger.error(f"[ 群管插件 ] 获取群员信息或踢人失败: {e}")
            return

    else:
        pass
