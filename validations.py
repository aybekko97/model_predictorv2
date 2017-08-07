#!/usr/bin/python
# -*- coding: utf-8 -*-
import copy

from telebot import types
import re

room_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

house_type_list = ['кирпичный', 'панельный', 'монолитный', 'каркасно-камышитовый', 'иное']

region_list = ['Алатауский р-н',
               'Алмалинский р-н',
               'Ауэзовский р-н',
               'Бостандыкский р-н',
               'Жетысуский р-н',
               'Медеуский р-н',
               'Наурызбайский р-н',
               'Турксибский р-н']

state_list = ['хорошее',
              'среднее',
              'евроремонт',
              'требует ремонта',
              'свободная планировка',
              'черновая отделка']

internet_list = ['ADSL',
                 'через TV кабель',
                 'проводной',
                 'оптика',
                 'нет']

bathroom_list = ['раздельный',
                 'совмещенный',
                 '2 с/у и более',
                 'нет']

yes_no_list = ['нет',
               'да']

furniture_list = ['полностью',
                  'частично',
                  'пустая']

feedback_list = ['очень дешево',
                 'дешево',
                 'нормально',
                 'дорого',
                 'очень дорого']

roomSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=3, resize_keyboard=True)
roomSelect.add(*(room_list+["⬅ Назад"]))

houseTypeSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
houseTypeSelect.add(*(house_type_list+["⬅ Назад", "🔚 Выйти"]))

hostelSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2, resize_keyboard=True)
hostelSelect.add(*(yes_no_list+["⬅ Назад", "🔚 Выйти"]))

regionSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
regionSelect.add(*(region_list+["⬅ Назад", "🔚 Выйти"]))

confirmSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2, resize_keyboard=True)
confirmSelect.add(*(yes_no_list+["⬅ Назад", "🔚 Выйти"]))

stateSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
stateSelect.add(*(state_list+["⬅ Назад", "🔚 Выйти"]))

internetSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
internetSelect.add(*(internet_list+["⬅ Назад", "🔚 Выйти"]))

bathroomSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
bathroomSelect.add(*(bathroom_list+["⬅ Назад", "🔚 Выйти"]))

furnitureSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
furnitureSelect.add(*(furniture_list+["⬅ Назад", "🔚 Выйти"]))

feedbackSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
feedbackSelect.add(*feedback_list)

commonSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
commonSelect.add(*["⬅ Назад", "🔚 Выйти"])

finalSelect = copy.deepcopy(commonSelect)
finalSelect.row_width = 2
finalSelect.add("🔹 Посчитать 🔹")

default_keyboard = types.InlineKeyboardMarkup()
phone_button = types.InlineKeyboardButton(text="Домашний телефон ✖", callback_data="phone")
balcony_button = types.InlineKeyboardButton(text="Балкон ✖", callback_data="balcony")
parking_button = types.InlineKeyboardButton(text="Парковка ✖", callback_data="parking")

default_keyboard.add(phone_button)
default_keyboard.add(balcony_button)
default_keyboard.add(parking_button)


def validate_room(msg):
    room_cnt = ''.join([c for c in msg if c in '1234567890.']).strip()
    if room_cnt.isdigit() and 0 < int(room_cnt) < 10:
        return room_cnt
    else:
        return False

def validate_house_type(msg):
    msg = msg.strip().lower()
    if msg in house_type_list:
        return msg
    return False

def validate_floor(msg):
    if re.match("^[0-9]* из [0-9]*$", msg):
        msg = msg.split()
        if int(msg[0]) < int(msg[2]) and int(msg[2]) <= 50:
            return [msg[0], msg[2]]
    return False


def validate_at_the_hostel(msg):
    msg = msg.strip().lower()
    if msg in yes_no_list:
        return str(yes_no_list.index(msg))
    return False


def validate_furniture(msg):
    msg = msg.strip().lower()
    if msg in furniture_list:
        if (furniture_list.index(msg) == 0):
            return "1.0"
        if (furniture_list.index(msg) == 1):
            return "0.5"
        if (furniture_list.index(msg) == 2):
            return "0.0"
    return False


def validate_region(msg):
    msg = msg.strip()
    if msg in region_list:
        return msg
    return False

def validate_confirm(msg):
    msg = msg.strip().lower()
    if msg in yes_no_list:
        return str(yes_no_list.index(msg))
    return False


def validate_internet(msg):
    msg = msg.strip()
    if msg in internet_list:
        return msg
    return False


def validate_bathroom(msg):
    msg = msg.strip().lower()
    if msg in bathroom_list:
        return msg
    return False


def validate_state(msg):
    msg = msg.strip().lower()
    if msg in state_list:
        return msg
    return False


def validate_built_time(msg):
    built_time = ''.join([c for c in msg if c in '1234567890. ']).strip()
    if built_time.isdigit() and 1900 < int(built_time) < 2017:
        return built_time
    else:
        return False


def validate_all_space(msg):
    all_space = ''.join([c for c in msg if c in '1234567890. ']).strip()
    try:
        if 20. < float(all_space) < 300.:
            return all_space
        else:
            return False
    except:
        return False