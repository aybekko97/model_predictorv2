# -*- coding: utf-8 -*-
# Этот токен невалидный, можете даже не пробовать :)
token = '443079396:AAFLgvbEDkqQ6Th4YQJBL0awC3ILFB0FVPk'

#FOR SERVER

WEBHOOK_HOST = '146.185.158.146'
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % token

#BOT SETTINGS
MAX_QUERY_LIMIT = 1

provider_token = '284685063:TEST:N2JmZGYxNDc1NmJk'  # @BotFather -> Bot Settings -> Payments