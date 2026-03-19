class NoCacheAuthMiddleware:
    """
    Agrega headers de no-cache a todas las respuestas de páginas autenticadas.
    Esto previene que el botón "atrás" del navegador muestre páginas
    privadas después de cerrar sesión.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Aplicar solo a páginas que requieren auth (no a estáticos ni landing)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
