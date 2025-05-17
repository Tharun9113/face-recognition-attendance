from django.shortcuts import redirect

class AdminPasswordResetMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is an admin password reset request
        if request.path.startswith('/admin/password_reset'):
            return redirect('password_reset')
        
        response = self.get_response(request)
        return response 