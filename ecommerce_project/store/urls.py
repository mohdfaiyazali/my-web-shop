from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='home'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('add/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('increase/<int:id>/', views.increase_quantity, name='increase_qty'),
    path('decrease/<int:id>/', views.decrease_quantity, name='decrease_qty'),
    path('remove/<int:id>/', views.remove_item, name='remove_item'),

    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='order_history'),

    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.payment_success, name='success'),
    path('payment-success/', views.payment_success, name='payment_success'),
]
