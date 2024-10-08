# plugins/p_groupManager/features/p_userInfoManager.py
import logging
from api.get import get_group_member_info
from api.send import send_group_msg
import time

logger = logging.getLogger("p_user_info_manager")

async def on_message(self, message, bot_role):
    raw_message = message.get('raw_message', '')
    group_id = message.get('group_id', '')
    user_id = message['sender']['user_id']

    # 检查消息是否为 "%我的信息"
    if raw_message == '%我的信息':

        try:
            # 获取用户信息
            user_info = get_group_member_info(self.bot.base_url, group_id, user_id, False, self.bot.token)
            
            logger.debug(f"[ 群管插件 ] 获取用户: {user_id} 信息: \n{user_info}")

            if user_info['status'] == 'ok':
                logger.info(f"获取用户信息成功")
                data = user_info['data']
                nickname = data['nickname']
                title = data.get('title', '无')  # 默认头衔为“无”
                card = data.get('card', '无')  # 如果没有设置群昵称则用 "无"
                join_time = data['join_time']
                join_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(join_time))  # 格式化入群时间

                # 计算入群总时长
                current_time = time.time()
                duration = int(current_time - join_time)

                # 计算年、月、天、小时、分钟、秒
                years = duration // 31536000  # 1年 = 365天
                months = (duration % 31536000) // 2592000  # 1月 = 30天
                days = (duration % 2592000) // 86400  # 1天 = 86400秒
                hours = (duration % 86400) // 3600  # 1小时 = 3600秒
                minutes = (duration % 3600) // 60  # 1分钟 = 60秒
                seconds = duration % 60  # 剩余秒数

                # 创建时长显示字符串
                duration_parts = []
                if years > 0:
                    duration_parts.append(f"{years}年")
                if months > 0:
                    duration_parts.append(f"{months}月")
                if days > 0:
                    duration_parts.append(f"{days}天")
                if hours > 0:
                    duration_parts.append(f"{hours}小时")
                if minutes > 0:
                    duration_parts.append(f"{minutes}分钟")
                if seconds > 0:
                    duration_parts.append(f"{seconds}秒")

                duration_display = " ".join(duration_parts) or "刚加入"

                # 映射角色为中文
                role_mapping = {
                    'owner': '群主',
                    'admin': '管理员',
                    'member': '普通群员'
                }
                role = role_mapping.get(data['role'], '其他')

                # 格式化消息
                response_message = (
                    f"[CQ:at,qq={user_id},name={card}] \n你的本群信息如下:\n\n" 
                    f"昵称: {nickname}\n"
                )

                if card:
                    response_message += f"群名片: {card}\n"
                if title:
                    response_message += f"头衔: {title}\n"

                response_message += (
                    f"角色: {role}\n"
                    f"入群时间: {join_time_formatted}\n"
                    f"入群总时长: {duration_display}"
                )

                # 发送消息
                logger.info("[ 群管插件 ] 尝试发送消息:\n %s\n", response_message)
                send_group_msg(self.bot.base_url, group_id, response_message, self.bot.token)
            else:
                logger.error(f"获取用户信息失败: {user_info['message']}")

        except Exception as e:
            logger.error(f"[ 群管插件 ] p_user_info_manager 处理消息时出错: {str(e)}")
