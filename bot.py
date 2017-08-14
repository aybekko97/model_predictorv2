#!usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import datetime
import telebot
import config

from telebot.types import LabeledPrice

from Main import HousePricing
from flat import Flat
from validations import *

import myapiai

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

# TRAINING MODEL

print("Started training..")

model = HousePricing()
model.train_model()

print("Finished training!")

WEBHOOK_HOST = '146.185.158.146/'
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % config.token

provider_token = '284685063:TEST:N2JmZGYxNDc1NmJk'  # @BotFather -> Bot Settings -> Payments

prices = [LabeledPrice(label='House Agent Service', amount=5750), LabeledPrice('Gift wrapping', 500)]

bot = telebot.AsyncTeleBot(config.token, threaded=True)

flat_dict = {}
step = {}
query_limit = {}
last_query_day = {}
wait_location = {}


# # Наш вебхук-сервер
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
    if step.get(chat_id, None) == None:
        return False
    return True


# wlc_msg = "Привет!\nТы обратился к боту, который сможет предсказать цену для твоей недвижимости. 🏡 ➡ 💰"

wlc_msg = "\nПривет!" \
          "\nПеред вами бот-оценщик рыночной стоимости вашей недвижимости. " \
          "Я даю наиболее быструю и наиболее обьективную оценку вашей квартиры относительно других наиболее похожих на нее." \
          "\nЯ постоянно совершенствуюсь и обучаюсь. " \
          "По вопросам обращайтесь по телефону +77028759922 или по почте ocenshik10@gmail.com"

help_msg = "*/ask* - чтобы предоставить данные вашей недвижимости для определения цены"


# Хэндлер на команды /start и /help

@bot.message_handler(func=lambda message: in_step_handler(message.chat.id) == False, commands=['help', 'start'])
def welcome_message(message):
    bot.send_message(message.chat.id, wlc_msg + "\n\n" + help_msg, parse_mode="Markdown")


attributes = ['room_number',  # 0
              'house_type',  # 1
              'built_time',  # 2
              'floor',  # 3
              'all_space',  # 4
              'at_the_hostel',  # 5
              'region',  # 6
              'addr_street',  # 7
              'addr_number',  # 8
              None,  # 9
              'state',  # 10
              'bathroom',  # 11
              'furniture',  # 12
              'internet']  # 13

# to_ask = [True, True, True, True,
#           True, True, True, True,
#           True, True, True, True,
#           True, True]

questions = ['Сколько комнат в квартире?',  # 0
             'Какой тип строения у квартиры?',  # 1
             'Год постройки дома(сдачи в эксплуатацию)?',  # 2
             'На каком этаже находится квартира? (прим. "7 из 10")',  # 3
             'Какова общая площадь? (прим. "75.5" м2)',  # 4
             'Квартира находится в приватном общежитии?',  # 5
             'В каком районе находится?',  # 6
             'Улица или микрорайон?',  # 7
             'Номер дома?',  # 8
             'Проверьте, правильно ли указано месторасположение квартиры на карте?',  # 9
             'В каком состоянии находится дом?',  # 10
             'Тип санузела(ванная,туалет)?',  # 11
             'Насколько меблирована квартира?',  # 12
             'Какой вид интернета имеется в вашем доме?',  # 13
             'Выберите варианты, которые пристуствуют в вашей квартире? ']  # 14

selections = [roomSelect,
              houseTypeSelect,
              commonSelect,
              commonSelect,
              commonSelect,
              hostelSelect,
              regionSelect,
              commonSelect,
              commonSelect,
              confirmSelect,
              stateSelect,
              bathroomSelect,
              furnitureSelect,
              internetSelect,
              default_keyboard]

validations = [validate_room,
               validate_house_type,
               validate_built_time,
               validate_floor,
               validate_all_space,
               validate_at_the_hostel,
               validate_region,
               validate_addr_street,
               validate_addr_number,
               validate_confirm,
               validate_state,
               validate_bathroom,
               validate_furniture,
               validate_internet,
               None]

MAX_QUERY_LIMIT = 1


order = [1, 2, 10, 7, 13, 11, 3, 5, 15, 14, 16, 12, 6, 4]
CONFIRM_STEP = 9
STATE_STEP = 10


@bot.message_handler(func=lambda message: (message.text == "/ask" or in_step_handler(message.chat.id) == True),
                     content_types=['text', 'location'])
def ask(message):
    chat_id = message.chat.id
    cur_step = step.get(chat_id, None)

    # Здесь обновление и проверка лимита запросов (изменение дня дегендей)
    try:
        if cur_step is None:
            prev_step = None
            cur_step = 0

            today = datetime.date.today().day
            if chat_id not in last_query_day or last_query_day[chat_id] != today:
                query_limit[chat_id] = MAX_QUERY_LIMIT
            if query_limit[chat_id] == 0:
                bot.send_message(chat_id, "Извините, вы исчерпали количество попыток.")
                return
            last_query_day[chat_id] = today
            last_keyboard[chat_id] = default_keyboard
            wait_location[chat_id] = False
            logger.info(" chat_id - [%s] : Asking is started!" % chat_id)
        else:
            prev_step = cur_step - 1
    except Exception as e:
        step[chat_id] = None
        logger.error(" chat_id - [%s] : message - %s" % (message.chat.id, e))
        bot.reply_to(message, 'Что-то пошло не так.')

    try:
        if cur_step - 1 == CONFIRM_STEP:
            if wait_location[chat_id] == True:
                if message.location == None:
                    msg = bot.send_message(chat_id,
                                           "*Но я жду локацию вашего дома, прошу, отправьте локацию.*",
                                           parse_mode="Markdown")
                    # bot.register_next_step_handler(msg, ask)
                    return
                else:
                    flat_dict[chat_id].location = (str(message.location.latitude), str(message.location.longitude))
                    bot.send_message(chat_id,
                                     "*Отлично!.*",
                                     parse_mode="Markdown")
                    cur_step += 1
                    msg = bot.send_message(chat_id,
                                           '*' + questions[cur_step - 1] + '*',
                                           reply_markup=selections[cur_step - 1],
                                           parse_mode="Markdown")
                    step[chat_id] = cur_step
                    wait_location[chat_id] = False
                    # bot.register_next_step_handler(msg, ask)
                    return
            if message.text == "нет":
                msg = bot.send_message(chat_id,
                                       "Пожалуйста, отправьте тогда геолокацию вашей квартиры (через прикрепить(знак скрепки) --> локация(location)).",
                                       parse_mode="Markdown")
                wait_location[chat_id] = True
                # bot.register_next_step_handler(msg, ask)
                return

    except Exception as e:
        step[chat_id] = None
        logger.error(" chat_id - [%s] : message - %s" % (message.chat.id, e))
        bot.reply_to(message, 'Что-то пошло не так.')

    try:
        if message.text == "⬅ Назад" and 0 < cur_step <= len(questions):
            if cur_step - 1 == STATE_STEP:
                cur_step -= 2
            else:
                cur_step -= 1
            msg = bot.send_message(chat_id,
                                   '*' + questions[cur_step - 1] + '*',
                                   reply_markup=selections[cur_step - 1],
                                   parse_mode="Markdown")
            step[chat_id] = cur_step
            # bot.register_next_step_handler(msg, ask)
            return
    except Exception as e:
        step[chat_id] = None
        logger.error(" chat_id - [%s] : message - %s" % (message.chat.id, e))
        bot.reply_to(message, 'Что-то пошло не так.')

    if message.text == "🔚 Выйти":
        step[chat_id] = None
        bot.send_message(chat_id, wlc_msg + "\n\n" + help_msg, parse_mode="Markdown")
        return

    if chat_id not in flat_dict:
        flat_dict[chat_id] = Flat()

    # Итерируем до следующего нужного нам вопроса


    # Здесь происходит валидация ответа
    try:
        if prev_step is not None and prev_step < len(attributes):
            try:
                logger.info(" chat_id - [%s] : message - %s" % (chat_id, message.text))
                flat = flat_dict[chat_id]
                if validations[prev_step] is not None:
                    val_string = validations[prev_step](message.text)
                    if isinstance(val_string, bool):
                        msg = bot.send_message(chat_id, "неправильно, введите еще раз, пожалуйста.")
                        # bot.register_next_step_handler(msg, ask)
                        return
                    if attributes[prev_step] is not None:
                        setattr(flat, attributes[prev_step], val_string)
                else:
                    # flat_dict[chat_id] = flat + "|" + message.text
                    if attributes[prev_step] is not None:
                        setattr(flat, attributes[prev_step], message.text)
            except Exception as e:
                logger.error(" chat_id - [%s] : cur_step - %s,  message - %s" % (message.chat.id, cur_step, e))
                bot.reply_to(message, 'Что-то пошло не так.')
    except Exception as e:
        logger.error(" chat_id - [%s] : message - %s" % (message.chat.id, e))
        bot.reply_to(message, 'Что-то пошло не так.')
        step[message.chat.id] = None

    if cur_step < len(questions):
        if cur_step == CONFIRM_STEP:
            latitude, longitude = HousePricing.yandex_geocoder("%s, %s" % (flat.addr_street, flat.addr_number))
            flat_dict[chat_id].location = (latitude, longitude)
            bot.send_location(chat_id, latitude, longitude)
        msg = bot.send_message(chat_id,
                               '*' + questions[cur_step] + '*',
                               reply_markup=selections[cur_step],
                               parse_mode="Markdown")

        if cur_step == len(questions) - 1:
            bot.send_message(chat_id, text="Если все выбрали, нажмите кнопку 'Посчитать!'", reply_markup=finalSelect)
        step[chat_id] = cur_step + 1

        # msg.wait()

        # bot.register_next_step_handler(msg, ask)
        return
    elif cur_step == len(questions):
        flat = flat_dict[chat_id]
        keyboard = last_keyboard[chat_id]
        flat.phone = "0" if (keyboard.keyboard[0][0]['text'][-1] == '✖') else "1"
        flat.balcony = "0" if (keyboard.keyboard[1][0]['text'][-1] == '✖') else "1"
        flat.parking = "0" if (keyboard.keyboard[2][0]['text'][-1] == '✖') else "1"
        flat = flat.__dict__
        loc = flat['location']
        del flat['location']
        data = list(flat.values())
        logger.info("%s" % (flat.keys()))
        new_data = []
        for pos in order:
            if pos == 4:
                new_data.extend(data[pos])
            else:
                new_data.append(data[pos])
        new_data.append(loc[0] + " " + loc[1])
        data = "|".join(new_data)
        logger.info(" chat_id - [%s] : message - got all data - %s" % (chat_id, data))

        msg = bot.send_message(chat_id, "Calculating... —> Идет расчет...")
        price = model.predict(data)[0]
        bot.send_message(chat_id, "Я думаю, подходящая цена - " + str(price))
        logger.info(" chat_id - [%s] : message - finished, predicted price - %s" % (chat_id, price))

        msg = bot.send_message(chat_id,
                               '*Пожалуйста, оцените результат относительно ваших ожиданий*',
                               reply_markup=feedbackSelect,
                               parse_mode="Markdown")
        step[chat_id] = cur_step + 1
        # bot.register_next_step_handler(msg, ask)
        return
    else:
        step[chat_id] = None
        query_limit[chat_id] -= 1
        if query_limit[chat_id] == 0:
            bot.send_message(chat_id,
                             "Спасибо за ответ!\nВы исчерпали лимит запросов. Нужно заплатить для дальнейшего пользования сервисом.")
            bot.send_invoice(message.chat.id, title='House Agent',
                             description='Узнайте цену вашей квартиры прямо тут и сейчас!'
                                         '\nНет нужды нанимать квартирного агента!'
                                         '\nСэкономьте время, вы вычислим цену вашей квартиры мгновенно!',
                             provider_token=provider_token,
                             currency='usd',
                             photo_url='https://www.imoney.my/articles/wp-content/uploads/2014/01/real-estate-agent.jpg',
                             photo_height=512,  # !=0/None or picture won't be shown
                             photo_width=512,
                             photo_size=512,
                             is_flexible=False,  # True If you need to set up Shipping Fee
                             prices=prices,
                             start_parameter='house-agent',
                             invoice_payload='Наслаждайтесь!')

        else:
            bot.send_message(chat_id, "Спасибо за ответ!")
        logger.info(" chat_id - [%s] : message - User's feedback = %s" % (chat_id, message.text))


last_keyboard = {}

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    query_limit[message.chat.id] = MAX_QUERY_LIMIT
    bot.send_message(message.chat.id,
                     'Поздравляю, теперь вы можете дальше пользоваться услугой.',
                     parse_mode='Markdown')

@bot.message_handler(func=lambda message: in_step_handler(message.chat.id) == False, content_types=['text'])
def echo_message(message):
    try:
        logger.info(" chat_id - [%s] : message - %s" % (message.chat.id, message.text))
        bot.reply_to(message, myapiai.get_response(message.text))
    except Exception as e:
        logger.error(" chat_id - [%s] : message - %s" % (message.chat.id, e))
        bot.reply_to(message, 'Что-то пошло не так.')


# В большинстве случаев целесообразно разбить этот хэндлер на несколько маленьких
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Если сообщение из чата с ботом
    if call.message:
        if call.data == "phone":
            keyboard = last_keyboard[call.message.chat.id]
            if keyboard.keyboard[0][0]['text'][-1] == '✖':
                keyboard.keyboard[0][0]['text'] = "Домашний телефон ✔"
            else:
                keyboard.keyboard[0][0]['text'] = "Домашний телефон ✖"
            last_keyboard[call.message.chat.id] = keyboard
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=keyboard)
        if call.data == "balcony":
            keyboard = last_keyboard[call.message.chat.id]
            if keyboard.keyboard[1][0]['text'][-1] == '✖':
                keyboard.keyboard[1][0]['text'] = "Балкон ✔"
            else:
                keyboard.keyboard[1][0]['text'] = "Балкон ✖"
            last_keyboard[call.message.chat.id] = keyboard
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=keyboard)
        if call.data == "parking":
            keyboard = last_keyboard[call.message.chat.id]
            if keyboard.keyboard[2][0]['text'][-1] == '✖':
                keyboard.keyboard[2][0]['text'] = "Паркинг ✔"
            else:
                keyboard.keyboard[2][0]['text'] = "Паркинг ✖"
            last_keyboard[call.message.chat.id] = keyboard
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=keyboard)

        if call.data == "back":
            msg = call.message
            msg.text = "⬅ Назад"
            # bot.register_next_step_handler(msg, ask)
            return
        if call.data == "exit":
            msg = bot.send_message()
            # bot.register_next_step_handler(msg, ask)
            return


bot.remove_webhook()


bot.skip_pending = True
bot.polling(none_stop=True)

# Снимаем вебхук перед повторной установкой (избавляет от некоторых проблем)
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

#
# @bot.pre_checkout_query_handler(func=lambda query: True)
# def checkout(pre_checkout_query):
#     bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
#                                   error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
#                                                 " try to pay again in a few minutes, we need a small rest.")


# @bot.message_handler(content_types=['successful_payment'])
# def got_payment(message):
#     bot.send_message(message.chat.id,
#                      'Hoooooray! Thanks for payment! We will proceed your order for `{} {}` as fast as possible! '
#                      'Stay in touch.\n\nUse /buy again to get a Time Machine for your friend!'.format(
#                          message.successful_payment.total_amount / 100, message.successful_payment.currency),
#                      parse_mode='Markdown')
