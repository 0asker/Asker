from main_app.models import Ban
from django.http import HttpResponseForbidden

def get_client_ip(request):
  x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
  if x_forwarded_for:
    ip = x_forwarded_for.split(',')[0]
  else:
    ip = request.META.get('REMOTE_ADDR')
  return ip

def ip_filter(get_response):
  def middleware(request):
    response = get_response(request)
    
    user_ip = get_client_ip(request)
    
    for ban in Ban.objects.all():
      if ban.ip == user_ip:
        return HttpResponseForbidden(ban.message)
    
    return response
  return middleware
