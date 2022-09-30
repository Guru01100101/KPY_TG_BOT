from functools import wraps

from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime as dt
import logging
import json
import pytz
import asyncio

logging.basicConfig(level=logging.DEBUG, encoding='UTF-8')


def read_config() -> dict:
    with open('config.json', encoding='utf-8') as f:
        return json.load(f)


def get_token(config: dict) -> str:
    return config['bot']['TOKEN']


def get_id(config: dict) -> int:
    return config['bot']['chat_id']


def set_chat_id(config: dict, chat_id: int) -> None:
    config['bot']['chat_id'] = chat_id
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)


def get_status(config: dict, reminder_name: str) -> dict:
    return config[reminder_name]['status']


def set_status(config: dict, reminder_name: str, status: bool = True) -> None:
    config[reminder_name]['status'] = status
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)


def admin_status(func):
    @wraps(func)
    async def wrapper(message: types.Message):
        if message.from_user.id in read_config()['bot']['admins_id']:
            await func(message)
        else:
            await message.answer('Немає доступу')

    return wrapper


bot = Bot(token=get_token(read_config()))
dp = Dispatcher(bot)


@admin_status
@dp.message_handler(commands=['send_id'], commands_prefix='!')
async def send_id(message: types.Message):
    await bot.send_message(message.from_user.id, message.chat.id)


@dp.channel_post_handler()
async def send_channel_id(message: types.Message):
    if message.text == '!send_id':
        await bot.send_message(read_config()['bot']['admins_id'][0], message.chat.id)


@dp.message_handler(commands=['my_id'], commands_prefix='!')
async def my_id(message: types.Message):
    await bot.send_message(message.from_user.id, f'Your ID: {message.from_user.id}')


@admin_status
@dp.message_handler(commands=['set_id'], commands_prefix='!')
async def set_id(message: types.Message):
    set_chat_id(read_config(), int(message.text.split()[1]))
    await message.answer(f'Новий id для чату: {message.text.split()[1]}')


@admin_status
@dp.message_handler(commands=['set_admin'], commands_prefix='!')
async def set_admin(message: types.Message):
    try:
        config = read_config()
        if message.text.split()[1].isalpha():
            user = await bot.get_chat(message.text.split()[1])
        else:
            user = await bot.get_chat(int(message.text.split()[1]))
        if user.id not in config['bot']['admins_id'] and int(message.text.split()[2]):
            config['bot']['admins_id'].append(user.id)
            await message.answer(f'Додано адміна з ID: {user.id}\n'
                                 f'Тег адміна: @{user.username}')
        elif user.id not in config['bot']['admins_id'] and not int(message.text.split()[2]):
            config['bot']['admins_id'].remove(user.id)
            await message.answer(f'Видалено адміна з ID: {message.text.split()[1]}\n'
                                 f'Тег адміна: @{user.username}')
        else:
            await message.answer(f'Команда !set_admin призначена для додавання адміна бота. Синтаксис команди:\n'
                                 f'!set_admin <user_id> <status>\n'
                                 f'де <user_id> ')
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(e)


@dp.message_handler(commands=['start'], commands_prefix='!/')
async def start(message: types.Message):
    await message.reply('Вас вітає бот, якого призначено для робочого чату Каховського районного управління Головного '
                        'управління ДСНС України у Херсонській області. Для отримання додаткової інформації '
                        'скористуйтесь командою !help або !допомога')


@dp.message_handler(commands=['help'], commands_prefix='!/')
async def bot_help(message: types.Message):
    await message.reply('Бот призначено для нагадування про робочі питання та не має додаткових команд для '
                        'загального використання. Якщо вас зацікавила структура боту, то ви можете знайти його на '
                        'github за посиланням: https://github.com/Guru01100101/KPY_TG_BOT')
    if message.from_user.id in read_config()['bot']['admins_id']:
        await message.reply('Для адміністраторів бота доступні такі команди:\n'
                            '!send_id - відправити id чату\n'
                            '!set_id - встановити id чату\n'
                            '\nСписок команд розширюватиметься з часом')


@admin_status
@dp.message_handler(commands=['send_now'], commands_prefix='!')
async def send_now(message: types.Message):
    pass


@admin_status
@dp.message_handler(commands=['set_status'], commands_prefix='!')
async def set_status(message: types.Message):
    try:
        config = read_config()
        if len(message.text.split()) == 1:
            await message.answer('Команда призначена для зміни статусу нагадування. '
                                 'Для зміни статусу нагадування введіть команду !set_status <назва нагадування> '
                                 '<статус>. <статус> може бути 1 (нагадувати) або 0 (не нагадувати)'
                                 'Для перегляду статусу нагадувань введіть команду !get_status <назва нагадування>')
        elif message.text.split()[1] == 'all':
            for reminder in config['reminders']:
                await set_status(config, reminder, bool(message.text.split()[2]))
                await message.reply(f'Статус нагадування {reminder} змінено на {bool(message.text.split()[2])}')
            await message.answer('Статуси нагадувань успішно змінено')
        else:
            await set_status(read_config(), message.text.split()[1], bool(message.text.split()[2]))
            await message.reply(
                f'Статус нагадування {message.text.split()[1]} було змінено на {bool(message.text.split()[2])}')
    except Exception as e:
        await message.reply('Помилка: ' + str(e))
        await message.reply('Для перегляду синтаксу введіть команду !set_status')


@admin_status
@dp.message_handler(commands=['get_status'], commands_prefix='!')
async def get_status(message: types.Message):
    try:
        if len(message.text.split()) == 1:
            await message.answer('Команда призначена для перегляду статусу нагадування. '
                                 'Для перегляду статусу нагадування введіть команду !get_status <назва нагадування>. '
                                 'Для перегляду статусу всіх нагадувань введіть команду !get_status all')
        elif message.text.split()[1] == 'all':
            config = read_config()
            for reminder in config['reminders']:
                await message.reply(f'Статус нагадування {reminder} - {get_status(config, reminder)}')
        else:
            await message.reply(f'Статус нагадування {message.text.split()[1]} - '
                                f'{get_status(read_config(), message.text.split()[1])}')
    except IndexError:
        await message.reply('Таке нагадування відсутнє.')


async def remind(reminder_name, send_now_flag=False):
    while read_config()['reminders'][reminder_name]['status']:
        reminder = read_config()['reminders'][reminder_name]
        now = dt.now(tz=pytz.timezone('Europe/Kiev'))
        for time in reminder['time']:
            h, m = map(int, time.split(":"))
            if (now.hour == h and now.minute == m) or send_now_flag:
                await bot.send_message(read_config()['bot']['chat_id'], reminder['message'])
                await bot.send_message(414923557, f'Нагадування {reminder[reminder_name]} надіслано о {h}:{m}')
                print(h, ':', m)
                print(f'Нагадування {reminder[reminder_name]} надіслано')
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(1)


async def on_startup(dp):
    for reminder_name in read_config()['reminders']:
        asyncio.create_task(remind(reminder_name))
        print(f'Додано нагадування: {reminder_name}')
    print('Бот запущено')


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
