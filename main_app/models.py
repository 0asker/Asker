from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import naturaltime


def make_embedded_content(text):
	urls = ('https://youtu.be/', 'youtube.com/watch?v=', 'https://voca.ro/', 'vocaroo.com/')
	if urls[0] in text or urls[1] in text:
		type = 0
		url_index = text.find(urls[0])
		if url_index == -1 or len(text) < url_index + len(urls[0]) + 11:
			type = 1
			url_index = text.find(urls[1])

		if len(text) < url_index + 11:
			return None
		url_index += len(urls[type])
		video_id = text[url_index:url_index + 11]
		if video_id:
			return """<div class="vid-container"><iframe src="https://www.youtube.com/embed/{}?rel=0" class="yt-vid" frameborder="0" allowfullscreen="allowfullscreen"></iframe></div>""".format(
				video_id)
	elif urls[2] in text or urls[3] in text:
		type = 2
		url_index = text.find(urls[2])
		if url_index == -1 or len(text) < url_index + len(urls[0]) + 4:
			type = 3
			url_index = text.find(urls[3])

		if len(text) < url_index + 4:
			return None
		url_end_index = text.find(' ', url_index)
		url_index += len(urls[type])
		if url_end_index > -1:
			audio_id = text[url_index:url_end_index].replace('"', '') # replace('"') p/ caso o link seja um src attr de uma tag <a> - necessário pois ha tags html guardadas formatadas no db
		else:
			audio_id = text[url_index:].replace('"', '') # replace('"') p/ caso o link seja um src attr de uma tag <a> - necessário pois ha tags html guardadas formatadas no db
		if audio_id:
			return """<div class="voc-container"><iframe width="300" height="60" src="https://vocaroo.com/embed/{}?autoplay=0" frameborder="0" allow="autoplay"></iframe><br></div>""".format(
				audio_id)


class UserProfile(models.Model):
	ip = models.TextField(null=True)
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	avatar = models.ImageField(default='avatars/default-avatar.png', blank=True)
	bio = models.TextField(max_length=400, blank=True)
	total_points = models.IntegerField(null=True, default=0, blank=True)
	total_views = models.IntegerField(default=0, blank=True) # total de visualizações desde o dia: 16/04/2021

	rank = models.IntegerField(default=-1, null=True, blank=True)

	blocked_users = models.ManyToManyField(User, related_name='blocked_by', blank=True) # usuários bloqueados pelo UserProfile.user atual.

	active = models.BooleanField(default=True) # conta está ativa ou não.
	verification_code = models.TextField(null=True) # código de verificação da conta.

	hide_activity = models.BooleanField(default=True)
	
	'''
	O campo abaixo vai ser usado para saber se
	o usuário já pegou ou não a recompensa por adicionar o site
	aos favoritos.
	'''
	message = models.TextField(null=True)

	def __str__(self):
		return self.user.username

	def total_questions(self):
		return Question.objects.filter(creator=self).count()

	def total_responses(self):
		return Response.objects.filter(creator=self).count()

	def points(self):
		total = self.total_responses() * 2
		total += self.total_questions()
		return total

class Question(models.Model):
	creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
	text = models.TextField()
	description = models.TextField(null=True)
	pub_date = models.DateTimeField(default=timezone.now)
	image = models.ImageField(null=True, blank=True)
	total_likes = models.IntegerField(default=0, null=True)
	total_responses = models.IntegerField(default=0)
	total_views = models.IntegerField(null=True, default=0)
	best_answer = models.IntegerField(blank=True, null=True) # ID da melhor resposta.

	def get_embedded_content(self):
		return make_embedded_content(self.description)

	def cut_description(self):
		d = self.description[:300]

		if len(d) == 300 and len(self.description) > 300:
			d += '<span style="color: #007bff; cursor: pointer;" onclick="show_more(this)">...Mostrar mais</span><span style="display: none;">{}</span> <span style="color: #007bff; cursor: pointer; display: none;" onclick="show_less(this)">Mostrar menos</span>'.format(self.description[300:])

		return d

	def may_choose_answer(self):
		if self.best_answer is None:
			if (timezone.now() - self.pub_date).total_seconds() > 3600: # TODO: fazer general rule pra quando é possivel escolher mr?
				return True
		return False

	def has_poll(self):
		return Poll.objects.filter(question=self).exists()

	def __str__(self):
	    return self.text


class Response(models.Model):
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
	text = models.TextField()
	pub_date = models.DateTimeField(default=timezone.now)
	likes = models.ManyToManyField(User)
	total_likes = models.IntegerField(default=0)
	image = models.ImageField(null=True, blank=True)

	def get_naturaltime(self):
		return correct_naturaltime(naturaltime(self.pub_date))

	def get_embedded_content(self):
		return make_embedded_content(self.text)
	
	def __str__(self):
		return self.text


class Comment(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    pub_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.text


class Notification(models.Model):
	receiver = models.ForeignKey(User, on_delete=models.CASCADE)
	type = models.TextField() # tipos: question-answered, like-in-response, comment-in-response, got-best-answer
	text = models.TextField(null=True)
	creation_date = models.DateTimeField(default=timezone.now)
	
	# os campos abaixo são usados caso a notificação seja do tipo like-in-response.
	liker = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='l') # quem deu o like
	response = models.ForeignKey(Response, on_delete=models.CASCADE, null=True, related_name='r') # qual é a resposta

	read = models.BooleanField(default=False) # notificação foi vista ou não pelo receiver (receiver clicou ou não na notificação, na verdade).

	def set_text(self, answer_id, comment_id=None):
		if self.type == 'like-in-response':
			self.text = '<p>Você recebeu um ❤️ na sua resposta <a href="/question/{}?n={}">"{}"</a></p>'.format(Response.objects.get(id=answer_id).question.id, self.id, Response.objects.get(id=answer_id).text)
		elif self.type == 'question-answered':
		    response = Response.objects.get(id=answer_id)
		    self.text = '<p><a href="/user/{}">{}</a> respondeu sua pergunta <a href="/question/{}?n={}">"{}"</a></p>'.format(response.creator.user.username, response.creator.user.username, response.question.id, self.id, response.question.text)
		elif self.type == 'comment-in-response':
			comment = Comment.objects.get(response=Response.objects.get(id=answer_id), id=comment_id)
			self.text = '<p><a href="/user/{}">{}</a> comentou na sua resposta na pergunta: <a href="/question/{}?n={}">"{}"</a></p>'.format(comment.creator.username, comment.creator.username, comment.response.question.id, self.id, comment.response.question.text)
		elif self.type == 'got-best-answer':
			response = Response.objects.get(id=answer_id)
			self.text = '<p>Sua resposta foi escolhida a melhor resposta da pergunta: <a href="/question/{}?n={}">"{}"</a></p>'.format(response.question.id, self.id, response.question.text)


class Ban(models.Model): # todos os IP's banidos:
	ip = models.TextField(null=False, primary_key=True)


class Poll(models.Model):
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	is_anonymous = models.BooleanField(default=True)
	multichoice = models.BooleanField()

	def may_vote(self):
		return (timezone.now() - self.question.pub_date).total_seconds() < 43200

class PollChoice(models.Model):
	poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
	text = models.TextField()
	votes = models.IntegerField(default=0)

class PollVote(models.Model):
	poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
	choice = models.ForeignKey(PollChoice, on_delete=models.CASCADE)
	voter = models.ForeignKey(User, on_delete=models.CASCADE)
