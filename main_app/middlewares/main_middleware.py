from main_app.models import UserStatus
from django.utils import timezone

def main_middleware(get_response):
	def middleware(request):
		response = get_response(request)

		if request.user.is_authenticated:
			'''
			Seta o último visto:
			'''
			us = UserStatus.objects.get(user=request.user)
			us.last_seen = timezone.now()
			us.save()

		return response
	return middleware
