from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.models import User
from django_project.settings import EMAIL_HOST_USER
from django.contrib.humanize.templatetags.humanize import naturalday
from djpjax import pjax
from django.template.response import TemplateResponse
from django.core.cache import cache

from main_app.models import UserProfile, Question, Response, Notification, Comment, Report, Ban

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


SUCCESS_ACCOUNT_VERIFICATION = '''
<style>
			/* Estilos para a div abaixo. */
			#alert-email-activation {
				width: 50%;
				margin: auto;
			}

			@media (min-width: 320px) and (max-width: 480px) {
				#alert-email-activation {
					width: 98%;
				}
			}
		</style>
		<div id="alert-email-activation" class="alert alert-success" role="alert">
			<p>Conta verificada com sucesso!</p>
		</div>
'''


@pjax()
def pjax_questions(request):
	context = {}
	q = Question.objects.order_by('-pub_date')
	p = Paginator(q, 20)
	questions = p.page(1)
	context['questions'] = questions
	return TemplateResponse(request, "base/recent-questions.html", context)


def replace_url_to_link(value):
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.MULTILINE|re.UNICODE)
    value = urls.sub(r'<a href="\1" target="_blank">\1</a>', value)
    urls = re.compile(r"([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)", re.MULTILINE|re.UNICODE)
    value = urls.sub(r'<a href="mailto:\1">\1</a>', value)
    return value

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

def index(request):	
	if request.method == 'POST':
		if Response.objects.filter(creator=UserProfile.objects.get(user=request.user), question=Question.objects.get(id=request.POST.get('question_id'))).exists():
			return HttpResponse('OK')

		user = User.objects.get(username=Question.objects.get(id=request.POST.get('question_id')).creator.user.username)
		user_profile = UserProfile.objects.get(user=user)

		if user_profile.blocked_users.filter(username=request.user.username).exists():
			return HttpResponse(False)

		q = Question.objects.get(id=request.POST.get('question_id'))

		text = request.POST.get('text').replace('\r\n\r\n', '\n\n')
		if not is_a_valid_response(text):
			return HttpResponse('Proibido.')

		r = Response.objects.create(question=q, creator=UserProfile.objects.get(user=request.user), text=bs(text, 'lxml').text)
		q.total_responses += 1

		u_p = UserProfile.objects.get(user=request.user)
		u_p.total_points += 2
		u_p.save()

		q.save()

		n = Notification.objects.create(receiver=r.question.creator.user,
										type='question-answered')
		n.set_text(r.id)
		n.save()
		return HttpResponse('OK')

	context = {}

	# pega as perguntas da mais nova para a mais velha:
	q = Question.objects.order_by('-pub_date')
	p = Paginator(q, 20)
	page = request.GET.get('page', 1)
	questions = p.page(page)
	context['questions'] = questions
	
	'''
	Perguntas populares:
	'''
	p_questions = cache.get('p_questions')
	if not p_questions:
		p_questions = Paginator(sorted(q[:150], key=lambda o: o.total_likes, reverse=True), 20).page(1).object_list
		cache.set('p_questions', p_questions)

	context['popular_questions'] = p_questions

	if request.user.is_authenticated:
		user_p = UserProfile.objects.get(user=request.user)
		user_p.ip = get_client_ip(request)
		user_p.save()
		context['user_p'] = user_p
		if not UserProfile.objects.get(user=request.user).active:
			context['account_verification_alert'] = '<div class="alert alert-info"><p>Confirme seu email abrindo o link enviado para ele.<br>Este é o email usado na tela de cadastro: {}</p><p>Caso não encontre o email, verifique na pasta de spam.</p></div>'.format(request.user.email)

	if request.GET.get('new_user', 'false') == 'true':
		context['account_verification_alert'] = SUCCESS_ACCOUNT_VERIFICATION
	
	return render(request, 'index.html', context)


def question(request, question_id):

	if Ban.objects.filter(ip=str(get_client_ip(request))).exists():
		return HttpResponse(Ban.objects.get(ip=get_client_ip(request)).message)

	try:
		q = Question.objects.get(id=question_id)
	except:
		# pergunta não encontrada:
		return HttpResponse('''<html>
			<head>
				<meta charset="utf-8">
				<meta name="viewport" content="width=device-width, initial-scale=1">
			</head>
			<body>
				<p>Essa pergunta não existe, talvez ela tenha sido apagada pelo criador da pergunta. <a href="/">Clique aqui</a> para voltar para a página inicial.</p>
			</body>
			</html>''')

	if request.method == 'POST':

		# para evitar respostas duplas:
		if Response.objects.filter(creator=UserProfile.objects.get(user=request.user), question=q).exists():
			return HttpResponse('OK')

		text = request.POST.get('response').replace('\r\n\r\n', '\n\n')
		if not is_a_valid_response(text):
			return HttpResponse('Proibido.')

		r = Response.objects.create(question=q, creator=UserProfile.objects.get(user=request.user), text=bs(text, 'lxml').text)

		''' Upload de imagens: '''
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			f = request.FILES['file']

			file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
			file_name += str(f)

			success = save_img_file(f, 'django_project/media/responses/' + file_name, (850, 850))
			if success: # TODO: mensagem caso não dê certo
				r.image = 'responses/' + file_name

			r.save()

		u = UserProfile.objects.get(user=request.user)
		u.total_points += 2
		u.save()

		# cria a notificação da resposta:
		n = Notification.objects.create(receiver=r.question.creator.user,
										type='question-answered')
		n.set_text(r.id)
		n.save()

		q.total_responses += 1
		q.save()

		json = {'answer_id': r.id}

		try:
			image_url = r.image.url
			json['has_image'] = True
			json['image_url'] = r.image.url
		except:
			json['has_image'] = False

		return JsonResponse(json)

	context = {'question': q,
			   'responses': Response.objects.filter(question=q).order_by('-pub_date').order_by('-total_likes')}

	if not request.user.is_anonymous:
		context['user_p'] = UserProfile.objects.get(user=request.user)
		context['answered'] = Response.objects.filter(creator=UserProfile.objects.get(user=request.user), question=q).exists()

	# questões recomendadas:
	qs = Question.objects.all().order_by('-pub_date')[:50]
	qs_list = list(qs)
	shuffle(qs_list)

	context['recommended_questions'] = qs_list[:20]

	return render(request, 'question.html', context)


def like(request):

    answer_id = request.GET.get('answer_id')
    print(request)

    r = Response.objects.get(id=answer_id)

    if r.creator.blocked_users.filter(username=request.user.username).exists():
        return HttpResponse('OK')

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

		subject = 'Asker.fun: confirmação de conta'
		message = '''Olá {}! Obrigado por criar uma conta no Asker.fun.

Para continuar, verifique seu endereço de email usando o link:
https://asker.pythonanywhere.com/account/verify?user={}&code={}

Obrigado e bem vindo(a)!
'''.format(username, sha256(bytes(username, 'utf-8')).hexdigest(), RANDOM_CODE)
		recipient = [email]

		print(send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False))

		return redirect(r)

	context = {
		'redirect': request.GET.get('redirect', '/'),
	}

	return render(request, 'signup.html', context)


def profile(request, username):
	u = UserProfile.objects.get(user=User.objects.get(username=username))
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
		if (timezone.now() - last_q.pub_date).seconds < 10:
			return HttpResponse('<p>Você deve esperar {} segundos para perguntar novamente.'.format(20 - (timezone.now() - last_q.pub_date).seconds))
	except:
		pass

	if request.method == 'POST':
		if request.POST.get('question') == '' or request.POST.get('question') == '.':
			return render(request, 'ask.html', {'error': '<p>Pergunta inválida.</p>'})

		description = bs(request.POST.get('description'), 'html.parser').text
		text = bs(request.POST.get('question'), 'html.parser').text
		description = replace_url_to_link(description) # transforma links (http, https, etc) em âncoras.

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

		u = UserProfile.objects.get(user=request.user)
		u.total_points += 1
		u.save()

		return redirect('/question/' + str(q.id))

	return render(request, 'ask.html', {'user_p': UserProfile.objects.get(user=request.user)})


def logout(request):
	django_logout(request)
	return redirect('/')


def test(request):
	return render(request, 'test.html')


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


def comments(request):
	response = Response.objects.get(id=request.GET.get('id'))
	page = int(request.GET.get('page'))
	p = Paginator(Comment.objects.filter(response=response), 3)

	json = {}
	json['comments'] = {}

	count = 1
	for comment in p.page(page):
		json['comments'][count] = {
			'username': comment.creator.username,
			'avatar': UserProfile.objects.get(user=comment.creator).avatar.url,
			'text': comment.text,
			'comment_id': comment.id,
		}
		count += 1

	if p.page(page).has_next():
		json['has_next'] = True
	else:
		json['has_next'] = False

	return JsonResponse(json)


'''
Faz um comentário para uma resposta.
'''
def comment(request):

	response_id = request.POST.get('response_id')
	text = request.POST.get('text')

	'''
	Verifica se está tudo certo para comentar:
	'''
	if request.method != 'POST' or (not is_a_valid_comment(text)):
		return HttpResponse('ERRO.')

	r = Response.objects.get(id=response_id)
	c = Comment.objects.create(response=r, creator=request.user, text=bs(text, "lxml").text) # cria o comentário da resposta.

	'''
	Cria a notificação do novo comentário:
	'''
	if request.user != r.creator.user:
		n = Notification.objects.create(receiver=r.creator.user, type='comment-in-response')
		n.set_text(r.id, comment_id=c.id)
		n.save()

	return redirect('/question/' + str(c.response.question.id))


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
	q = Question.objects.filter(creator=UserProfile.objects.get(user=request.user)).order_by('-pub_date')
	p = Paginator(q, 10)
	page = request.GET.get('q_page', 2)

	json = {
	}

	json['questions'] = {}

	count = 1
	for q in p.page(page):
		json['questions'][count] = {
			'text': q.text,
			'id': q.id,
			'naturalday': naturalday(q.pub_date),
		}
		count += 1

	json['has_next'] = p.page(page).has_next()

	return JsonResponse(json)


def get_more_responses(request):
	r = Response.objects.filter(creator=UserProfile.objects.get(user=request.user)).order_by('-pub_date')
	p = Paginator(r, 10)
	page = request.GET.get('r_page', 2)

	json = {
	}

	json['responses'] = {}

	count = 1
	for r in p.page(page):
		json['responses'][count] = {
			'text': r.text,
			'question_text': r.question.text,
			'question_id': r.question.id,
			'id': r.question.id,
		}
		count += 1

	json['has_next'] = p.page(page).has_next()

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
	if request.GET.get('type') == 'response':
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
	else:
		if UserProfile.objects.get(user=request.user).total_points < 300:
			return HttpResponse('OK')
		q = Question.objects.get(id=request.GET.get('id'))
		if q.reporters.filter(username=request.user.username).exists():
			return HttpResponse('OK')
		q.reports += 1
		q.reporters.add(request.user)
		q.save()

		if q.reports >= 3:
			q.delete()
	return HttpResponse('OK')


def edit_profile(request, username):

	if request.method == 'POST':
		if request.POST.get('type') == 'profile-pic':
			form = UploadFileForm(request.POST, request.FILES)
			if form.is_valid():
				f = request.FILES['file']
				file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
				file_name += str(f)

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
					return render(request, 'edit-profile.html', {'user_p': UserProfile.objects.get(user=User.objects.get(username=username)), 'password_display': 'block', 'invalid_password': ' is-invalid'})
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
	else:
		u_p.blocked_users.add(User.objects.get(username=username))
	return HttpResponse('OK')


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
	if len(text) > 5000:
		return False
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

		send_mail('Asker: trocar senha', 'Para alterar sua senha do Asker, use o link: https://asker.pythonanywhere.com/reset-password?type=get-form&username={}&code={}\nEntre em contato por este email caso ocorra algum erro.'.format(u_p.user.username, u_p.verification_code), EMAIL_HOST_USER, [u_p.user.email], fail_silently=False)

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
    if user.id != quser.id:
        return HttpResponse('Proibido.')
    if r.creator.user.id == quser.id:
        return HttpResponse('Proibido.')
    if q.best_answer is None:
        q.best_answer = answer_id
        q.save()
        n = Notification.objects.create(receiver=r.creator.user, type='got-best-answer', response=r)
        n.set_text(answer_id)
        n.save()
        rcuserp = UserProfile.objects.get(user=r.creator.user)
        quserp = UserProfile.objects.get(user=User.objects.get(id=quser.id))
        rcuserp.total_points += 2
        quserp.total_points += 1
        rcuserp.save()
        quserp.save()
    #else: # P/ testes rápidos - desfaz a MR
    #    q.best_answer = None
    #    q.save()

    return HttpResponse('OK')