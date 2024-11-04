# groupManager-plugin

`groupManager-plugin` 项目是 DreamSu Bot 的一个简易群管插件。插件内功能分为两档权限：

1. 群主、管理员、账号主人
2. 普通成员

## 群管功能指令

- `%踢人 用户ID`
- `%踢人 @某人`
- `%禁言 用户ID*分钟数`
- `%禁言 @某人*分钟数`
- `%解禁 用户ID`
- `%解禁 @某人`
- `%全体禁言`
- `%全体解禁`

## 普通功能指令

- `%我的信息`

## 部署方式

在终端中执行以下命令：

```bash
# 切换到 DreamSu Bot框架项目目录
cd DreamSu

# 克隆插件到指定目录
git clone https://github.com/YeiJ/groupManager-plugin.git plugins/p_groupManager/

```

启动项目即可。
