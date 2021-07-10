from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import HttpResponse, JsonResponse

'''
Paginação:
'''
from django.core.paginator import Paginator, EmptyPage

from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.models import User
from django_project.settings import EMAIL_HOST_USER
from django.contrib.humanize.templatetags.humanize import naturalday
from djpjax import pjax
from django.template.response import TemplateResponse
from django.core.cache import cache

import django_project.general_rules as general_rules
from main_app.models import UserProfile, Question, Response, Notification, Comment, Report, Poll, PollChoice, PollVote
from main_app.templatetags.main_app_extras import fix_naturaltime
from main_app.forms import UploadFileForm

from bs4 import BeautifulSoup as bs
from redislite import Redis

import re
from random import shuffle
from hashlib import sha256

import time
import random
import string

import io
from PIL import Image, ImageFile, UnidentifiedImageError, ImageSequence


import re
'''
Retorna True se a requisição vier de um dispositivo mobile.
'''
def mobile(request):
	MOBILE_AGENT_RE=re.compile(r".*(iphone|mobile|androidtouch)",re.IGNORECASE)

	if MOBILE_AGENT_RE.match(request.META['HTTP_USER_AGENT']):
		return True
	return False


def search_questions(query):
  queries = query.split()

  all_questions = Question.objects.all()

  result = {'questions': []}

  for question in all_questions:
    reputation = 0
    for query in queries:
      if query in question.text or query in question.description:
        reputation += 1

    precision = (reputation / len(queries)) * 100
    if precision >= 70:
      result['questions'].append({
        'title': question.text,
        'description': question.description,
        'id': question.id,
        'precision': precision,
      })

  '''
    {
      ['title': 'título da pergunta',
      'description': 'descrição da pergunta',
      'id': 'id da pergunta',
      'precision': 'precisão da pergunta baseado na consulta do usuário',]
    }
  '''



  return result


def compress_animated(bio, max_size, max_frames):
	im = Image.open(bio)
	frames = list()
	min_size = min(max_size)
	frame_count = 0
	for frame in ImageSequence.Iterator(im):
		if frame_count > max_frames:
			break
		compressed_f = frame.convert('RGBA') # PIL não salvará o canal A! Workaround: salvar em P-mode
		alpha_mask = compressed_f.getchannel('A') # Máscara de transparência
		compressed_f = compressed_f.convert('RGB').convert('P', colors=255) # Converte para P
		mask = Image.eval(alpha_mask, lambda a: 255 if a <= 128 else 0) # Eleva pixels transparentes
		compressed_f.paste(255, mask) # Aplica a máscara
		compressed_f.info['transparency'] = 255 # O valor da transparência, na paleta, é o 255
		if max(im.size[0], im.size[1]) > min_size:
			compressed_f.thumbnail(max_size)
		frames.append(compressed_f)
		frame_count += 1
	dur = im.info['duration']
	im_final = frames[0]
	obio = io.BytesIO()
	im_final.save(obio, format='GIF', save_all=True, append_images=frames[1:], duration=dur, optimize=False, disposal=2)
	#print('Antes: {}, Depois: {}. Redução: {}%'.format(str(bio.tell()), str(obio.tell()), str(100 - int((obio.tell()*100) / bio.tell())) ))
	if obio.tell() < bio.tell():
		return obio
	return bio

def save_img_file(post_file, file_path, max_size):
	img_data = b''
	for chunk in post_file.chunks():
		img_data += chunk

	ImageFile.LOAD_TRUNCATED_IMAGES = True
	try:
		im = Image.open(io.BytesIO(img_data))
		if im.format in ('GIF', 'WEBP') and im.is_animated:
			bio = compress_animated(io.BytesIO(img_data), max_size, 80)
			with open(file_path, 'wb+') as destination:
				destination.write(bio.getbuffer())
		else:
			im.thumbnail(max_size)
			im.save(file_path, im.format)
	except UnidentifiedImageError:
		return False
	return True


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def calculate_popular_questions():
	last_questions = Question.objects.order_by('-pub_date')[:100]

	'''
	Essa variável guarda, dentro, as perguntas e seus totais de pontos.
	Por exemplo: questions[0][0] é o total de pontos. questions[0][1] é o ID da pergunta.
	'''
	questions = []

	'''
	Calculando o total de likes da pergunta com mais likes:
	'''
	likes = 0
	for q in last_questions:
		if q.total_likes > likes:
			likes = q.total_likes

	'''
	Calculando o total de respostas da pergunta com mais respostas:
	'''
	responses = 0
	for q in last_questions:
		if q.total_responses > responses:
			responses = q.total_responses

	'''
	Calculando o total de visualizações da pergunta com mais visualizações.
	'''
	views = 0
	for q in last_questions:
		if q.total_views > views:
			views = q.total_views

	'''
	Adicionando as perguntas na variável questions e inicializando os pontos de acordo com o tempo de likes.
	'''
	for q in last_questions:
		questions.append([q.total_likes / likes * 100, q.id])

	'''
	Incrementando pontos de acordo com o total de respostas.
	'''
	for question in last_questions:
		for q in questions:
			if q[1] == question.id:
				q[0] += question.total_responses / responses * 100

	'''
	Incrementando pontos de acordo com o total de visualizações.
	'''
	for question in last_questions:
		for q in questions:
			if q[1] == question.id:
				q[0] += question.total_views / views * 100

	questions = sorted(questions, key=lambda questions: questions[0], reverse=True) # ordenação: com mais pontos para menos pontos.
	ids = []
	for q in questions:
		ids.append(q[1])

	'''
	Adicionando as questões numa lista de JSON.
	'''
	p_questions = []
	for id in ids:

		try:
			question = Question.objects.get(id=id)
		except:
			continue

		p_questions.append(question)

	return p_questions


'''
 Essa função salva uma resposta. Sempre quando um usuário
envia uma resposta para uma pergunta, a resposta passa por aqui
para ser salva (no banco de dados).
'''
def save_answer(request):
	if request.method != 'POST':
		return HttpResponse('Proibido.')

	question_id = request.POST.get('question_id')
	question = Question.objects.get(id=question_id)

	response_creator = UserProfile.objects.get(user=request.user) # criador da nova resposta.

	'''
	Testa se o usuário já respondeu a pergunta:
	'''
	if Response.objects.filter(creator=response_creator, question=question).exists():
		return HttpResponse('Você já respondeu essa pergunta.')

	if question.creator.blocked_users.filter(username=request.user.username).exists():
		return HttpResponse(False)

	text = request.POST.get('text')

	if not is_a_valid_response(text):
		return HttpResponse('Proibido.')

	response = Response.objects.create(question=question,
									   creator=response_creator,
									   text=bs(text, 'lxml').text)

	question.total_responses += 1
	question.save()

	response_creator.total_points += 2
	response_creator.save()

	notification = Notification.objects.create(receiver=question.creator.user,
											   type='question-answered')
	notification.set_text(response.id)
	notification.save()

	json = {'answer_id': response.id}

	'''
	Upload de imagens:
	'''

	form = UploadFileForm(request.POST, request.FILES)
	if form.is_valid():
		f = request.FILES['file']

		file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
		file_name += str(f)

		success = save_img_file(f, 'django_project/media/responses/' + file_name, (850, 850))
		if success: # TODO: mensagem caso não dê certo
			response.image = 'responses/' + file_name

		response.save()

	try:
		image_url = response.image.url
		json['has_image'] = True
		json['image_url'] = response.image.url
	except:
		json['has_image'] = False

	#from django.contrib.humanize.templatetags.humanize import naturaltime

	'''
	Resposta serializada:
	response = {
		'creator_username': response.creator.user.username,
		'text': response.text,
		'pub_date': naturaltime(response.pub_date),
		'total_likes': response.total_likes,
	}
	'''

	return render(request, 'base/response-content.html', {
		'question': question,
		'response': response,
	})


def index(request):

	context = {}

	# pega as perguntas da mais nova para a mais velha:
	q = Question.objects.order_by('-pub_date')
	p = Paginator(q, 20)
	page = request.GET.get('page', 1)
	questions = p.page(page)
	context['questions'] = questions

	'''
	Pegando as perguntas populares:
	Pega as últimas 250 perguntas;
	Pega o total de likes da pergunta com mais likes (dessas últimas 250);
	Compara cada pergunta (uma por uma) com esse total de likes, por exemplo: a pergunta com mais likes tem 100 likes, se a pergunta x tem 50 likes, então a pergunta x ganha 50 pontos (50%: o cálculo é feito com base na porcentagem);
	No final, organiza as perguntas por total de likes e guarda o ID delas em uma lista para consultar as perguntas novamente no banco de dados (Question.objects.filter(id__in=IDS_EM_ORDEM_DE_QUAL_PERGUNTA_TEM_MAIS_PONTOS)).
	'''

	p_questions = cache.get('p_questions')

	if not p_questions:
		p_questions = calculate_popular_questions()
		cache.set('p_questions', p_questions)


	'''
	Paginação das perguntas populares:
	'''
	page = request.GET.get('p_page', 1)
	p_questions = Paginator(p_questions, 20)
	context['popular_questions'] = p_questions.page(page)

	if request.user.is_authenticated:
		user_p = UserProfile.objects.get(user=request.user)
		user_p.ip = get_client_ip(request)
		user_p.save()
		context['user_p'] = user_p
		if not user_p.active:
			context['account_verification_alert'] = '<div class="alert alert-info"><p>Confirme seu email abrindo o link enviado para ele.<br>Este é o email usado na tela de cadastro: {}</p><p>Caso não encontre o email, verifique na pasta de spam.</p></div>'.format(request.user.email)

	if request.GET.get('new_user', 'false') == 'true':
		context['account_verification_alert'] = SUCCESS_ACCOUNT_VERIFICATION

	return render(request, 'index.html', context)


def question(request, question_id):
	try:
		q = Question.objects.get(id=question_id)
		q.total_views += 1
		q.save()
	except:
		return_to = request.META.get("HTTP_REFERER") if request.META.get("HTTP_REFERER") is not None else '/'
		context = {'error': 'Pergunta não encontrada',
				   'err_msg': 'Talvez ela tenha sido apagada pelo criador da pergunta.',
				   'redirect': return_to}
		return render(request, 'error.html', context)

	responses = Response.objects.filter(question=q).order_by('-pub_date').order_by('-total_likes')

	context = {'question': q,
			   'responses': responses}
	
	if mobile(request) and random.choice([1,2,3,4]) == 4:
		print('oi' * 1000)
		context['MOBILE_ADS'] = True

	if not request.user.is_anonymous:
		context['user_p'] = UserProfile.objects.get(user=request.user)
		context['answered'] = False
		for response in responses:
			if response.id == request.user.id:
				context['answered'] = True
				break

	'''
	Questões recomendadas.
	Elas ficam no cache por 5 minutos até se atualizarem.

	Dica: organizar ordem das questões em JavaScript no lado do cliente para
	evitar processamento desnecessário no servidor.
	'''
	recommended_questions = cache.get('recommended_questions')
	if not recommended_questions:
		cache.set('recommended_questions', list(Question.objects.order_by('-pub_date')[:15]))
		recommended_questions = cache.get('recommended_questions')
	shuffle(recommended_questions)
	context['recommended_questions'] = recommended_questions


	if q.has_poll():
		context['poll'] = Poll.objects.get(question=q)
		context['poll_choices'] = PollChoice.objects.filter(poll=context['poll'])
		context['poll_votes'] = PollVote.objects.filter(poll=context['poll'])

	return render(request, 'question.html', context)


def like(request):

    answer_id = request.GET.get('answer_id')

    r = Response.objects.get(id=answer_id)

    q = r.question
    if r.likes.filter(username=request.user.username).exists():
        r.likes.remove(request.user)
        r.total_likes = r.likes.count()
        r.save()
        # diminui total de likes da pergunta:
        q.total_likes -= 1
        q.save()
    else:
        r.likes.add(request.user)
        r.total_likes = r.likes.count()
        r.save()
        # aumenta total de likes da pergunta:
        q.total_likes += 1
        q.save()

        if not Notification.objects.filter(type='like-in-response', liker=request.user, response=r).exists():
            # cria uma notificação para o like (quem recebeu o like será notificado):
            n = Notification.objects.create(receiver=Response.objects.get(id=answer_id).creator.user,
                                            type='like-in-response',
                                            liker=request.user,
                                            response=r)
            n.set_text(answer_id)
            n.save()

    return HttpResponse('OK')


def delete_response(request):
    r = Response.objects.get(id=request.GET.get('response_id'))

    ''' Tira 2 pontos do criador da resposta, já que a resposta vai ser apagada por ele mesmo. '''
    creator = r.creator
    creator.total_points -= 3 # por enquanto vai tirar 3, para alertar trolls.
    creator.save()

    try:
        ''' Deleta também a imagem do sistema de arquivos para liberar espaço. '''
        import os
        os.system('rm ' + r.image.path)
    except:
        pass

    q = r.question
    q.total_responses -= 1
    q.save()
    r.delete()

    return HttpResponse('OK')


def signin(request):

	r = request.GET.get('redirect')

	if r == None:
		r = '/'

	if request.method == 'POST':
		r = request.POST.get('redirect')
		email = request.POST.get('email')
		password = request.POST.get('password')

		# testa se o email existe:
		if not User.objects.filter(email=email).exists():
			return render(request, 'signin.html', {'login_error': '''<div class="alert alert-danger error-alert" role="alert"><h4 class="alert-heading">Ops!</h4>Dados de login incorretos.</div>''',
												   'redirect': r})

		user = authenticate(username=User.objects.get(email=email).username, password=password)

		if user is None:
			return render(request, 'signin.html', {'login_error': '''<div class="alert alert-danger error-alert" role="alert"><h4 class="alert-heading">Ops!</h4>Dados de login incorretos.</div>''',
												   'redirect': r})
		login(request, user)
		return redirect(r)

	return render(request, 'signin.html', {'redirect': r})


def signup(request):

	if request.method == 'POST':
		r = request.POST.get('redirect')
		username = request.POST.get('username').strip()
		email = request.POST.get('email').strip()
		password = request.POST.get('password')

		'''
		Validação do nome de usuário: verifica se combina com o regex (apenas letras, números, hífens, undercores e espaços).
		'''
		regex = r'^[-\w_ ]+$'
		try:
			re.search(regex, username)[0]
		except:
			html = '<div class="alert alert-danger"><p>O nome de usuário deve conter apenas caracteres alfanuméricos, hífens, underscores e espaços.</p></div>'
			return render(request, 'signup.html', {'invalid_username': html,
														 'username': username,
														 'email': email,
														 'redirect': r,
														 'username_error': ' is-invalid'})

		''' Validação das credenciais: '''
		if not is_a_valid_user(username, email, password):
			return HttpResponse('Proibido.')

		if User.objects.filter(username=username).exists():
			return render(request, 'signup.html', {'error': '''<div class="alert alert-danger error-alert" role="alert"><h4 class="alert-heading">Ops!</h4>Nome de usuário em uso.</div>''',
												   'username': username,
												   'email': email,
												   'redirect': r,
												   'username_error': ' is-invalid'})

		if User.objects.filter(email=email).exists():
			return render(request, 'signup.html', {'error': '''<div class="alert alert-danger error-alert" role="alert"><h4 class="alert-heading">Ops!</h4>Email em uso. Faça login <a href="/signin">aqui</a>.</div>''',
												   'username': username,
												   'email': email,
												   'redirect': r,
												   'email_error': ' is-invalid'})

		u = User.objects.create_user(username=username, email=email, password=password)
		login(request, u)

		''' Geração do código de confirmação de conta: '''
		s = 'abcdefghijklmnopqrstuvwxyz123456789'
		RANDOM_CODE = ''.join(random.sample(s, len(s)))

		new_user_profile = UserProfile.objects.create(user=u)
		new_user_profile.ip = get_client_ip(request)
		new_user_profile.active = True
		new_user_profile.verification_code = RANDOM_CODE
		new_user_profile.save()

		#subject = 'Asker.fun: confirmação de conta'
		#message = '''Olá {}! Obrigado por criar uma conta no Asker.fun.
#
#Para continuar, verifique seu endereço de email usando o link:
#https://asker.pythonanywhere.com/account/verify?user={}&code={}
#
#Obrigado e bem vindo(a)!
#'''.format(username, sha256(bytes(username, 'utf-8')).hexdigest(), RANDOM_CODE)
#		recipient = [email]
#		print(send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False))

		return redirect(r)

	context = {
		'redirect': request.GET.get('redirect', '/'),
	}

	return render(request, 'signup.html', context)


def profile(request, username):
	try:
		u = UserProfile.objects.get(user=User.objects.get(username=username))
	except:
		return_to = request.META.get("HTTP_REFERER") if request.META.get("HTTP_REFERER") is not None else '/'
		context = {'error': 'Usuário não encontrado', 'err_msg': 'Este usuário não existe ou alterou seu nome.',
				   'redirect': return_to}
		return render(request, 'error.html', context)
	if request.user.username != username and request.user.username != 'Erick':
		u.total_views += 1
		u.save()

	context = {'user_p': u, 'change_profile_picture_form': UploadFileForm()}

	if request.user.username == username or not u.hide_activity:
		q_page = request.GET.get('q-page', 1)
		r_page = request.GET.get('r-page', 1)

		context['questions'] = Paginator(Question.objects.filter(creator=u).order_by('-pub_date'), 10).page(q_page).object_list
		context['responses'] = Paginator(Response.objects.filter(creator=u).order_by('-pub_date'), 10).page(r_page).object_list

	if request.method == 'POST':
		# TODO: acho que isso não é mais necessário, já que agora existe outra url pra editar o perfil?

		new_bio = request.POST.get('bio', None)

		if new_bio != None:
			u = UserProfile.objects.get(user=request.user)
			u.bio = new_bio
			u.save()
			return redirect('/user/' + username)

	return render(request, 'profile.html', context)


def ask(request):
	'''
	Controle de spam
	'''
	try:
		last_q = Question.objects.filter(creator=UserProfile.objects.get(user=request.user))
		last_q = last_q[last_q.count()-1] # pega a última questão feita pelo usuário.
		if (timezone.now() - last_q.pub_date).seconds < 25:
			return_to = request.META.get("HTTP_REFERER") if request.META.get("HTTP_REFERER") is not None else '/'
			context = {'error': 'Ação não autorizada',
					   'err_msg': 'Você deve esperar {} segundos para perguntar novamente.'.format(25 - (timezone.now() - last_q.pub_date).seconds),
					   'redirect': return_to}
			return render(request, 'error.html', context)
	except:
		pass

	if request.method == 'POST':

		if request.POST.get('question') == '' or request.POST.get('question') == '.':
			return render(request, 'ask.html', {'error': '<p>Pergunta inválida.</p>'})

		description = bs(request.POST.get('description'), 'html.parser').text
		description = description.replace('\r', '')

		text = request.POST.get('question')

		if not is_a_valid_question(text, description):
			return HttpResponse('Proibido.')

		q = Question.objects.create(creator=UserProfile.objects.get(user=request.user), text=text, description=description)

		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			f = request.FILES['file']

			file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
			file_name += str(f)

			success = save_img_file(f, 'django_project/media/questions/' + file_name, (850, 850))
			if success: # TODO: mensagem caso não dê certo
				q.image = 'questions/' + file_name

			q.save()

		ccount = request.POST.get('choices-count')
		if ccount.isdigit():
			is_multichoice = request.POST.get('is-multichoice') is not None
			ccount = int(ccount)
			if ccount <= general_rules.MAXIMUM_POLL_CHOICES and ccount > 1: # Proteção de POST manual
				qpoll = Poll.objects.create(question=q, is_anonymous=True, multichoice=is_multichoice)
				for i in range(1, ccount + 1):
					choice = request.POST.get('choice-' + str(i))
					if len(choice) <= 60 and len(choice) >= 1 and choice.replace(' ', '') != '':
						PollChoice.objects.create(poll=qpoll, text=choice)
					else:
						PollChoice.objects.create(poll=qpoll, text="...")


		u = UserProfile.objects.get(user=request.user)
		u.total_points += 1
		u.save()

		return redirect('/question/' + str(q.id))

	return render(request, 'ask.html', {'user_p': UserProfile.objects.get(user=request.user),
																			'is_mobile': mobile(request)})


def logout(request):
	django_logout(request)
	return redirect('/')


def notification(request):

    p = Paginator(Notification.objects.filter(receiver=request.user).order_by('-creation_date'), 15)

    page = request.GET.get('page', 1)

    context = {
        'notifications': p.page(page),
    }

    return render(request, 'notification.html', context)


def deleteQuestion(request):
	if request.method != 'POST':
		return HttpResponse('Erro.')
	q = Question.objects.get(id=request.POST.get('question_id'))
	q.delete()
	return HttpResponse('OK')


def comment(request):
	Comment.objects.create(response=Response.objects.get(id=request.POST.get('response_id')),
												 creator=request.user,
												 text=request.POST.get('text'),
												 pub_date=timezone.now())
	return HttpResponse('')


def rank(request):
	rank = UserProfile.objects.order_by('-total_points')[:50]
	count = 0
	for user in rank:
		count += 1
		user.rank = count
	return render(request,'rank.html',{'rank':rank})


def edit_response(request):

	id=request.POST.get('response_id')

	r = Response.objects.get(creator=UserProfile.objects.get(user=request.user), id=id)
	r.text = bs(request.POST.get('response').replace('\r\n\r\n', '\n\n'), 'lxml').text
	r.save()

	return redirect('/question/' + str(r.question.id))


def get_more_questions(request):
	page = request.GET.get('q_page', 2)
	user_id = request.GET.get('user_id')
	target = UserProfile.objects.get(user=User.objects.get(id=user_id))
	if target.hide_activity:
		if target.user.id != request.user.id:
			return 'Proibido.'
	q = Question.objects.filter(creator=target).order_by('-pub_date')

	p = Paginator(q, 10)

	json = {
	}

	json['questions'] = {}

	count = 1

	try:
		p.page(page)
	except:
		return HttpResponse(False)

	for q in p.page(page):
		if target.user.id == request.user.id:
			best_answer = q.best_answer
		else:
			best_answer = -1
		json['questions'][count] = {
			'text': q.text,
			'id': q.id,
			'naturalday': naturalday(q.pub_date),
			'best_answer': best_answer
		}
		count += 1

	json['has_next'] = p.page(page).has_next()

	return JsonResponse(json)


def get_more_responses(request):
	page = request.GET.get('r_page', 2)
	user_id = request.GET.get('user_id')
	target = UserProfile.objects.get(user=User.objects.get(id=user_id))
	if target.hide_activity:
		if target.user.id != request.user.id:
			return 'Proibido.'
	r = Response.objects.filter(creator=target).order_by('-pub_date')
	p = Paginator(r, 10)

	json = {
	}

	json['responses'] = {}

	count = 1
	for r in p.page(page):
		json['responses'][count] = {
			'text': r.text,
			'question_text': r.question.text,
			'question_id': r.question.id,
			'best_answer': r.id == r.question.best_answer,
			'creator': r.question.creator.user.username,
			'naturalday': naturalday(r.question.pub_date)
		}
		count += 1

	json['has_next'] = p.page(page).has_next()

	print(json)

	return JsonResponse(json)


def delete_question(request, question_id):
	if request.user.username != 'Erick':
		return HttpResponse('Proibido.')
	q = Question.objects.get(id=question_id)
	q.delete()
	return HttpResponse('OK')


def delete_comment(request):
	c = Comment.objects.get(id=request.GET.get('comment_id'))

	if request.user != c.creator:
		return HttpResponse('Proibido.')

	c.delete()
	return HttpResponse('OK')


def report(request):

	report_type = request.GET.get('type')

	if report_type == 'response':
		if Report.objects.filter(item=request.GET.get('id')).exists():
			return HttpResponse('OK')

		if request.user.is_anonymous:
			reporter = None
		else:
			reporter = request.user

		Report.objects.create(type=request.GET.get('type'),
							  item=request.GET.get('id'),
							  reporter=reporter,
							  url='https://asker.fun/question/' + str(Response.objects.get(id=request.GET.get('id')).question.id),
							  text='Resposta: ' + str(Response.objects.get(id=request.GET.get('id')).text))
	elif report_type == 'ad':
		Report.objects.create(type="ad",
							  reporter=request.user,
							  text=request.GET.get('text'))
	else:
		if UserProfile.objects.get(user=request.user).total_points < 300:
			return HttpResponse('OK')
		q = Question.objects.get(id=request.GET.get('id'))
		if q.reporters.filter(username=request.user.username).exists():
			return HttpResponse('OK')
		#q.reports += 1
		#q.reporters.add(request.user)
		#q.save()

		if q.reports >= 3:
			q.delete()
	return HttpResponse('OK')


def edit_profile(request, username):

	if request.method == 'POST':
		if request.POST.get('type') == 'profile-pic':
			form = UploadFileForm(request.POST, request.FILES)
			if form.is_valid():
				f = request.FILES['file']
				'''
				Nome da imagem do usuário no sistema de arquivos: nome de usuário atual, data de alteração e horário da alteração.
				'''
				file_name = '{}-{}-{}'.format(request.user.username, timezone.now().date(), timezone.now().time())

				success = save_img_file(f, 'django_project/media/avatars/' + file_name, (192, 192))
				if not success:
					return redirect('/user/' + request.user.username + '/edit')  # TODO: Mostrar um erro de arquivo invalido!

				u = UserProfile.objects.get(user=request.user)
				u.avatar = 'avatars/' + file_name
				u.save()
			return redirect('/user/' + username)
		if request.POST.get('type') == 'bio':
			u = UserProfile.objects.get(user=request.user)
			u.bio = request.POST.get('bio')
			u.save()
			return redirect('/user/' + username)
		if request.POST.get('type') == 'username':

			username = request.POST.get('username')

			# validação do novo nome de usuário:
			r = r'^[-\w_ ]+$'
			try:
				re.search(r, username)[0]
			except:
				html = '<div class="alert alert-danger"><p>O nome de usuário deve conter apenas caracteres alfanuméricos, hífens, underscores e espaços.</p></div>'
				return render(request, 'edit-profile.html', {'invalid_username_text': html,
															 'username': username,
															 'invalid_username': ' is-invalid'})

			if len(username) > 30:
				return HttpResponse('Escolha um nome de usuário menor ou igual a 30 caracteres.')

			if User.objects.filter(username=username).exists():
				return render(request, 'edit-profile.html', {'user_p': UserProfile.objects.get(user=User.objects.get(username=username)), 'username_display': 'block', 'invalid_username': ' is-invalid'})

			password = request.POST.get('password')
			user = authenticate(username=request.user.username, password=password)
			if user is None:
				if not User.objects.filter(username=request.POST.get('username')).exists():
					try:
						return render(request, 'edit-profile.html', {'user_p': UserProfile.objects.get(user=User.objects.get(username=username)), 'password_display': 'block', 'invalid_password': ' is-invalid'})
					except:
						return render(request, 'edit-profile.html',
									  {'user_p': UserProfile.objects.get(user=User.objects.get(username=request.user.username)),
									   'password_display': 'block', 'invalid_password': ' is-invalid'})
			user.username = request.POST.get('username').strip()
			user.save()
			login(request, user)
			return redirect('/user/' + user.username)
		if request.POST.get('type') == 'privacy':
			u = UserProfile.objects.get(user=request.user)
			if request.POST.get('hide-activity') is not None:
				u.hide_activity = True
			else:
				u.hide_activity = False
			u.save()
			return redirect('/user/' + username)

	return render(request, 'edit-profile.html', {'user_p': UserProfile.objects.get(user=User.objects.get(username=username))})


def block(request, username):
	u_p = UserProfile.objects.get(user=request.user)
	if u_p.blocked_users.filter(username=username).exists():
		u_p.blocked_users.remove(User.objects.get(username=username))
		return HttpResponse('Bloquear')
	u_p.blocked_users.add(User.objects.get(username=username))
	return HttpResponse('Bloqueado')


def account_verification(request):
	hash = request.GET.get('user') # o valor do parâmetro user é nada mais nada menos do que a soma sha256 do nome de usuário.
	CODE = request.GET.get('code') # código de verificação.

	for u in UserProfile.objects.all():
		if sha256(bytes(u.user.username, 'utf-8')).hexdigest() == hash:
			if u.verification_code == CODE:
				u.active = True
				u.save()
				return redirect('/?new_user=true')
			else:
				return HttpResponse('Erro: código de verificação incorreto.')
	return HttpResponse('Erro.')


def user_info(request, username):
	if request.user.username != 'Erick':
		return HttpResponse('Sem informações.')

	user = User.objects.get(username=username)
	user_profile = UserProfile.objects.get(user=user)

	context = {
		'user_p': user_profile,
	}

	return render(request, 'user-info.html', context)


''' A função abaixo faz a validação das credenciais de novos usuários. '''
def is_a_valid_user(username, email, password):
	if len(username) > 30:
		return False
	elif len(email) > 60:
		return False
	elif len(password) < 6 or len(password) > 256:
		return False
	return True


''' A função abaixo faz a validação de novas questões (perguntas). '''
def is_a_valid_question(text, description):
	if len(text) > 180:
		return False
	if len(description) > 5000:
		return False
	return True


''' A função abaixo faz a validação de novas respostas. '''
def is_a_valid_response(text):
	return True


''' A função abaixo faz a validação de um novo comentário. '''
def is_a_valid_comment(text):
	if len(text) > 300:
		return False
	return True


'''
Recompensa por adicionar o site aos favoritos.
'''
def increasePoints(request):

	user_profile = UserProfile.objects.get(user=request.user)

	if user_profile.message == 'ok': # caso o usuário já tenha ganhado os 100 pontos por adicionar o site aos favoritos.
		return HttpResponse('OK')

	user_profile.total_points += 100
	user_profile.message = 'ok' # 'ok' em message: significa que o usuário já ganhou a recompensa por adicionar o site aos favoritos.
	user_profile.save()
	return HttpResponse('OK')


def reset_password(request):

	if request.method == 'POST':
		user = User.objects.get(email=request.POST.get('email'))
		user.set_password(request.POST.get('password1'))
		user.save()

		return HttpResponse('''<!doctype html>
		<html>
		<head>
		<meta charset="utf-8">
		<meta name="viewport" content="width=device-width, initial-scale=1">
		</head>
		<body>
		<p>Senha alterada com sucesso. <a href="/signin">Clique aqui</a> para fazer login.</p>
		</body>
		</html>
		''')

	if request.GET.get('type', None) == 'email-verification':
		'''
		Para alterar senha:
		é gerado novo código de verificação aleatório para a conta;
		é enviado um email para a conta com três parâmetros GET: parâmetro type = get-form, parâmetro verification-code = novo código de verificação e parâmetro username = username;
		se o código de verificação estiver correto é enviado o formulário para troca de senha, se não, é enviado um erro.
		'''
		u_p = UserProfile.objects.get(user=User.objects.get(email=request.GET.get('email')))
		u_p.verification_code = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
		u_p.save()

		send_mail('Asker: trocar senha', 'Para alterar sua senha do Asker, use o link: https://br.asker.fun/reset-password?type=get-form&username={}&code={}\nEntre em contato por este email caso ocorra algum erro.'.format(u_p.user.username.replace(' ', '%20'), u_p.verification_code), EMAIL_HOST_USER, [u_p.user.email], fail_silently=False)

		return HttpResponse('Email de verificação enviado. Por favor, verifique seus emails, caso não encontre, verifique a pasta de spam.')
	elif request.GET.get('type', None) == 'get-form':
		u_p = UserProfile.objects.get(user=User.objects.get(username=request.GET.get('username')))

		if u_p.verification_code == request.GET.get('code'):
			return render(request, 'change-password.html', {'email': u_p.user.email})
		return HttpResponse('Ocorreu um erro, por favor, tente novamente. Caso o erro persista, <a href="mailto:minha.ccontta@gmail.com">nos envie um email</a>.')

	return render(request, 'reset-password-1-part.html')


def update_popular_questions(request):

	q = Question.objects.order_by('-pub_date')

	redis_connection = Redis('/tmp/asker.db')
	ID_LIST = ''
	for id in Paginator(sorted(q[:150], key=lambda o: o.total_likes, reverse=True), 20).page(1).object_list:
		ID_LIST += str(id) + ' '
	ID_LIST = ID_LIST.strip()
	redis_connection.set('popular_questions', ID_LIST)

	return HttpResponse('OK')

def choose_best_answer(request):

    answer_id = request.GET.get('answer_id')
    r = Response.objects.get(id=answer_id)
    q = r.question
    user = request.user
    quser = q.creator
    if user.id == quser.id and r.creator.user.id == user.id:
        return HttpResponse('Proibido.')
    if r.creator.user.id == quser.id:
        return HttpResponse('Proibido.')
    if q.may_choose_answer():
        q.best_answer = answer_id
        q.save()
        n = Notification.objects.create(receiver=r.creator.user, type='got-best-answer', response=r)
        n.set_text(answer_id)
        n.save()
        rcuserp = UserProfile.objects.get(user=r.creator.user)
        quserp = UserProfile.objects.get(user=request.user)
        rcuserp.total_points += 10
        quserp.total_points += 2
        rcuserp.save()
        quserp.save()
    #else: # P/ testes rápidos - desfaz a MR
    #    q.best_answer = None
    #    q.save()

    return HttpResponse('OK')


def delete_account(request):
	if not request.user.is_authenticated:
		return HttpResponse('Proibido.')

	if request.method == 'POST':
		try:
			user = request.user
			user.delete()
		except:
			return False

	return render(request, 'delete-account.html')


def rules(request):
  return render(request, 'rules.html')


def change_email(request):

  if request.method == 'POST':
    password = request.POST.get('password')
    new_email = request.POST.get('email')

    user = authenticate(username=request.user.username, password=password)

    print(request.user.username)
    print(new_email)
    print(password)

    if user is None:
      return HttpResponse('Senha incorreta. <a href="/change-email">Tentar novamente</a>.')

    user.email = new_email
    user.save()

    try:
      login(request)
    except:
      pass

    return HttpResponse('Pronto! Seu novo email é: {}. <a href="/">Voltar para a página inicial</a>.'.format(new_email))

  return render(request, 'change-email.html')


def test(request):

  context = {
    'result': search_questions(request.GET.get('query')),
  }

  return render(request, 'test.html', context)


def activity(request):
  return redirect('/user/' + request.user.username)


'''
Retorna True se tem novas notificações e False se não.
'''
def have_new_notif(request):
  return HttpResponse(True)


'''
Marca todas as notificações como vistas.
'''
def mark_notifications_as_viewed(request):
  for notification in Notification.objects.filter(receiver=request.user):
    notification.read = True
    notification.save()
  return HttpResponse('OK')



def vote_on_poll(request):
	if request.method != 'POST':
		return HttpResponse('Ok.')

	poll_id = request.POST.get('poll')
	user_choices = request.POST.getlist('choices[]')
	p = Poll.objects.get(id=poll_id)
	has_voted = PollVote.objects.filter(poll=p, voter=request.user).exists()

	if has_voted:
		return HttpResponse('Proibido.')
	if not p.multichoice:
		if len(user_choices) > 1:
			return HttpResponse('Proibido.')
	if len(user_choices) > general_rules.MAXIMUM_POLL_CHOICES:
		return HttpResponse('Proibido.')
	if not p.may_vote():
		return HttpResponse('Proibido.')

	for choice in user_choices:
		c_query = PollChoice.objects.filter(id=choice, poll=p) # pollchoice.poll == req.poll (poll=p) p/ evitar manipulação de POST
		if c_query.exists():
			c = c_query[0]
			PollVote.objects.create(poll=p, choice=c, voter=request.user)
			c.votes += 1
			c.save()

	return HttpResponse('Ok.')

def undo_vote_on_poll(request):
	if request.method != 'POST':
		return HttpResponse('Ok.')
	poll_id = request.POST.get('poll')
	p = Poll.objects.get(id=poll_id)
	votes = PollVote.objects.filter(poll=p, voter=request.user)

	if not p.may_vote():
		return HttpResponse('Proibido.')

	for vote in votes:
		c = vote.choice
		c.votes -= 1
		c.save()
		vote.delete()

	return HttpResponse('Ok.')


'''
Configura o status do usuário para online.
'''
def set_status(request):

	user_profile = UserProfile.objects.get(user=request.user)
	user_profile.last_seen = timezone.now()

	return HttpResponse('OK')


def get_popular_questions(request):
	p_questions = cache.get('p_questions')

	if not p_questions:
		p_questions = calculate_popular_questions()
		cache.set('p_questions', p_questions)

	paginator = Paginator(p_questions, 20)
	page = request.GET.get('popular_page', 2)

	try:
		return render(request, 'base/popular-question.html', {'popular_questions': paginator.page(page), 'render_directly': True})
	except EmptyPage:
		return HttpResponse('EmptyPage')
