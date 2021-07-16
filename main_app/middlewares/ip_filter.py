from django.http import HttpResponse

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

		ip = get_client_ip(request)
		
		if ip == '177.84.47.47' or ip == '104.244.72.168' or ip == '109.70.100.25' or ip == '179.176.97.151' or ip == '191.33.210.17':
			return HttpResponse('')

		response = self.get_response(request)

		# Code to be executed for each request/response after
		# the view is called.

		return response
