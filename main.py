from functools import wraps

from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime as dt
import logging
import json
import pytz
import asyncio

logging.basicConfig(level=logging.INFO)


def read_config() -> dict:
    with open('config.json', encoding='utf-8') as f:
        return json.load(f)


def get_token(config: dict) -> str:
    return config['bot']['TOKEN']


def get_id(config: dict) -> int:
    return config['bot']['chat_id']


def set_id(config: dict, chat_id: int) -> None:
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


def log_errors(func):
    @wraps(func)
    async def wrapper(message: types.Message):
        try:
            await func(message)
        except Exception as e:
            logging.exception(e)

    return wrapper


bot = Bot(token=get_token(read_config()))
dp = Dispatcher(bot)


@dp.message_handler(commands=['send_id'], prefix='!')
@admin_status
async def send_id(config: dict, message: types.Message):
    await bot.send_message(config['bot']['admin_id'], message.chat.id)


@dp.message_handler(commands=['set_id'], prefix='!')
@admin_status
async def set_bot_id(config: dict, message: types.Message):
    set_id(config, int(message.text.split()[1]))
    await message.answer(f'Новий id для чату: {message.text.split()[1]}')


@dp.message_handler(commands=['start'], prefix='!/')
async def start(message: types.Message):
    await message.reply('Вас вітає бот, якого призначено для робочого чату Каховського районного управління Головного '
                        'управління ДСНС України у Херсонській області. Для отримання додаткової інформації '
                        'скористуйтесь командою !help або !допомога')


@dp.message_handler(commands=['help'], prefix='!/')
async def bot_help(message: types.Message):
    await message.reply('Бот призначено для нагадування про робочі питання та не має додаткових команд для '
                        'загального використання. Якщо вас зацікавила структура боту, то ви можете знайти його на '
                        'github за посиланням: https://github.com/Guru01100101/KPY_TG_BOT')


@dp.message_handler(commands=['show'], prefix='!')
@admin_status
async def show(message: types.Message):
    pass


@dp.message_handler(commands=['send_now'], prefix='!')
@admin_status
async def send_now(message: types.Message):
    pass


@dp.message_handler(commands=['stop'], prefix='!')
@admin_status
async def stop(message: types.Message):
    pass


@dp.message_handler(commands=['set_status'], prefix='!')
@admin_status
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
        else:
            await set_status(read_config(), message.text.split()[1], bool(message.text.split()[2]))
            await message.reply(f'Статус нагадування {message.text.split()[1]} було змінено на {bool(message.text.split()[2])}')
    except IndexError:
        await message.reply('Невірний формат команди')


@dp.message_handler(commands=['get_status'], prefix='!')
@admin_status
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


async def remind():
    pass


async def on_startup(dp):
    asyncio.create_task(remind())
    await bot.send_message(get_id(read_config()), 'Бот запущено')
