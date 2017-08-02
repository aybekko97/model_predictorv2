import apiai
import json

CLIENT_ACCESS_TOKEN = 'a85e4e863dca410ba7de7043177e1f52'

ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)


def get_response(query_text):
    request = ai.text_request()
    request.query = query_text
    response = json.loads(request.getresponse().read().decode('utf-8'))
    responseStatus = response["status"]["code"]
    if 200 == responseStatus:
        # Sending the textual response of the bot.
        return response["result"]["fulfillment"]["speech"]
    else:
        return "Sorry, I couldn't understand that question"
