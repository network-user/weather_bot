"""Телеграм бот для просмотра погоды"""
import asyncio
import sqlite3

from aiogram import F
import requests
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

bot = Bot(token="bot token")

dp = Dispatcher()

api_token = "you api token from api.weatherapi.com site"


class Form(StatesGroup):
    waiting_for_item = State()


async def save_user(message: types.Message, state: FSMContext):
    """
    Функция сохраняет новых пользователей в БД
    """
    user = message.from_user.username
    user_id = message.from_user.id
    with sqlite3.connect("telegram_bot_database.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM POGODA WHERE name=?", (user,))
        result = cursor.fetchone()
        if result is None:
            cursor.execute('INSERT INTO POGODA (name, id) VALUES (?, ?)',
                           (user, user_id,))
            connection.commit()
            await message.answer(
                "Вы еще не выбрали город. Пожалуйста, введите город")
            await state.set_state(Form.waiting_for_item)
            print("Пользователь сохранён")

    return f'Новый пользователь: {user}'


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Обработка команды /start
    """
    kb = [
        [types.KeyboardButton(text="Посмотреть погоду")],
        [types.KeyboardButton(text="Выбрать город")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await save_user(message, state)

    await message.answer(
        "Здравствуйте, этот бот предназначен для просмотра погоды.",
        reply_markup=keyboard
    )


@dp.message(F.text == "Выбрать город")
async def change_city(message: types.Message, state: FSMContext):
    """
    Функция смены города
    """
    await message.answer("Введите город, за погодой которого хотите следить:")
    await state.set_state(Form.waiting_for_item)


@dp.message(Form.waiting_for_item)
async def change_city(message: types.Message, state: FSMContext):
    """
    Функция смены города
    """
    user_id = message.from_user.id
    with sqlite3.connect("telegram_bot_database.db") as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE POGODA SET city = ? WHERE id = ?
        ''', (message.text, user_id))
        connection.commit()
    await message.answer("Город изменен")
    await state.clear()


@dp.message(F.text == "Посмотреть погоду")
async def get_weather(message: types.Message):
    """
    Получение погоды
    """
    user_id = message.from_user.id
    with sqlite3.connect("telegram_bot_database.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT city FROM POGODA WHERE id = ?", (user_id,))
        city = cursor.fetchone()
    if city is None:
        await message.answer("Вы ещё не выбрали город для просмотра погоды")
        return
    city = city[0]
    url = f"https://api.weatherapi.com/v1/current.json?key={api_token}&q={city}&units=metric"
    response = requests.get(url)
    if response.status_code == 400:
        await message.answer("Ошибка получения погоды, попробуйте указать другой город")
    json_data = response.text
    data = json.loads(json_data)

    city_name = data["location"]['name']
    current_time = data["location"]["localtime"]
    temp = data["current"]["temp_c"]
    wind_speed = data["current"]["wind_kph"]
    humidity = data["current"]["humidity"]
    condition = data["current"]["condition"]["text"]

    await message.answer(f"**Текущая погода в городе {city_name}:**\n"
                         f"**Время:** {current_time}\n"
                         f"**Температура:** {round(temp)}°C\n"
                         f"**Ветер:** {wind_speed} км/ч\n"
                         f"**Влажность:** {humidity}%\n"
                         f"**Погодные условия:** {condition}")


async def send_messages_all_users(message: types.Message, text: str):
    """
    Функция массовой рассылки
    """
    with sqlite3.connect("telegram_bot_database.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM POGODA")
        results = cursor.fetchall()
        for row in results:
            user_id = row[0]
            print(text)
            await bot.send_message(user_id, text)


@dp.message(Command("alart_all"))
async def alart_all_users(message: types.Message):
    """
    Отправка массовой рассылки
    """
    text = ("Внимание, если вам показывает некорректную погоду, "
            "попробуйте ввести название города на Английском языке")
    await send_messages_all_users(message, text)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
