import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import CommandStart
from config import TOKEN
connection = sqlite3.connect("geeks.db")
cursor = connection.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS adminandusers (
                id INTEGER PRIMARY KEY,
                id_chats INTEGER,
                full_name TEXT,
                is_admin BOOLEAN DEFAULT FALSE
                )
            ''')
connection.commit()


bot = Bot(token=TOKEN)
dp = Dispatcher()

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='для админов', callback_data='админ')]
])
keyboard_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='рассылка', callback_data='рассылочка')],
    [InlineKeyboardButton(text='пользователи', callback_data='пользователи')]
])

@dp.message(CommandStart())
async def start_bot(message: Message):
    cursor.execute("SELECT id FROM adminandusers WHERE id = ?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO adminandusers (id, id_chats, full_name, is_admin) VALUES (?, ?, ?, ?)",
                       (message.from_user.id, message.chat.id, message.from_user.full_name, False))
        connection.commit()
    
    await message.reply("Привет! Используйте /start, чтобы начать.", reply_markup=keyboard)



@dp.callback_query(F.data == 'админ')
async def show_admin_commands(callback_query: CallbackQuery):
    await callback_query.message.reply('Команды админов', reply_markup=keyboard_admin)

@dp.callback_query(F.data == 'рассылочка')
async def send_broadcast(callback_query: CallbackQuery):
    await callback_query.message.reply('Введите текст для рассылки.')
    await dp.current_state(user=callback_query.from_user.id).set_data({'broadcasting': True})

@dp.message()
async def handle_broadcast_message(message: Message):
    state = dp.current_state(user=message.from_user.id)
    data = await state.get_data()

    if data.get('broadcasting'):
   
        cursor.execute("SELECT id FROM adminandusers")
        users = cursor.fetchall()

        for user in users:
            try:
                await bot.send_message(user[0], message.text) 
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение пользователю {user[0]}: {e}")

        await state.update_data(broadcasting=False) 
        await message.reply("Рассылка завершена!")

@dp.callback_query(F.data == 'пользователи')
async def list_users(callback_query: CallbackQuery):
    cursor.execute("SELECT id, full_name FROM adminandusers")
    users = cursor.fetchall()
    if users:
        user_list = "\n".join([f"ID: {user[0]}, Имя: {user[1]}" for user in users])
        await callback_query.message.reply(f"Пользователи:\n{user_list}", reply_markup=admin_management_keyboard())
    else:
        await callback_query.message.reply("Нет пользователей.")

def admin_management_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Добавить админа', callback_data='добавить_админа')],
        [InlineKeyboardButton(text='Удалить админа', callback_data='удалить_админа')]
    ])

@dp.callback_query(F.data == 'добавить_админа')
async def add_admin(callback_query: CallbackQuery):
    await callback_query.message.reply('Введите ID пользователя, которого хотите сделать админом.')

@dp.callback_query(F.data == 'удалить_админа')
async def remove_admin(callback_query: CallbackQuery):
    await callback_query.message.reply('Введите ID пользователя, которого хотите удалить из админов.')


@dp.message()
async def handle_message(message: Message):
    if message.text.startswith('/addadmin'):
        try:
            user_id = int(message.text.split()[1])
            cursor.execute("UPDATE adminandusers SET is_admin = TRUE WHERE id = ?", (user_id,))
            connection.commit()
            await message.reply(f'Пользователь с ID {user_id} теперь админ.')
        except (ValueError, IndexError):
            await message.reply("Пожалуйста, укажите корректный ID пользователя.")
        except Exception as e:
            logging.error(f"Ошибка при добавлении админа: {e}")
            await message.reply("Произошла ошибка при добавлении админа.")
    elif message.text.startswith('/removeadmin'):
        try:
            user_id = int(message.text.split()[1])
            cursor.execute("UPDATE adminandusers SET is_admin = FALSE WHERE id = ?", (user_id,))
            connection.commit()
            await message.reply(f'Пользователь с ID {user_id} больше не админ.')
        except (ValueError, IndexError):
            await message.reply("Пожалуйста, укажите корректный ID пользователя.")
        except Exception as e:
            logging.error(f"Ошибка при удалении админа: {e}")
            await message.reply("Произошла ошибка при удалении админа.")
    else:
        await message.answer("Я вас не понял.")


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        connection.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
