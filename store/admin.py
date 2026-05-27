from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'available', 'featured')
    list_filter = ('available', 'featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
