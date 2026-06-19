from django.contrib.auth import get_user_model

class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        User = get_user_model()
        user = User.objects.filter(username='Hafiz').first()
        if user:
            request.user = user
        response = self.get_response(request)
        return response
