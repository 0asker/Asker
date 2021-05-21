'''
esse script funciona 24 horas por dia em busca de novas perguntas para responder.
'''

import os
import django
import time
import sqlite3
from difflib import SequenceMatcher

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")
django.setup()

from main_app.models import User, UserProfile, Question, Response

bot_username = '3kgijpnfazmacehomqldl1'

bot_user = User.objects.get(username=bot_username)
bot_user_p = UserProfile.objects.get(user=bot_user)

conn = sqlite3.connect('conversations.db')

def similar(a, b):
	return SequenceMatcher(None, a, b).ratio()

def get_response(message):
	message = message.lower()
	result = 'tá'
	conversations = conn.execute('SELECT * FROM conversations').fetchall()
	for c in conversations:
		if similar(c[0].lower(), message) >= 0.65:
			result = c[1]
			break
	return result

while True:
	last = Question.objects.all().last()

	# verifica se já o bot respondeu essa pergunta
	if Response.objects.filter(question=last, creator=bot_user_p).exists():
		# já respondeu.
		# time.sleep para não forçar muito o servidor.
		time.sleep(5)
		continue
	'''
	Se o Bot ainda não respondeu a pergunta, responde ela.
	'''
	response = get_response(last.text)
	r = Response.objects.create(question=last, creator=bot_user_p, text=response)
	r.save()

	q = r.question
	q.total_responses += 1
	q.save()
