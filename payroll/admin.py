import logging

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from decimal import Decimal
from payees.utils import restrict_queryset_by_group
from payees.constants import RESTRICTED_PAYEE_GROUP
from .models import (Payment, PayRecordRegister, PayRun,
                     PayRunStatusChoices, Form16, Form16Entries,
                     ComponentValue)
from .alerts import (approve_payrun_action, reject_payrun_action,
                     run_payrun_action, is_payrun_exists)
from .forms import PayRunForm
from configs.models import Component

logger = logging.getLogger(__name__)


# Register your models here.


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["payee", "label"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return restrict_queryset_by_group(qs, request.user,
                                          payee_field='payee')


class PayRunAdmin(admin.ModelAdmin):
    list_display = ('display_month_name', 'year', 'status', 'created_by')
    list_filter = ('status', 'month', 'year')
    search_fields = ('status', 'get_month_name', 'year')
    readonly_fields = ('status', 'created_at','error_log_summary')
    ordering = ['-created_at']
    actions = ['run_payrun', 'approve_payrun', 'reject_payrun']
    form = PayRunForm


    def add_view(self, request, form_url='', extra_context=None):
        if is_payrun_exists(request):
            return redirect(reverse('admin:payroll_payrun_changelist'))
        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if change == False:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def approve_payrun(self, request, queryset):
        approve_payrun_action(self, request, queryset)

    approve_payrun.short_description = 'Approve selected payrun'

    def reject_payrun(self, request, queryset):
        reject_payrun_action(self, request, queryset)

    reject_payrun.short_description = 'Reject selected payrun'

    def run_payrun(self, request, queryset):
        run_payrun_action(self, request, queryset)

    run_payrun.short_description = 'Run selected payrun'

    def has_errors(self, obj):
        return bool(obj.error_log)
    has_errors.boolean = True

    def error_log_summary(self, obj):
        if not obj.error_log:
            return "-"
        return format_html("<pre>{}</pre>", obj.error_log)
    error_log_summary.short_description = 'Error Log'



class EarningsInline(admin.TabularInline):
    model = ComponentValue
    extra = 1
    can_delete = False
    verbose_name_plural = "Additional Earnings"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(component__operation='sum')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "component":
            kwargs["queryset"] = Component.objects.filter(operation='sum')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Disable related buttons (add, view, change)
        component_field = formset.form.base_fields['component']
        component_field.widget.can_add_related = False
        component_field.widget.can_change_related = False
        component_field.widget.can_view_related = False

        # Disable fields if the PayRun status is 'APPROVED'
        if obj and obj.pay_run.status == PayRunStatusChoices.APPROVED:
            component_field.disabled = True
            formset.form.base_fields['value'].disabled = True

        return formset

    def has_add_permission(self, request, obj=None):
        # Disable add permission if PayRun status is 'APPROVED'
        if obj and obj.pay_run.status == PayRunStatusChoices.APPROVED:
            return False
        return super().has_add_permission(request, obj)


class DeductionsInline(admin.TabularInline):
    model = ComponentValue
    extra = 1
    can_delete = False
    verbose_name_plural = "Deductions"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(component__operation='subtract')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "component":
            kwargs["queryset"] = Component.objects.filter(operation='subtract')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Disable related buttons (add, view, change)
        component_field = formset.form.base_fields['component']
        component_field.widget.can_add_related = False
        component_field.widget.can_change_related = False
        component_field.widget.can_view_related = False

        # Disable fields if the PayRun status is 'APPROVED'
        if obj and obj.pay_run.status == PayRunStatusChoices.APPROVED:
            component_field.disabled = True
            formset.form.base_fields['value'].disabled = True

        return formset

    def has_add_permission(self, request, obj=None):
        # Disable add permission if PayRun status is 'APPROVED'
        if obj and obj.pay_run.status == PayRunStatusChoices.APPROVED:
            return False
        return super().has_add_permission(request, obj)


class PayRecordRegisterAdmin(admin.ModelAdmin):
    inlines = [EarningsInline, DeductionsInline]
    readonly_fields = ('payee', 'amount', 'pay_run', 'tds_percentage',
                       'bank_name', 'account_number', 'account_holder_name',
                       'account_type', 'ifsc_code', 'micr_code',
                       'swift_code', 'branch_address', 'gross_amount',
                       'net_income')
    list_filter = ('pay_run__status', 'pay_run__month', 'pay_run__year')
    list_display = ('payee', 'amount', 'gross_amount', 'pay_run')
    actions = None  # Disable the delete action

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # show everything, even unapproved

        # Check if user is in a restricted group
        is_restricted = request.user.groups.filter(name__in=RESTRICTED_PAYEE_GROUP).exists()

        if is_restricted:
            # Restrict to records linked to this user + filter for approved pay_runs
            qs = restrict_queryset_by_group(qs, request.user, payee_field='payee')
            return qs.filter(pay_run__status='approved')

        # User is not in restricted groups => full access
        return qs

    def get_total_earnings(self, obj):
        return sum(c.value for c in obj.components.filter(
            component__operation='Sum'))

    get_total_earnings.short_description = 'Total Earnings'

    def get_total_deductions(self, obj):
        return sum(
            c.value for c in obj.components.filter(
                component__operation='Subtract'))

    get_total_deductions.short_description = 'Total Deductions'

    def has_delete_permission(self, request, obj=None):
        # Hide delete for all objects
        if obj:
            return False
        return super().has_delete_permission(request, obj)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        pay_record_register = form.instance

        # Calculate the total based on component operations (sum or subtract)
        total = pay_record_register.amount + sum(
            component_value.value if component_value.component.operation == 'sum'
            else -component_value.value
            for component_value in
            ComponentValue.objects.filter(pay_record=pay_record_register)
        )

        # Update gross_amount and save the instance
        pay_record_register.gross_amount = total
        pay_record_register.save()

        tds_percentage = Decimal(str(pay_record_register.tds_percentage or 0))  # Safe default to 0
        tds_amount = (pay_record_register.gross_amount * tds_percentage) / Decimal('100')
        total_net_income = pay_record_register.gross_amount - tds_amount

        pay_record_register.net_income = total_net_income
        pay_record_register.save()


class Forms16EntriesAdmin(admin.ModelAdmin):
    list_display = (
        'financial_year', 'form_16_link', 'form_16_link_to_download')
    list_filter = ('financial_year',)
    list_per_page = 20

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return restrict_queryset_by_group(qs, request.user,
                                          payee_field='payee')

    def form_16_link(self, obj):
        if obj.form_16:
            return format_html(
                "<a href='{}' target='_blank'>{}</a>",
                obj.form_16.url,
                obj.form_16.name.split('/')[-1]  # Show only filename
            )
        return "No File"

    form_16_link.short_description = "Form 16 File"

    def form_16_link_to_download(self, obj):
        if obj.form_16:
            return format_html('<a href="{}" download>Download</a>',
                               obj.form_16.url)
        return "No file"

    form_16_link_to_download.short_description = 'Form 16'
    form_16_link_to_download.allow_tags = True


class Form16Inline(admin.TabularInline):  # or StackedInline
    model = Form16Entries
    fields = ['form_16_link', 'financial_year']
    readonly_fields = ['form_16_link', 'financial_year']
    extra = 0
    can_delete = False
    verbose_name = "Form16 PDF"
    verbose_name_plural = "Form16 PDFs"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('financial_year')

    def form_16_link(self, obj):
        if obj.form_16:
            return format_html(
                "<a href='{}' target='_blank'>{}</a>",
                obj.form_16.url,
                obj.form_16.name.split('/')[-1]  # Show only filename
            )
        return "No File"


class Forms16Admin(admin.ModelAdmin):
    list_display = ('financial_year', 'form_16_link', 'view_form_entries')

    def form_16_link(self, obj):
        if obj.form16_zip_file:
            return format_html(
                "<a href='{}' target='_blank'>{}</a>",
                obj.form16_zip_file.url,
                obj.form16_zip_file.name.split('/')[-1]  # Show only filename
            )
        return "No File"

    form_16_link.short_description = "Form 16 File"

    def view_form_entries(self, obj):
        """
        Generates a button that links to Form16Entries filtered by financial_year.
        """
        url = reverse(
            'admin:payroll_form16entries_changelist')
        url += f"?financial_year__id__exact={obj.id}"  # Filters by foreign key ID
        return format_html(
            '<a class="button" href="{}" style="background:#28a745; color:white; padding:4px 8px; border-radius:4px; text-decoration:none;">View Form Entries</a>',
            url)

    view_form_entries.short_description = "View Form Entries"


admin.site.register(Payment, PaymentAdmin)
admin.site.register(PayRecordRegister, PayRecordRegisterAdmin)
admin.site.register(PayRun, PayRunAdmin)
admin.site.register(Form16, Forms16Admin)
admin.site.register(Form16Entries, Forms16EntriesAdmin)
