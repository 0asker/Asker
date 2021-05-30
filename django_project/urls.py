"""django_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from main_app import views

urlpatterns = [
	path('', views.index, name='index'),
	path('news', views.index, name='index'),
	path('popular', views.index, name='index'),
	path('question/<int:question_id>', views.question, name='question'),
	path('pjax-questions', views.pjax_questions, name='pjax_questions'),
	path('answer/like', views.like, name='like'), # quando uma resposta recebe um like, é usado esse padrão de URL.
	path('answer/choose', views.choose_best_answer, name="choose_best_answer"),
	path('delete_response', views.delete_response, name='delete_response'), # esse padrão de URL é usado para deletar respostas.
	path('user/<str:username>', views.profile, name='profile'),
	path('user/<str:username>/edit', views.edit_profile, name='edit_profile'),
	path('user/<str:username>/block', views.block, name='block'), # esse padrão de URL é usado para um usuário bloquear outro.
	path('ask', views.ask, name='ask'),
	path('signin', views.signin, name='signin'),
	path('signup', views.signup, name='signup'),
	path('logout', views.logout, name='logout'),
	path('notifications', views.notification, name='notification'),
	path('delete_question', views.deleteQuestion, name='deleteQuestion'),
  path('test', views.test, name='test'),
	path('delete_comment', views.delete_comment, name='delete_comment'),
	path('comments', views.comments, name='comments'), # esse padrão de URL é usado para obter comentários de respostas. Os comentários são retornados no formato JSON.
	path('comment', views.comment, name='comment'), # esse padrão de URL é usado para fazer um comentário em uma resposta (postar um comentário).
	path('rank', views.rank, name='rank'),
	path('edit-response', views.edit_response, name='edit_response'), # padrão de URL usado para editar respostas.
	path('report', views.report, name='report'), # esse padrão de URL é usado para reportar uma pergunta.
	path('account/verify', views.account_verification, name='account_verification'), # padrão de URL usado para verificar o email de uma conta após a sua criação.
	path('user/<str:username>/info', views.user_info, name='user_info'),
	path('reset-password', views.reset_password, name='reset_password'), # padrão de URL usado para alterar a senha.
	path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'))),
	path('update-popular-questions', views.update_popular_questions, name='update_popular_questions'),
	path('get_more_questions', views.get_more_questions, name='get_more_questions'),
	path('get_more_responses', views.get_more_responses, name='get_more_responses'),
	path('save_answer', views.save_answer, name='save_answer'),
	path('delete-account', views.delete_account, name='delete_account'),
  path('rules', views.rules, name='rules'),
  path('change-email', views.change_email, name='change_email'),
  path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
