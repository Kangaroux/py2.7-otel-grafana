from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import url, include
from django.http import JsonResponse


def root_view(request):
    return JsonResponse({
        'message': 'Welcome to the Django OTel PoC API',
        'endpoints': {
            'products': '/api/products/',
            'product_detail': '/api/products/<id>/',
            'orders': '/api/orders/',
            'create_order': '/api/orders/create/',
        },
    })


urlpatterns = [
    url(r'^$', root_view, name='root'),
    url(r'^api/', include('api.urls')),
]
