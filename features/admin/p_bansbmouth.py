# plugins/p_groupManager/features/admin/p_bansbmouth.py

import logging
import re
import time
from api.send import send_group_msg
from api.get import get_group_member_info
from api.set import set_group_ban
from api.set import set_group_whole_ban


logger = logging.getLogger("p_bansbmouth_manager")

def get_ban_target_id(message):
    raw_message = message.get('raw_message', '')

    # 匹配解禁指令
    if raw_message.startswith('%解禁') or raw_message.startswith('%解除禁言'):
        cq_match = re.search(r'\[CQ:at,qq=(\d+),name=.*?\]', raw_message)
        if cq_match:
            return int(cq_match.group(1)), 0  # 解禁时长为0

        command_match = re.search(r'%解禁\s*(\d+)|%解除禁言\s*(\d+)', raw_message)
        if command_match:
            ban_target_id = int(command_match.group(1) or command_match.group(2))
            return ban_target_id, 0  # 解禁时长为0

    # 匹配 CQ 码
    cq_match = re.search(r'\[CQ:at,qq=(\d+),name=.*?\]', raw_message)
    
    # 尝试从 raw_message 中查找禁言指令
    command_match = re.search(r'%禁言\s*(\d+)', raw_message)
    if command_match:
        ban_target_id = int(command_match.group(1))  # 从指令获取用户 ID
    elif cq_match:
        ban_target_id = int(cq_match.group(1))  # 从 CQ 码获取用户 ID
    else:
        logger.warning(f"[ 群管插件 ] 不合规指令: {raw_message}")
        return None, None

    # 从 message 字段获取时长
    duration = 60  # 默认为60秒
    if message.get('message'):
        last_item = message['message'][-1]  # 获取最后一个元素
        if last_item['type'] == 'text':
            # 检查最后一个元素的文本是否包含时长信息
            duration_match = re.search(r'\*([\d]+)', last_item['data']['text'])
            if duration_match:
                duration = int(duration_match.group(1)) * 60  # 转换为秒

    return ban_target_id, duration



async def on_message_admin(self, message, bot_role):
    raw_message = message.get('raw_message', '')
    group_id = message.get('group_id', '未知群ID')
    user_id = message['sender']['user_id']
    response_message = ""
    
    if raw_message.startswith('%禁言') or raw_message.startswith('%解禁') or raw_message.startswith('%解除禁言'):
        try:
            if not self.bot.is_group_admin(group_id, user_id):
                if not self.bot.is_admin(user_id):
                    logger.info("[ 群管插件 ] 拒绝非特权用户在群禁言！")
                    return

            if bot_role != 1:
                logger.info("[ 群管插件 ] 机器人不是该群群管！")
                response_message = f"{self.bot.bot_nickname}还不是本群群管(；′⌒`)"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return
        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析禁言前置条件时出现错误: {e}")
            return
        
        try:
            ban_target_id_str, duration = get_ban_target_id(message)
            logger.debug(f"[ 群管插件 ] 解析到的禁言时长为 {duration} 秒。")
        except Exception as e:
            logger.error(f"[ 群管插件 ] 执行 get_ban_target_id 时出错: {str(e)}")
            return

        if ban_target_id_str is None:
            logger.warning("[ 群管插件 ] 禁言对象 ID 获取失败！")
            return
        
        try:
            ban_target_id = int(ban_target_id_str)
        except ValueError:
            logger.warning(f"[ 群管插件 ] 禁言对象 ID `{ban_target_id_str}` 无法转换为整数！")
            return
        
        try:
            is_in_group = self.bot.is_target_in_group(ban_target_id, group_id)
            logger.debug(f"目标用户 {ban_target_id} {is_in_group} 群 {group_id} 中")

            if not is_in_group:
                logger.warning("[ 群管插件 ] 目标用户不在本群！")
                response_message = f"目标用户 {ban_target_id} 不在本群(¬_¬\")"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return
        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析禁言目标 是否为该群用户 时出现错误: {e}")

        try:
            if ban_target_id == user_id:
                logger.warning("[ 群管插件 ] 某人尝试禁言自己！")
                response_message = f"禁止自娱自乐(╬▔皿▔)╯"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return
        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析禁言目标 是否为其自己 时出现错误: {e}")
            
        try:
            if ban_target_id == self.bot.bot_id:
                logger.warning("[ 群管插件 ] 某人尝试让机器人禁言自己！")
                response_message = "坏蛋！"
                response_message1 = "大坏蛋！o(≧口≦)o"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                time.sleep(0.5)
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                time.sleep(0.5)
                send_group_msg(self.bot.base_url, group_id, response_message1, self.bot.token)
                return

        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析禁言目标 是否为其自己 时出现错误: {e}")

        try:
            is_admin = self.bot.is_group_admin(group_id, ban_target_id)
            logger.debug(f"目标用户 {ban_target_id} 是本群管理吗？返回: {is_admin}")

            if is_admin:
                logger.warning(f"[ 群管插件 ] 目标用户 {ban_target_id} 是本群管理，无法禁言。")
                response_message = f"目标用户 {ban_target_id} 是本群管理，无法禁言┑(￣Д ￣)┍"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return
        except Exception as e:
            logger.error(f"[ 群管插件 ] 分析禁言目标 是否为该群管理 时出现错误: {e}")

        try:
            # 获取管理员信息
            admin_info = get_group_member_info(self.bot.base_url, group_id, user_id, False, self.bot.token)
            if not isinstance(admin_info, dict) or admin_info.get('status') != 'ok' or admin_info.get('retcode') != 0:
                logger.error("[ 群管插件 ] 获取管理员信息失败或格式不正确")
                return

            admin_nickname = admin_info['data']['nickname']

            # 获取被踢目标信息
            target_user_info = get_group_member_info(self.bot.base_url, group_id, ban_target_id, False, self.bot.token)
            logger.debug(f"获取禁言目标信息: {target_user_info}")  # 添加此行

            if not isinstance(target_user_info, dict) or target_user_info.get('status') != 'ok' or target_user_info.get('retcode') != 0:
                logger.error("[ 群管插件 ] 获取禁言目标信息失败或格式不正确")
                return

            target_user_nickname = target_user_info['data']['nickname']
            if duration != 0:
                logger.warning(f"[ 群管插件 ][ 管理禁言事件 ] 群聊 {group_id} 管理员 {admin_nickname} ( {user_id} ) 尝试将用户 {target_user_nickname} ( {ban_target_id} ) 禁言 {duration // 60} 分钟。")
            else:
                logger.warning(f"[ 群管插件 ][ 管理禁言事件 ] 群聊 {group_id} 管理员 {admin_nickname} ( {user_id} ) 尝试解除用户 {target_user_nickname} ( {ban_target_id} ) 的禁言。")

            set_group_ban(self.bot.base_url, group_id, ban_target_id, duration, self.bot.token)
            if duration != 0:
                response_message = f"用户 {target_user_nickname} ( {ban_target_id} ) 因触犯天条，被管理禁言 {duration // 60} 分钟"
            else:
                response_message = f"用户 {target_user_nickname} ( {ban_target_id} ) 被管理解除禁言"
            send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)

        except Exception as e:
            logger.error(f"[ 群管插件 ] 获取群员信息或禁言失败: {e}")
            return

    elif raw_message.startswith('%全体禁言') or raw_message.startswith('%全体解禁') or raw_message.startswith('%取消全体禁言'):
        try:
            if not self.bot.is_group_admin(group_id, user_id):
                if not self.bot.is_admin(user_id):
                    logger.info("[ 群管插件 ] 拒绝非特权用户在群禁言！")
                    return

            if bot_role != 1:
                logger.info("[ 群管插件 ] 机器人不是该群群管！")
                response_message = f"{self.bot.bot_nickname}还不是本群群管(；′⌒`)"
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
                return

            # 全体禁言或解禁的逻辑
            if raw_message.startswith('%全体禁言'):
                logger.warning(f"[ 群管插件 ][ 管理全体禁言事件 ] 群聊 {group_id} 管理员 {user_id} 尝试全体禁言。")
                set_group_whole_ban(self.bot.base_url, group_id, True, self.bot.token)
                response_message = f"已开启全体禁言。"
                
            elif raw_message.startswith('%取消全体禁言') or raw_message.startswith('%全体解禁'):
                logger.warning(f"[ 群管插件 ][ 管理全体解禁事件 ] 群聊 {group_id} 管理员 {user_id} 尝试解除全体禁言。")
                set_group_whole_ban(self.bot.base_url, group_id, False, self.bot.token)
                response_message = "全体禁言已解除。"

            send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)

        except Exception as e:
            logger.error(f"[ 群管插件 ] 执行全体禁言或解禁时出错: {e}")
            return

    else:
        pass
