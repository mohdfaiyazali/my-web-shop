from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import razorpay

from .models import Product, Cart, CartItem, Order, OrderItem


# 🛍️ PRODUCT VIEWS
def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'store/product_detail.html', {'product': product})


# 🛒 CART VIEWS
@login_required
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        item.quantity += 1
        item.save()

    return redirect('view_cart')


@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)

    total = sum(item.product.price * item.quantity for item in items)

    return render(request, 'store/cart.html', {
        'items': items,
        'total': total
    })


@login_required
def increase_quantity(request, id):
    item = get_object_or_404(CartItem, id=id)
    item.quantity += 1
    item.save()
    return redirect('view_cart')


@login_required
def decrease_quantity(request, id):
    item = get_object_or_404(CartItem, id=id)

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()

    return redirect('view_cart')


@login_required
def remove_item(request, id):
    item = get_object_or_404(CartItem, id=id)
    item.delete()
    return redirect('view_cart')


# 💳 RAZORPAY CHECKOUT (MAIN FLOW)
@login_required
def checkout(request):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)

    if not items:
        return redirect('view_cart')

    total = sum(item.product.price * item.quantity for item in items)
    amount = int(total * 100)  # Razorpay uses paise

    # Create Razorpay Order
    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    # Save Order in DB
    Order.objects.create(
        user=request.user,
        amount=amount,
        razorpay_order_id=payment['id'],
        status="Pending"
    )

    return render(request, "store/checkout.html", {
        "payment": payment,
        "key_id": settings.RAZORPAY_KEY_ID
    })

# 🔐 PAYMENT VERIFICATION
@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        params_dict = {
            'razorpay_order_id': request.POST.get('razorpay_order_id'),
            'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
            'razorpay_signature': request.POST.get('razorpay_signature')
        }

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            # ✅ Verify payment signature
            client.utility.verify_payment_signature(params_dict)

            # ✅ Get order safely
            order = Order.objects.get(
                razorpay_order_id=params_dict['razorpay_order_id']
            )

            # ✅ Store payment ID + update status
            order.razorpay_payment_id = params_dict['razorpay_payment_id']
            order.status = "Success"
            order.save()

            # ✅ Get user's cart
            cart = Cart.objects.filter(user=order.user).first()

            if cart:
                items = CartItem.objects.filter(cart=cart)

                # ✅ Move items → OrderItems (avoid duplicates)
                if not order.items.exists():
                    for item in items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity
                        )

                # ✅ Clear cart
                items.delete()

            return render(request, "store/success.html")

        except Exception as e:
            print("❌ Payment verification failed:", e)
            return render(request, "store/failure.html")

    return redirect('product_list')

# 📦 ORDER HISTORY
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-id')

    return render(request, 'store/order_history.html', {
        'orders': orders
    })


# ✅ SIMPLE SUCCESS PAGE
def order_success(request):
    return render(request, 'store/order_success.html')