from django.contrib import admin
from . import models
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin


# Register your models here.


@admin.register(models.User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'in_stock', 'price',)
    list_filter = ('active', 'in_stock', 'date_updated',)
    list_editable = ('in_stock',)
    search_fields = ('name',)
    prepopulated_fields = {"slug": ('name',)}


admin.site.register(models.Product, ProductAdmin)


class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    list_filter = ('active',)
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}
    # autocomplete_fields = ('tags',)


admin.site.register(models.ProductTag, ProductTagAdmin)


class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_tag', 'product_name',)
    readonly_fields = ('thumbnail',)
    search_fields = ('product__name',)

    def thumbnail_tag(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="%s"/>' % obj.thumbnail.url
            )
        return '-'

    thumbnail_tag.short_description = "Thumbnail"

    def product_name(self, obj):
        return obj.product.name


admin.site.register(models.ProductImage, ProductImageAdmin)
