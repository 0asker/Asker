from django_project import general_rules

from django import template

from main_app.models import User, UserProfile, Question, Response, Comment

register = template.Library()

@register.simple_tag
def MINIMUM_POINTS_FOR_POSTING_IMAGES():
	return general_rules.MINIMUM_POINTS_FOR_POSTING_IMAGES


@register.simple_tag
def total_answers(qid):
	try:
		return Response.objects.filter(question=Question.objects.get(id=qid)).count()
	except:
		return 'null'


@register.simple_tag
def answered(username, qid):
	return Response.objects.filter(creator=UserProfile.objects.get(user=User.objects.get(username=username)), question=Question.objects.get(id=qid)).exists()


@register.simple_tag
def answer(username, qid):
	try:
		text = Response.objects.get(creator=UserProfile.objects.get(user=User.objects.get(username=username)), question=Question.objects.get(id=qid)).text
	except:
		text = 'null'
	if len(text) > 77:
		text = text[0:77] + '...'
	return text


@register.filter(name='total_likes')
def total_likes(response_id):
    return Response.objects.get(id=response_id).likes.all().count()


@register.filter(name='like_or_not')
def like_or_not(response_id, username):
    r = Response.objects.get(id=response_id)

    if r.likes.filter(username=username).exists():
        return 'red-heart.png'
    return 'white-heart.png'


@register.filter(name='pull_best_answer')
def pull_best_answer(responses):
    if not responses:
        return responses
    best_answer = responses[0].question.best_answer
    if best_answer is not None:
        responses = sorted(responses, key=lambda response: response.id != best_answer)
    return responses


@register.filter(name='total_comments')
def total_comments(response_id):
    return Comment.objects.filter(response=Response.objects.get(id=response_id)).count()


@register.filter(name='last_response_pub_date')
def last_response_pub_date(question_id):
    q = Question.objects.get(id=question_id)
    return Response.objects.filter(question=q).order_by('-pub_date')[0].pub_date


@register.filter(name='last_response')
def last_response(question_id):
	from django.contrib.humanize.templatetags.humanize import naturaltime
	from ..models import correct_naturaltime
	try:
		r = Response.objects.filter(question=Question.objects.get(id=question_id)).order_by('-pub_date')
		return 'respondida {} por <a href="/user/{}">{}</a>'.format(correct_naturaltime(naturaltime(r[0].pub_date)), r[0].creator.user.username, r[0].creator.user.username)
	except:
		return ''


@register.filter(name='cut_description')
def cut_description(description):
	if len(description) < 300:
		return description

	pt1 = description[:300]
	pt2 = description[300:]
	s=''
	if len(pt2) > 0:
		s = '{}<span style="color: #007bff; cursor: pointer;" onclick="this.nextSibling.style.display=`inline`; this.style.display=`none`; this.nextSibling.nextSibling.style.display=`inline`">...Mostrar mais</span><span style="display: none">{}</span><span style="display: none; color: #007bff; cursor: pointer;" onclick="this.previousSibling.style.display=`none`; this.style.display=`none`; this.previousSibling.previousSibling.style.display=`inline`"> Mostrar menos</span>'.format(pt1, pt2)
	return s.replace('\n', '<br>')


@register.filter(name='blocked')
def blocked(username, username2):
	u_p = UserProfile.objects.get(user=User.objects.get(username=username))

	if u_p.blocked_users.filter(username=username2).exists():
		return 'Bloqueado'
	return 'Bloquear'
