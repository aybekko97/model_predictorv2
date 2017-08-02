#!usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime

import telebot
import cherrypy
import config
import requests

from Main import HousePricing
from flat import Flat
from validations import *

import myapiai


# import pandas as pd

import sys

# sys.path.append("thesun/ML/Controller/")
# sys.path.append("thesun/ML/")
# from System import *

# TRAINING MODEL

model = HousePricing()
model.train_model()

# LOGGING SETTING
logging.basicConfig(level=logging.DEBUG,
                    filename='system.log',
                    format="%(asctime)s - %(levelname)s - %(lineno)s - %(message)s")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('history.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

# from AddressHandler import *

WEBHOOK_HOST = '146.185.158.146'
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % config.token

bot = telebot.TeleBot(config.token)

flat_dict = {}
step = {}
query_limit = {}
last_query_day = {}


# Наш вебхук-сервер
# class WebhookServer(object):
#     @cherrypy.expose
#     def index(self):
#         if 'content-length' in cherrypy.request.headers and \
#                         'content-type' in cherrypy.request.headers and \
#                         cherrypy.request.headers['content-type'] == 'application/json':
#             length = int(cherrypy.request.headers['content-length'])
#             json_string = cherrypy.request.body.read(length).decode("utf-8")
#             update = telebot.types.Update.de_json(json_string)
#             # Эта функция обеспечивает проверку входящего сообщения
#             bot.process_new_updates([update])
#             return ''
#         else:
#             raise cherrypy.HTTPError(403)


def in_step_handler(chat_id):
    if step.get(chat_id, 0) == 0 or step.get(chat_id, 0) == None:
        return False
    return True


# Хэндлер на команды /start и /help
@bot.message_handler(commands=['help', 'start'])
def welcome_message(message):
    wlc_msg = "Привет!\nТы обратился к боту, который сможет предсказать цену для твоей недвижимости. 🏡 ➡ 💰"
    help_msg = "*/ask* - чтобы предоставить данные вашей недвижимости для определения цены"
    bot.send_message(message.chat.id, wlc_msg + "\n\n" + help_msg, parse_mode="Markdown")

attributes = ['room_number',  # 0
              'house_type',  # 1
              'built_time',  # 2
              'floor',  # 3
              'all_space',  # 4
              'living_space',  # 5
              'kitchen_space',  # 6
              'at_the_hostel',  # 7
              'region',  # 8
              'map_complex',  # 9
              'addr_street',  # 10
              'addr_number',  # 11
              'state',  # 12
              'phone',  # 13
              'internet',  # 14
              'bathroom',  # 15
              'balcony',  # 16
              'balcony_is_glazed',  # 17
              'door',  # 18
              'parking',  # 19
              'furniture',  # 20
              'flooring',  # 21
              'ceiling']  # 22

to_ask = [True, True, True, True,
          True, False, False, True,
          True, False, True, True,
          True, True, True, True,
          True, False, False, True,
          True, False, False]
'''
to_ask = [False, False, False, False,
          False, False, False, False,
          True, False, True, True,
          True, True, True, True,
          True, False, False, True,
          True, False, False]
'''
questions = ['Сколько комнат в квартире?',
             'Какой тип строения у квартиры?',
             'Год постройки дома(сдачи в эксплуатацию)?',
             'На каком этаже находится квартира? (прим. "7 из 10")',
             'Какова общая площадь? (прим. "75.5" м2)',
             'Какова площадь жилой комнаты? (прим. "41" м2)',
             'Какова площадь куханной? (прим. "12.2" м2)',
             'Квартира находится в приватном общежитии?',
             'В каком районе находится?',
             'Жилой комплекс в котором находится дом? (прим. "нет" или "Нурлы Тау")',
             'Улица или микрорайон?',
             'Номер дома?',
             'В каком состоянии находится дом?',
             'Имеется ли домашний телефон?',
             'Какой вид интернета имеется в вашем доме?',
             'Тип санузела(ванная,туалет)?',
             'Есть ли балкон?',
             'Балкон остеклен?',
             'Тип входной двери?',
             'Есть ли рядом парковка?',
             'Насколько мебелирована квартира?',
             'Каким материалом покрыт пол?',
             'Высота потолков в квартире? (прим. "2.9" в метрах)']

selections = [roomSelect,
              houseTypeSelect,
              None,
              None,
              None,
              None,
              None,
              hostelSelect,
              regionSelect,
              None,
              None,
              None,
              stateSelect,
              phoneSelect,
              internetSelect,
              bathroomSelect,
              balconySelect,
              balconyIsGlazedSelect,
              doorSelect,
              parkingSelect,
              furnitureSelect,
              flooringSelect,
              None]

validations = [validate_room,
               validate_house_type,
               validate_built_time,
               validate_floor,
               validate_all_space,
               None,
               None,
               validate_at_the_hostel,
               validate_region,
               None,
               validate_addr_street,
               None,
               validate_state,
               validate_phone,
               validate_internet,
               validate_bathroom,
               validate_balcony,
               None,
               None,
               validate_parking,
               validate_furniture,
               None,
               None]

MAX_QUERY_LIMIT = 3

order = [1, 2, 10, 7, 12, 13, 3, 5, 14, 11, 15, 16, 6, 4, 8, 9]

@bot.message_handler(commands=['ask'])
def ask(message):
    try:
        chat_id = message.chat.id
        prev_step = step.get(chat_id, None)
        cur_step = prev_step

        # Здесь обновление и проверка лимита запросов (изменение дня дегендей)
        if cur_step is None:
            cur_step = 0

            today = datetime.date.today().day
            if chat_id not in last_query_day or last_query_day[chat_id] != today:
                query_limit[chat_id] = MAX_QUERY_LIMIT
            if query_limit[chat_id] == 0:
                bot.send_message(chat_id, "Извините, вы исчерпали количество попыток.")
                return
            last_query_day[chat_id] = today
            logger.info(" chat_id - [%s] : Asking is started!" % chat_id)
        else:
            prev_step -= 1

        if chat_id not in flat_dict:
            flat_dict[chat_id] = Flat()

        # Итерируем до следующего нужного нам вопроса
        while cur_step < len(questions) and to_ask[cur_step] is False:
            cur_step += 1

        # Здесь происходит валидация ответа
        if prev_step is not None and prev_step < len(questions):
            logger.info(" chat_id - [%s] : message - %s" % (chat_id, message.text))
            flat = flat_dict[chat_id]
            if validations[prev_step] is not None:
                val_string = validations[prev_step](message.text)
                if isinstance(val_string, bool):
                    msg = bot.send_message(chat_id, "неправильно, введите еще раз, пожалуйста.")
                    bot.register_next_step_handler(msg, ask)
                    return
                setattr(flat, attributes[prev_step], val_string)
            else:
                #flat_dict[chat_id] = flat + "|" + message.text
                setattr(flat, attributes[prev_step], message.text)

        if cur_step < len(questions):
            msg = bot.send_message(chat_id,
                                   '*' + questions[cur_step] + '*',
                                   reply_markup=selections[cur_step],
                                   parse_mode="Markdown")
            step[chat_id] = cur_step + 1
            bot.register_next_step_handler(msg, ask)
        elif cur_step == len(questions):
            flat = flat_dict[chat_id].__dict__
            data = list(flat.values())

            new_data = []
            for pos in order[:-2]:
                if (pos == 4):
                    new_data.extend(data[pos])
                else:
                    new_data.append(data[pos])
            new_data.append("%s, %s" % (data[order[-2]], data[order[-1]]))
            data = "|".join(new_data)
            logger.info(" chat_id - [%s] : message - got all data - %s" % (chat_id, data))

            msg = bot.send_message(chat_id, "Calculating...")
            price = model.predict(data)
            bot.send_message(chat_id, "Я думаю, подходящая цена - " + price)
            logger.info(" chat_id - [%s] : message - finished, predicted price - %s" % (chat_id, price))

            msg = bot.send_message(chat_id,
                                   '*Оцените, пожалуйста, результат относительно ваших ожидании.*',
                                   reply_markup=feedbackSelect,
                                   parse_mode="Markdown")
            step[chat_id] = cur_step + 1
            bot.register_next_step_handler(msg, ask)
        else:
            step[chat_id] = None
            query_limit[chat_id] -= 1
            bot.send_message(chat_id, "Спасибо за ответ!\nУ вас осталось %s попыток на сегодня." % query_limit[chat_id])
            logger.info(" chat_id - [%s] : message - User's feedback = %s" % (chat_id, message.text))
    except Exception as e:
        logger.error(" chat_id - [%s] : message - %s" % (message.chat.id, str(e)))
        bot.reply_to(message, 'Что-то пошло не так.')
        step[message.chat.id] = 0


@bot.message_handler(func=lambda message: in_step_handler(message.chat.id) == False, content_types=['text'])
def echo_message(message):
    try:
        logger.info(" chat_id - [%s] : message - %s" % (message.chat.id, message.text))
        bot.reply_to(message, myapiai.get_response(message.text))
    except Exception as e:
        logger.error(" chat_id - [%s] : message - %s" % (message.chat.id, e.strerror))
        bot.reply_to(message, 'Что-то пошло не так.')

bot.remove_webhook()

bot.polling(none_stop=True)

# # Снимаем вебхук перед повторной установкой (избавляет от некоторых проблем)
# bot.remove_webhook()
#
# # Ставим заново вебхук
# bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
#                 certificate=open(WEBHOOK_SSL_CERT, 'r'))
#
# # Указываем настройки сервера CherryPy
# cherrypy.config.update({
#     'server.socket_host': WEBHOOK_LISTEN,
#     'server.socket_port': WEBHOOK_PORT,
#     'server.ssl_module': 'builtin',
#     'server.ssl_certificate': WEBHOOK_SSL_CERT,
#     'server.ssl_private_key': WEBHOOK_SSL_PRIV
# })
#
# # Собственно, запуск!
# cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
