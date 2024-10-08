# plugins/p_groupManager/main.py
from plugin_base import Plugin
import logging
import os
import importlib.util

logger = logging.getLogger("p_groupManager")

class P_groupmanagerPlugin(Plugin):
    def __init__(self, bot):
        self.bot = bot
        self.ensure_features_dir()
        self.features = self.load_features()

    def ensure_features_dir(self):
        features_path = os.path.join(os.path.dirname(__file__), 'features')
        admin_path = os.path.join(features_path, 'admin')

        os.makedirs(features_path, exist_ok=True)
        os.makedirs(admin_path, exist_ok=True)
        logger.debug("确保功能文件夹存在: %s", features_path)

    def load_features(self):
        features = {}
        # 加载公共插件
        features.update(self._load_plugins_from_directory(os.path.join(os.path.dirname(__file__), 'features')))
        # 加载特权插件
        features.update(self._load_plugins_from_directory(os.path.join(os.path.dirname(__file__), 'features/admin')))
        return features

    def _load_plugins_from_directory(self, directory):
        features = {}
        for feature_file in os.listdir(directory):
            if feature_file.endswith('.py') and feature_file.startswith('p_'):
                feature_name = feature_file[:-3]  # 去掉.py后缀
                feature_path = os.path.join(directory, feature_file)
                logger.debug("正在加载群管功能: %s", feature_name)

                try:
                    spec = importlib.util.spec_from_file_location(feature_name, feature_path)
                    feature_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(feature_module)

                    # 保存特性插件模块
                    features[feature_name] = feature_module
                    logger.info(f"加载群管功能成功: {feature_name}")
                except Exception as e:
                    logger.error(f"加载群管功能失败: {feature_name}, 错误: {str(e)}")
        return features

    async def on_message(self, message):
        message_type = message.get('message_type', '未知类型')
        raw_message = message.get('raw_message', '')
        if message_type == 'private':
            return
        
        elif message_type == 'group' and raw_message.startswith('%'):
            bot_role = 0  # 默认机器人不是群管
            group_id = message.get('group_id', '未知群ID')

            if self.bot.is_group_admin(group_id, self.bot.bot_id):
                bot_role = 1  # 机器人是群管

            sender = message.get('sender', {})
            user_id = sender.get('user_id', '未知用户')
            logger.info(f"[ 群管插件 ] 收到群消息: {raw_message} 来自用户: {user_id} 在群: {group_id}")
            if bot_role:
                logger.info("[ 群管插件 ] 机器人是该群管理")
            
            logger.info("[ 群管插件 ] 群管插件分发消息 ")

            if not self.bot.is_group_admin(group_id, user_id):
                if self.bot.is_admin(user_id):
                    # 消息分发给 admin 插件和公共插件
                    await self.dispatch_to_plugins(message, bot_role, admin=True)
                    await self.dispatch_to_plugins(message, bot_role)
                else:
                    # 消息仅分发给公共插件
                    await self.dispatch_to_plugins(message, bot_role)
            else:
                # 群管处理逻辑
                await self.dispatch_to_plugins(message, bot_role, admin=True)
                await self.dispatch_to_plugins(message, bot_role)

        else:
            return

    async def dispatch_to_plugins(self, message, bot_role, admin=False):
        for feature_name, feature_module in self.features.items():
            try:
                if admin and hasattr(feature_module, 'on_message_admin'):
                    await feature_module.on_message_admin(self, message, bot_role)
                elif not admin and hasattr(feature_module, 'on_message'):
                    await feature_module.on_message(self, message, bot_role)
            except Exception as e:
                logger.error(f"[ 群管插件 ] 插件 {feature_name} 处理消息时出错: {str(e)}")
