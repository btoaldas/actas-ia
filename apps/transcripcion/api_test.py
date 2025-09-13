from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET"])
def api_test_conectividad(request):
    """
    API simple para probar conectividad sin autenticación
    """
    return JsonResponse({
        'status': 'ok',
        'mensaje': 'API funcionando correctamente',
        'timestamp': '2025-09-13T09:30:00Z'
    })