from nonebot import on_command, CommandSession, scheduler
from .Object import Room
import config
import re

CREATE_USAGE = """请将如下格式填写完整并发送
========================
格式：/开门 岛密码|备注|[最大登岛人数(可选，默认""" + str(config.DEFAULT_CAPACITY) + """人)]
示例1：/开门 GTX98|大头菜价格 605
示例2：/开门 GTX98|大头菜价格 605|4"""


@on_command('create', aliases=('open', '开房', '开门', '开启'), only_to_me=True)
async def create(session: CommandSession):
    room = Room()
    user_id = session.event['user_id']
    if await room.check_group_member(user_id) is None:
        return
    for key, item in room.room.items():
        if user_id == item['user']:
            await session.finish(f'你已有岛开启中，岛ID为：{key}，如需更新岛密码请使用 /重开 命令，如需关闭岛请使用 /关门 命令')
    details = session.get('details', prompt=CREATE_USAGE)
    format_details = await get_details(details)
    if format_details is not None:
        if format_details[2]:
            room_id = room.open(format_details[0], format_details[1], None, config.GROUP_ID, session.event['user_id'],
                                session.event["sender"]['nickname'],
                                int(format_details[2]))
        else:
            room_id = room.open(format_details[0], format_details[1], None, config.GROUP_ID, session.event['user_id'],
                                session.event["sender"]['nickname'])
        await session.send(f'发布成功\n岛ID为：{room_id}')
        message = room.room_to_string(room.room[str(room_id)], False)
        await session.bot.send_msg(message_type="group", group_id=config.GROUP_ID,
                                   message=f'[CQ:at,qq={user_id}]创建了新房间\n{message}')
        for sub in room.subscribe:
            await session.bot.send_msg(message_type="private", user_id=sub,
                                       message=f'新房间\n{message}')
    if format_details is None:
        await session.finish('格式错误')


@create.args_parser
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if session.is_first_run:
        if stripped_arg:
            session.state['details'] = stripped_arg
        return
    if not stripped_arg:
        session.pause('不能输入空值，请重新输入')
    session.state[session.current_key] = stripped_arg


@on_command('备注', aliases=('修改备注', '更新备注', 'remake'), only_to_me=True)
async def edit_remake(session: CommandSession):
    room = Room()
    user_id = session.event['user_id']
    if await room.check_group_member(user_id) is None:
        return
    remake = session.current_arg_text.strip()
    room_list = room.room.copy()
    remake_len = len(remake)
    if remake_len == 0 and remake_len <= 100:
        await session.finish(f"备注不能为空或字符长度超过100")
    for room_id, item in room_list.items():
        if user_id == item['user']:
            item['remake'] = remake
            room.room[room_id] = item
            member_ids = list(room.queue[room_id].keys()) + list(room.member[room_id].keys())
            for member_id in member_ids:
                await session.bot.send_msg(message_type="private",
                                           user_id=int(member_id),
                                           message=f"岛【{room_id}】修改备注\n新备注：{remake}")
            await session.finish(f"修改备注成功")
    await session.send(f"你尚未开启过岛，请使用 /开岛 命令，并输入正确格式开启")


# 表格内容解析
async def get_details(text):
    match = re.match(r'^([0-9A-Za-z]{5})[|]([^|]{1,100})[|]{0,1}([1-7]{0,1})$', text)
    if match:
        return match.groups()
    return None


@scheduler.scheduled_job('interval', minutes=1)
async def _():
    room = Room()
    room.save()
