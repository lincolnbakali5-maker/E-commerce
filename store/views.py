from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import Product


def _get_cart(request):
    return request.session.setdefault('cart', {})


def _cart_items(request):
    cart = _get_cart(request)
    items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            continue

        quantity = int(quantity)
        line_total = product.price * quantity
        items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
        })
        total += line_total

    return items, total


def _cart_quantity(request):
    return sum(int(quantity) for quantity in _get_cart(request).values())


def _ensure_sample_products():
    if Product.objects.exists():
        return

    sample_products = [
        Product(
            name='Classic Baseball Hat',
            slug='classic-baseball-hat',
            description='A comfortable, adjustable baseball hat for everyday wear.',
            price=19.99,
            featured=True,
            image_url='https://via.placeholder.com/500x300/1c4364/ffffff?text=Baseball+Hat',
        ),
        Product(
            name='Canvas Bucket Hat',
            slug='canvas-bucket-hat',
            description='A lightweight canvas bucket hat with a wide brim.',
            price=24.99,
            featured=True,
            image_url='https://via.placeholder.com/500x300/4b4f72/ffffff?text=Bucket+Hat',
        ),
        Product(
            name='Wool Fedora',
            slug='wool-fedora',
            description='A stylish wool fedora with a classic, structured fit.',
            price=34.99,
            featured=False,
            image_url='https://via.placeholder.com/500x300/854e3f/ffffff?text=Wool+Fedora',
        ),
        Product(
            name='Sun Visor Cap',
            slug='sun-visor-cap',
            description='A sporty visor that keeps your face shaded and cool.',
            price=14.99,
            featured=False,
            image_url='https://via.placeholder.com/500x300/2d6a4f/ffffff?text=Visor+Cap',
        ),
    ]

    Product.objects.bulk_create(sample_products)


def home(request):
    _ensure_sample_products()
    featured_products = Product.objects.filter(available=True, featured=True)
    if not featured_products.exists():
        featured_products = Product.objects.filter(available=True)[:4]

    context = {
        'featured_products': featured_products,
        'cart_count': _cart_quantity(request),
    }
    return render(request, 'store/home.html', context)


def product_list(request):
    products = Product.objects.filter(available=True)
    context = {
        'products': products,
        'cart_count': _cart_quantity(request),
    }
    return render(request, 'store/products.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    context = {
        'product': product,
        'cart_count': _cart_quantity(request),
    }
    return render(request, 'store/product_detail.html', context)


def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('store:product_list')

    product = get_object_or_404(Product, pk=product_id, available=True)
    cart = _get_cart(request)
    quantity = int(request.POST.get('quantity', 1))

    cart[str(product_id)] = cart.get(str(product_id), 0) + max(quantity, 1)
    request.session.modified = True
    messages.success(request, f'Added {product.name} to your cart.')
    return redirect('store:cart')


def cart_view(request):
    if request.method == 'POST':
        cart = _get_cart(request)
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                product_id = key.split('_', 1)[1]
                try:
                    quantity = int(value)
                except ValueError:
                    quantity = 1
                if quantity > 0:
                    cart[product_id] = quantity
                else:
                    cart.pop(product_id, None)
        request.session.modified = True
        messages.success(request, 'Your cart has been updated.')
        return redirect('store:cart')

    items, total = _cart_items(request)
    context = {
        'items': items,
        'total': total,
        'cart_count': _cart_quantity(request),
    }
    return render(request, 'store/cart.html', context)


def checkout(request):
    items, total = _cart_items(request)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()

        if not name or not email:
            messages.error(request, 'Please enter your full name and a valid email address.')
            return redirect('store:cart')

        request.session['cart'] = {}
        request.session.modified = True

        context = {
            'customer_name': name,
            'total': total,
            'cart_count': 0,
        }
        return render(request, 'store/order_complete.html', context)

    return redirect('store:cart')
