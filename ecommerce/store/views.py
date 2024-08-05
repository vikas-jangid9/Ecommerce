from django.shortcuts import render
from django.http import JsonResponse
from .models import *
import json
import datetime
from .utils import cartData, guestOrder

def store(request):
    data = cartData(request)

    cartItem = data['cartItem']

    products = Product.objects.all()
    context ={'products':products, 'cartItem':cartItem, 'shipping':False}
    return render(request, 'store/store.html', context)

def cart(request):
    data = cartData(request)

    cartItem = data['cartItem']
    order = data['order']
    items = data['items']

    context ={'items':items, 'order':order, 'cartItem':cartItem}
    return render(request, 'store/cart.html', context)

def checkout(request):
    data= cartData(request)

    cartItem = data['cartItem']
    order = data['order']
    items = data['items']
    
    context ={'items':items, 'order':order, 'cartItem':cartItem}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    try:
        data = json.loads(request.body)
        productId = data['productId']
        action = data['action']

        customer = request.user.customer
        product = Product.objects.get(id=productId)
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

        if action == 'add':
            orderItem.quantity = (orderItem.quantity + 1)
        elif action == 'remove':
            orderItem.quantity = (orderItem.quantity - 1)

        orderItem.save()

        if orderItem.quantity <= 0:
            orderItem.delete()
        return JsonResponse('Item was added', safe=False)
    except json.JSONDecodeError as e:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': 'Missing required field'}, status=400)
    
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
       

        if order.shipping == True:
            ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
            )


    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id


    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
        customer=customer,
        order=order,
        address=data['shipping']['address'],
        city=data['shipping']['city'],
        state=data['shipping']['state'],
        zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment complete', safe=False)