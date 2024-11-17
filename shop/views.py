from django.shortcuts import render
from rest_framework.generics import ListAPIView,ListCreateAPIView,RetrieveAPIView
from .serializers import *
from .models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .cart import Cart
import json

from .tasks import order_created
from django.conf import settings
import stripe
from decimal import Decimal
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone




class AllCategoryView(ListCreateAPIView):
    serializer_class=CategorySerializer
    queryset=Category.objects.all()

class AllProductsView(ListAPIView):
    serializer_class=ProductSerializer


    def get_queryset(self):
        category_slug=self.kwargs.get('category_slug')
        category=None
        products=Product.objects.filter(available=True)
        if category_slug:
            category=get_object_or_404(Category,slug=category_slug)
            products=products.filter(category=category)
        return products
    
class ProductCreateView(APIView):
    def post(self,request,format=None):
        serializer=ProductSerializer(data=request.data,context={'data':request.data})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'msg':'your product created successfully'},status=status.HTTP_201_CREATED)

class ProductDetailView(RetrieveAPIView):
    serializer_class=ProductUpdateSerializer
    queryset=Product.objects.all()
    def get_serializer_context(self):
  
        cart=Cart(self.request)
        context=super().get_serializer_context()
        context["cart"] = cart

        return context




class CartAddProduct(APIView):
    
    def post(self,request,format=None):
        cart=Cart(request)
        product_id=request.data.get('product_id')
        quantity=int(request.data.get('quantity',1))
        product=get_object_or_404(Product,id=product_id)
        cart.add(product=product,quantity=quantity)
        
        return Response({'msg':'Product added to cart successfully'},status=status.HTTP_201_CREATED)

class CartRemoveProduct(APIView):
    def delete(self,request,format=None):
        cart=Cart(request)
        product_id=request.data.get('product_id')
        product=get_object_or_404(Product,id=product_id)
        cart.remove(product=product)
        return Response({'msg':'Product removed from cart successfully'},status=status.HTTP_200_OK)

class CartUpdateQuantity(APIView):
    def put(self,request,format=True):
        cart=Cart(request)
        product_id=request.data.get('product_id')
        print(product_id)
        quantity=int(request.data.get('quantity',None))
        product=get_object_or_404(Product,id=product_id)
        cart.add(product=product,quantity=quantity,override_quantity=True)
        return Response({'msg':'Product quantity updated successfully'},status=status.HTTP_200_OK)

class CartAllProducts(APIView):
    def get(self,request,format=True):
        cart=Cart(request)
        cart_items=[]
        
        for item in cart:
            product_data={}
            product_data['product'] = ProductCartSerializer(item['product']).data
            product_data['quantity'] = item['quantity']
            product_data['total_price_for_product'] = str(item['total_price'])  # Convert to string if necessary
            cart_items.append(product_data)
        cart_items.append({'total_price':cart.get_total_price()})
        if  cart.coupon:
            cart_items.append({f" 'SUMMER' coupon ({cart.coupon.discount}% off)":cart.get_discount()})
            cart_items.append({'total_price_after_discount':cart.get_total_price_after_discount()})
            
        return Response(cart_items,status=status.HTTP_200_OK)




class OrderCreateView(APIView):
    def post(self,request,format=None):
        cart=Cart(request)
        serializer=OrderSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        if cart.coupon:
            serializer.validated_data['coupon']=cart.coupon
            serializer.validated_data['discount']=cart.coupon.discount
        order=serializer.save()
        for item in cart:
            OrderItem.objects.create(order=order,product=item['product'],price=item['price'],quantity=item['quantity'])
        cart.clear()
        order_created.delay(order.id)
        request.session['order_id']=order.id
        return Response(serializer.data,status=status.HTTP_201_CREATED)


stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION
class PaymentProcess(APIView):
    def post(self,request,format=None):
        order_id = request.session.get('order_id')
        order=get_object_or_404(Order,id=order_id)
        session_data = {
            'mode': 'payment',
            'client_reference_id': order.id,
            'success_url':settings.SITE_URL + '?success=true',
            'cancel_url': settings.SITE_URL + '?canceled=true',
            'line_items': []
        }

        for item in order.items.all():
            session_data['line_items'].append(
            {
            'price_data':{'unit_amount':int(item.price * Decimal('100')) , 'currency':'usd' ,'product_data':{'name':item.product.name}},
            'quantity':item.quantity
            
            })
            
        # Stripe coupon
        if order.coupon:
            stripe_coupon = stripe.Coupon.create(
                name=order.coupon.code,
                percent_off=order.discount,
                duration='once',
            )
            session_data['discounts'] = [{'coupon': stripe_coupon.id}]

        # create Stripe checkout session
        session = stripe.checkout.Session.create(**session_data)
        return Response({'url': session.url}, status=status.HTTP_303_SEE_OTHER)

        


@csrf_exempt
def stripe_webhook(request):

    payload = request.body

    sig_header = request.META['HTTP_STRIPE_SIGNATURE']


    event = None
    try:
        event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
    # Invalid payload
        return Response(status=400)
    except stripe.error.SignatureVerificationError as e:
    # Invalid signature
        return Response(status=400)
    if event.type == 'checkout.session.completed':
        session = event.data.object
    if (session.mode == 'payment' and session.payment_status == 'paid'):

        try:
            order = Order.objects.get(
            id=session.client_reference_id
            )
        except Order.DoesNotExist:
            return HttpResponse(status=404)
    # mark order as paid
    order.paid = True
    order.save()
    return HttpResponse(status=200)






class CouponApplyView(APIView):
    def post(self,request,format=None):
        now=timezone.now()
        serializer=CouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code=serializer.data['code']
        coupon=get_object_or_404(Coupon,code=code,valid_from__lte=now,valid_to__gte=now,active=True)
        request.session['coupon_id'] = coupon.id
        return Response({'status':'Ok'},status=status.HTTP_200_OK)