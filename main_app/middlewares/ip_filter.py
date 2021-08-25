from django.http import HttpResponseForbidden
from ..models import Ban

def get_client_ip(request):
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0]
	else:
		ip = request.META.get('REMOTE_ADDR')
	return ip

class IpFilter:
	def __init__(self, get_response):
		self.get_response = get_response
		# One-time configuration and initialization.

	def __call__(self, request):
		# Code to be executed for each request before
		# the view (and later middleware) are called.
		
		if Ban.objects.filter(ip=get_client_ip(request)).exists():
			return HttpResponseForbidden('Proibido.')

		# Code to be executed for each request/response after
		# the view is called.

		return self.get_response(request)
