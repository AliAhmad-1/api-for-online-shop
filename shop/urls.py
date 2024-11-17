from django.urls import path
from .views import *
urlpatterns = [

    path('products/',AllProductsView.as_view(),name='products'),
    path('products/<slug:category_slug>',AllProductsView.as_view(),name='products_by_category'),
    path('product/create/',ProductCreateView.as_view(),name='product_create'),
    path('categories/',AllCategoryView.as_view(),name='categories'),
    path('product/<uuid:pk>/',ProductDetailView.as_view(),name='product_detail'),
    path('cart/add/',CartAddProduct.as_view(),name='add_to_cart'),
    path('cart/remove/',CartRemoveProduct.as_view(),name='remove_product_cart'),
    path('cart/update/',CartUpdateQuantity.as_view(),name='update_quantity'),
    path('cart/',CartAllProducts.as_view(),name='cart_products'),
    path('order/create/',OrderCreateView.as_view(),name='create_order'),
    path('payment/process/',PaymentProcess.as_view(),name='process'),
    path('payment/webhook/', stripe_webhook, name='stripe-webhook'),
    path('apply/',CouponApplyView.as_view(),name='apply_coupon')
  
]
