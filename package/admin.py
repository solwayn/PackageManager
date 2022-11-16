from django.contrib import admin, messages
from django.db.models import Count, DecimalField, IntegerField, OuterRef, Subquery, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render

from package.forms import BulkSendForm
from package.models import Order


class TotalPackagesFilter(admin.SimpleListFilter):
    title = "total_packages_filter"
    parameter_name = "total_packages_filter"

    def lookups(self, request, model_admin):
        return (
            ("1", "1"),
            ("2", "2"),
            ("5", "5"),
            ("10", "10"),
            ("11", "10+"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value in ("1", "2", "5", "10"):
            queryset = queryset.filter(_total_packages=value)
        elif value in ("11",):
            queryset = queryset.filter(_total_packages__gt=value)
        return queryset


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        furniture_weight = Order.objects.annotate(furniture_weight=Sum("items__furniture__weight")).filter(
            pk=OuterRef("pk")
        )
        total_package = Order.objects.annotate(total_packages=Count("items__furniture__packages")).filter(
            pk=OuterRef("pk")
        )
        packages_weight = Order.objects.annotate(packages_weight=Sum("items__furniture__packages__weight")).filter(
            pk=OuterRef("pk")
        )
        qs = Order.objects.annotate(
            _furniture_weight=Subquery(furniture_weight.values("furniture_weight"), output_field=DecimalField()),
            _total_packages=Subquery(total_package.values("total_packages"), output_field=IntegerField()),
            _packages_weight=Subquery(packages_weight.values("packages_weight"), output_field=DecimalField()),
        )
        return qs

    list_display = (
        "id",
        "created_at",
        "customer_name",
        "country",
        "status",
        "delivery_company",
        "furniture_weight",
        "total_packages",
        "packages_weight",
    )
    list_filter = ("status", TotalPackagesFilter)
    actions = ["count_weight", "bulk_send"]

    def packages_weight(self, obj):
        return obj._packages_weight

    def furniture_weight(self, obj):
        return obj._furniture_weight

    def total_packages(self, obj):
        return obj._total_packages

    packages_weight.admin_order_field = "_packages_weight"
    furniture_weight.admin_order_field = "_furniture_weight"
    total_packages.admin_order_field = "_total_packages"

    def count_weight(self, request, queryset):
        weight = queryset.aggregate(Sum("_furniture_weight"))["_furniture_weight__sum"]
        messages.add_message(request, messages.INFO, f"Weight in kg: {weight}")

    def bulk_send(self, request, queryset):
        if request.method == "POST" and "apply" in request.POST:
            form = BulkSendForm(request.POST)
            if form.is_valid():
                queryset.update(status=Order.Status.SENT, delivery_company=form.cleaned_data["delivery_company"])
                self.message_user(request, "Changed status on {} orders".format(queryset.count()))
                return HttpResponseRedirect(request.get_full_path())

        return render(request, "admin/bulk_send.html", context={"form": BulkSendForm(), "orders": queryset})
