'''
Este middleware trata a requisição de forma correta quando ela vem de uma notificação.
Por exemplo, veja este exemplo de notificação:
 X respondeu sua pergunta "Y?"
 
Então o usuário aperta em: "Y?", isso significa que ele leu a notificação,
e este middleare detecta isso e marca a notificação como "lida" (notification.read = True).
'''

from main_app.models import Notification

class NotificationMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response
    # One-time configuration and initialization.

  def __call__(self, request):
    '''
    Tratamento das notificações.
    '''
    notification_id = request.GET.get('n')
    
    if notification_id is not None:
      notification = Notification.objects.get(id=notification_id)
      notification.read = True
      notification.save()
    
    
    
    # Code to be executed for each request before
    # the view (and later middleware) are called.

    response = self.get_response(request)

    # Code to be executed for each request/response after
    # the view is called.

    return response
