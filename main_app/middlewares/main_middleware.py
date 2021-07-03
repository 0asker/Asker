from main_app.models import UserProfile
from django.utils import timezone

def main_middleware(get_response):
	def middleware(request):
		response = get_response(request)

		if request.user.is_authenticated:
			'''
			Seta o último visto:
			'''
			user_profile = UserProfile.objects.get(user=request.user)
			user_profile.last_seen = timezone.now()
			user_profile.save()

		return response
	return middleware
