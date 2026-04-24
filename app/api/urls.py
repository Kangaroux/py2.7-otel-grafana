from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import url

from api import views

urlpatterns = [
    url(r'^products/$', views.list_products, name='list_products'),
    url(r'^products/(?P<product_id>\d+)/$', views.get_product, name='get_product'),
    url(r'^orders/$', views.list_orders, name='list_orders'),
    url(r'^orders/create/$', views.create_order, name='create_order'),
]
