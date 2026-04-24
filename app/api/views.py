from __future__ import absolute_import, print_function, unicode_literals

import json

from django.http import JsonResponse
from opentelemetry import trace

from api.models import Product, Order

tracer = trace.get_tracer(__name__)


def list_products(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    products = list(
        Product.objects.all().values('id', 'name', 'price', 'description', 'created_at')
    )
    for p in products:
        p['price'] = str(p['price'])
        p['created_at'] = p['created_at'].isoformat()
    return JsonResponse({'products': products})


def get_product(request, product_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    data = {
        'id': product.id,
        'name': product.name,
        'price': str(product.price),
        'description': product.description,
        'created_at': product.created_at.isoformat(),
    }
    return JsonResponse({'product': data})


def create_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    product_id = body.get('product_id')
    quantity = body.get('quantity', 1)
    notes = body.get('notes', '')

    if not product_id:
        return JsonResponse({'error': 'product_id is required'}, status=400)

    with tracer.start_as_current_span("validate_and_create_order") as span:
        span.set_attribute("order.product_id", product_id)
        span.set_attribute("order.quantity", quantity)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            span.set_attribute("order.error", "product_not_found")
            return JsonResponse({'error': 'Product not found'}, status=404)

        span.add_event("order_validated", {"product_id": product_id})

        order = Order.objects.create(
            product=product,
            quantity=quantity,
            notes=notes,
        )

        span.add_event("order_created", {"order_id": order.id})

    data = {
        'id': order.id,
        'product_id': order.product_id,
        'product_name': order.product.name,
        'quantity': order.quantity,
        'notes': order.notes,
        'created_at': order.created_at.isoformat(),
    }
    return JsonResponse({'order': data}, status=201)


def list_orders(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    orders = []
    for order in Order.objects.select_related('product').all():
        orders.append({
            'id': order.id,
            'product_id': order.product_id,
            'product_name': order.product.name,
            'quantity': order.quantity,
            'notes': order.notes,
            'created_at': order.created_at.isoformat(),
        })
    return JsonResponse({'orders': orders})
