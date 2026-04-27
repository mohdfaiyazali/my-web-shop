from django import forms
from .models import Product, Cart, CartItem

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description','image','stock']


