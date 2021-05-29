from main_app.models import Ban
from django.http import HttpResponseForbidden

def request_filter(get_response):
	def middleware(request):

		user_ip = request.META['REMOTE_ADDR']

		try:
			ban = Ban.objects.get(ip=user_ip)
			return HttpResponseForbidden(ban.message)
		except:
			return get_response(request)

	return middleware
