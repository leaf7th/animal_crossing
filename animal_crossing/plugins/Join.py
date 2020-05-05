from nonebot import on_command, CommandSession
from .Object import Room


@on_command('join', aliases=('进房', '排队', '参加'), only_to_me=True)
async def join(session: CommandSession):
    details = session.current_arg_text.strip()
    details = str(details)
    room = Room()
    user_id = str(session.event['user_id'])
    room_id = room.in_member(user_id)
    if await room.check_group_member(session.event['user_id']) is None:
        return
    if details not in room.room.keys():
        await session.send('该岛不存在')
    elif room_id:
        if room.member[room_id][user_id]['ready'] is True:
            await session.send(f'你已在岛【{room_id}】中，岛密码为：' + room.room[room_id]["passwd"])
        else:
            await session.send(f'你已在岛【{room_id}】中，你尚未准备')
    elif room.in_queue(user_id) is not None:
        await session.send('你已在队列中，请勿重复排队或排多个队伍')
    else:
        if room.get_user_number(details) < int(room.room[details]['length']) and len(room.queue[details]) == 0:
            await room.add_member(user_id, details, session.event["sender"]['nickname'])
            await session.send(f'成功进入岛\n'
                               f'岛密码为：{room.room[details]["passwd"]}\n'
                               f'请在出岛后使用 /退出 命令退出该岛\n'
                               f'大头菜房请勿跑多趟，每次排队仅能跑一趟！')
        else:
            room.add_queue(user_id, details, session.event["sender"]['nickname'])
            length = room.get_wait_len(user_id)
            await session.send(f"成功进入队列\n"
                               f"前方队列长度为：{length}人")


@join.args_parser
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if session.is_first_run:
        if stripped_arg:
            session.state['details'] = stripped_arg
        return
    if not stripped_arg:
        session.pause('不能返回空值，请重新输入')
    session.state[session.current_key] = stripped_arg
