import graphene
from graphene_django.types import DjangoObjectType
from .models import Payment, PayRecordRegister
from django.contrib.auth.decorators import login_required


class PayRecordRegisterType(DjangoObjectType):
    class Meta:
        """
        This section displays the payee's bank information, along with the
        salary and TDS percentage.
        """
        model = PayRecordRegister
        fields = ('amount', 'bank_name', 'payee', 'account_number',
                  'account_holder_name', 'account_type', 'ifsc_code',
                  'micr_code', 'swift_code', 'branch_address',
                  'tds_percentage', 'gross_amount')


class PaymentType(DjangoObjectType):
    class Meta:
        """
        This section displays the salary amount of the employee
        """
        model = Payment
        fields = ('amount', 'label', 'payee')


class PayrollQuery(graphene.ObjectType):
    all_payments = graphene.List(PaymentType)
    all_pay_record_register = graphene.List(PayRecordRegisterType)

    @staticmethod
    @login_required
    def resolve_all_payments(root, info):
        # Check if the user is authenticated
        PayrollQuery.check_authorization(info.context)
        # Fetch all pay records
        return Payment.objects.all()

    @staticmethod
    @login_required
    def resolve_all_pay_record_register(root, info):
        # Check if the user is authenticated
        PayrollQuery.check_authorization(info.context)
        # Fetch all pay records
        return PayRecordRegister.objects.all()
