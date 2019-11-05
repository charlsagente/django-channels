from . import models
from django.utils.html import format_html
from datetime import datetime, timedelta
import logging
from django.contrib import admin
from django.contrib.auth.admin import (
    UserAdmin as DjangoUserAdmin
)
from django.db.models.functions import TruncDay
from django.db.models import Avg, Count, Min, Sum
from django.urls import path
from django.template.response import TemplateResponse
from django import forms

logger = logging.getLogger(__name__)


# Register your models here.


def make_active(self, request, queryset):
    queryset.update(active=True)


make_active.short_description = "Mark selected items as active"


def make_inactive(self, request, queryset):
    queryset.update(active=False)


make_inactive.short_description = (
    "Mark selected items as inactive"
)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'in_stock', 'price',)
    list_filter = ('active', 'in_stock', 'date_updated',)
    list_editable = ('in_stock',)
    search_fields = ('name',)
    prepopulated_fields = {"slug": ('name',)}
    autocomplete_fields = ("tags",)
    actions = [make_active, make_inactive]

    # Slug is an important field for our site, it is used in
    # all the product URLS. We want to limit the ability to
    # change this only ot the owners of the company.
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return list(self.readonly_fields) + ["slug", "name"]

    # This is required for get_readonly_fields to work
    def get_prepopulated_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.prepopulated_fields
        else:
            return {}


class DispatchersProductAdmin(ProductAdmin):
    readonly_fields = ("description", "price", "tags", "active")
    prepopulated_fields = {}
    autocomplete_fields = ()


class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    list_filter = ('active',)
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}

    # autocomplete_fields = ('tags',)

    # tag slugs also appear in urls, therefore it is a
    # property only owners can change
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return list(self.readonly_fields) + ["slug", "name"]

    # This is required for get_readonly_fields to work
    def get_prepopulated_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.prepopulated_fields
        else:
            return {}


class UserAdmin(DjangoUserAdmin):
    # User model has a lot of fields, which is why we are
    # reorganizing them for readability
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
        (
            "important dates",
            {"fields": ("last_login", "date_joined")},
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


class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "name",
        "address1",
        "address2",
        "city",
        "country",
    )
    readonly_fields = ("user",)


class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_tag', 'product_name',)
    readonly_fields = ('thumbnail',)
    search_fields = ('product__name',)

    # this function returns HTML for the first column defined
    # in the list_display propery above
    def thumbnail_tag(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="%s"/>' % obj.thumbnail.url
            )
        return '-'

    # This defines the column name for the list_display
    thumbnail_tag.short_description = "Thumbnail"

    def product_name(self, obj):
        return obj.product.name


class BasketLineInline(admin.TabularInline):
    model = models.BasketLine
    raw_id_fields = ("product",)


class BasketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "count")
    list_editable = ("status",)
    list_filter = ("status",)
    inlines = (BasketLineInline,)


class OrderLineInline(admin.TabularInline):
    model = models.OrderLine
    raw_id_fields = ("product",)


class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_editable = ("status",)
    list_filter = ("status", "shipping_country", "date_added")
    inlines = (OrderLineInline,)
    fieldsets = (
        (None, {"fields": ("user", "status")}),
        (
            "Billing info",
            {
                "fields": (
                    "billing_name",
                    "billing_address1",
                    "billing_address2",
                    "billing_zip_code",
                    "billing_city",
                    "billing_country",
                )
            },
        ),
        (
            "Shipping info",
            {
                "fields": (
                    "shipping_name",
                    "shipping_address1",
                    "shipping_address2",
                    "shipping_zip_code",
                    "shipping_city",
                    "shipping_country",
                )
            },
        ),
    )


# Employees need a custom version of the order views because
# they are not allowed to change products already purchased
# without adding and removing lines

class CentralOfficeOrderLineInLine(admin.TabularInline):
    model = models.OrderLine
    readonly_fields = ("product",)


class CentralOfficeOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_editable = ("status",)
    readonly_fields = ("user",)
    list_filter = ("status", "shipping_country", "date_added",)
    inlines = (CentralOfficeOrderLineInLine,)
    fieldsets = (
        (None, {"fields": ("user", "status")}),
        (
            "Billing info",
            {
                "fields": (
                    "billing_name",
                    "billing_address1",
                    "billing_address2",
                    "billing_zip_code",
                    "billing_city",
                    "billing_country",
                )
            },
        ),
        (
            "Shipping info",
            {
                "fields": (
                    "shipping_name",
                    "shipping_address1",
                    "shipping_address2",
                    "shipping_zip_code",
                    "shipping_city",
                    "shipping_country",
                )
            },
        ),
    )


# Dispatchers do not need to see the billing address in the fields

class DispatchersOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "shipping_name",
        "date_added",
        "status",
    )
    list_filter = ("status", "shipping_country", "date_added")
    inlines = (CentralOfficeOrderLineInLine,)
    fieldsets = (
        (
            "Shipping info",
            {
                "fields": (
                    "shipping_name",
                    "shipping_address1",
                    "shipping_address2",
                    "shipping_zip_code",
                    "shipping_city",
                    "shipping_country",
                ),
            },
        ),
    )

    # Dispatchers are onlyh allowed to see orders that
    # are ready to be shipped
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=models.Order.PAID)


# The class below will pass to the Django Admin templates a couple
# of extra values that represent colors of headings

class ColoredAdminSite(admin.sites.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        context["site_header_color"] = getattr(
            self, "site_header_color", None
        )
        context["module_caption_color"] = getattr(
            self, "module_caption_color", None
        )
        return context


class PeriodSelectForm(forms.Form):
    PERIODS = ((30, "30 days"), (60, "60 days"), (90, "90 days"))
    period = forms.TypedChoiceField(
        choices=PERIODS, coerce=int, required=True
    )


# The following will add reporting views to the list of
# available urls and will list them from the index page
class ReportingColoredAdminSite(ColoredAdminSite):
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "orders_per_day/",
                self.admin_view(self.orders_per_day),
            ),
            path(
                "most_bought_products/",
                self.admin_view(self.most_bought_products),
                name="most_bought_products",
            ),
        ]
        return my_urls + urls

    def most_bought_products(self, request):
        if request.method == "POST":
            form = PeriodSelectForm(request.POST)
            if form.is_valid():
                days = form.cleaned_data["period"]
                starting_day = datetime.now() - timedelta(
                    days=days)
                data = (
                    models.OrderLine.objects.filter(
                        order__date_added__gt=starting_day
                    )
                        .values("product__name")
                        .annotate(c=Count("id"))
                )
                logger.info(
                    "most_bought_products query: %s", data.query
                )
                labels = [x["product__name"] for x in data]
                values = [x["c"] for x in data]
        else:
            form = PeriodSelectForm()
            labels = None
            values = None

        context = dict(
            self.each_context(request),
            title="Most bought products",
            form=form,
            labels=labels,
            values=values,
        )
        return TemplateResponse(
            request, "most_bought_products.html", context
        )

    def orders_per_day(self, request):
        starting_day = datetime.now() - timedelta(days=180)
        order_data = (
            models.Order.objects.filter(
                date_added__gt=starting_day
            ).annotate(
                day=TruncDay("date_added")
                # Creates a temporary/annotated day field, populating it with data based on the date_added field
            ).values(
                "day"  # Uses the new day field as unit of aggregation
            ).annotate(
                c=Count("id")  # Counts orders for specific days
            )
        )  # The query includes two annotate() calls. The first acts on all rows in the order table, the second acts on the
        # result of the group_by clause, which is generated by values()
        labels = [
            x["day"].strftime("%Y-%m-%d") for x in order_data]
        values = [x["c"] for x in order_data]
        context = dict(
            self.each_context(request),
            title="Orders per day",
            labels=labels,
            values=values,
        )
        return TemplateResponse(
            request, "orders_per_day.html", context
        )

    def index(self, request, extra_context=None):
        reporting_pages = [
            {
                "name": "Orders per day",
                "link": "orders_per_day/",
            },
            {
                "name": "Most bought products",
                "link": "most_bought_products/",
            },
        ]
        if not extra_context:
            extra_context = {}
        extra_context = {"reporting_pages": reporting_pages}
        return super().index(request, extra_context)


# Finally we define 3 instances of AdminSite, each with their own # set of required permissions and colors
class OwnersAdminSite(ReportingColoredAdminSite):
    site_header = "BookTime owners administration"
    site_header_color = "black"
    module_caption_color = "grey"

    def has_permission(self, request):
        return (
                request.user.is_active and request.user.is_superuser
        )


class CentralOfficeAdminSite(ReportingColoredAdminSite):
    site_header = "BookTime central office administration"
    site_header_color = "purple"
    module_caption_color = "pink"

    def has_permission(self, request):
        return (
                request.user.is_active and request.user.is_employee
        )


class DispatchersAdminSite(ColoredAdminSite):
    site_header = "BookTime central dispatch administration"
    site_header_color = "green"
    module_caption_color = "lightgreen"

    def has_permission(self, request):
        return (
                request.user.is_active and request.user.is_dispatcher
        )


main_admin = OwnersAdminSite()

main_admin.register(models.ProductTag, ProductTagAdmin)
main_admin.register(models.ProductImage, ProductImageAdmin)
main_admin.register(models.Product, ProductAdmin)
main_admin.register(models.User, UserAdmin)
main_admin.register(models.Address, AddressAdmin)
main_admin.register(models.Basket, BasketAdmin)
main_admin.register(models.Order, OrderAdmin)

central_office_admin = CentralOfficeAdminSite(
    "central-office-admin",
)
central_office_admin.register(models.Product, ProductAdmin)
central_office_admin.register(models.ProductTag, ProductTagAdmin)
central_office_admin.register(
    models.ProductImage, ProductImageAdmin
)
central_office_admin.register(models.Address, AddressAdmin)
central_office_admin.register(
    models.Order, CentralOfficeOrderAdmin
)
dispatchers_admin = DispatchersAdminSite("dispatchers-admin")
dispatchers_admin.register(models.ProductTag, ProductTagAdmin)
dispatchers_admin.register(models.Order, DispatchersOrderAdmin)

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile


class InvoiceMixin:
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "invoice/<int:order_id>/",
                self.admin_view(self.invoice_for_order),
                name="invoice",
            )
        ]
        return my_urls + urls

    def invoice_for_order(self, request, order_id):
        order = get_object_or_404(models.Order, pl=order_id)
        if request.GET.get("format") == "pdf":
            html_string = render_to_string(
                "invoice.html", {"order": order}
            )
            html = HTML(
                string=html_string,
                base_url=request.build_absolute_uri(),
            )
            result = html.write_pdf()
            response = HttpResponse(
                content_type="application/pdf"
            )
            response[
                "Content-Disposition"
            ] = "inline; filename=invoice.pdf"
            response["Content-Transfer-Encoding"] = "binary"
            with tempfile.NamedTemporaryFile(
                    delete=True
            ) as output:
                output.write(result)
                output.flush()
                output = open(output.name, "rb")
                binary_pdf = output.read()
                response.write(binary_pdf)
            return response
        return render(request, "invoice.html", {"order": order})

