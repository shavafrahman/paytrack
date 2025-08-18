import logging

from celery import shared_task
from decimal import Decimal

from .models import (PayRun, Payment, PayRunStatusChoices, PayRecordRegister)
from payees.models import Payee, BankDetails

# For getting the named logger
logger = logging.getLogger('celery_debug')


@shared_task
def run_pay_run_task(payrun_id):
    logger.info('Starting task with pay_run_id: %s', payrun_id)

    try:
        pay_run = PayRun.objects.get(id=payrun_id)
    except PayRun.DoesNotExist:
        logger.error('PayRun with ID %s does not exist.', payrun_id)
        return

    if pay_run.status in [PayRunStatusChoices.COMPLETED,
                            PayRunStatusChoices.APPROVED,
                            PayRunStatusChoices.REJECTED,
                            PayRunStatusChoices.IN_PROGRESS,]:
        logger.warning('PayRun %s is not in DUE status. Skipping.', payrun_id)
        return

    payees = Payee.objects.filter(status='active', is_deleted='False')
    pay_run.status = PayRunStatusChoices.IN_PROGRESS
    pay_run.save()

    error_log = []

    for payee in payees:
        logger.info('Processing payee: %s', payee)

        try:
            bank_details = BankDetails.objects.get(payee=payee, payee_acknowledgement=True)
        except BankDetails.DoesNotExist:
            error_log.append(f"{payee.full_name} - Missing acknowledged bank "
                             f"details")
            continue

        try:
            total_amount = Payment.objects.get(payee=payee)
        except Payment.DoesNotExist:
            error_log.append(f"{payee.full_name} - No payment data available")
            continue

        tds_percentage = Decimal(str(payee.tds_type.tds_percentage if payee.tds_type else 0))
        tds_amount = (total_amount.amount * tds_percentage) / Decimal('100')
        total_net_income = total_amount.amount - tds_amount

        PayRecordRegister.objects.create(
            pay_run=pay_run,
            amount=total_amount.amount,
            payee=payee,
            bank_name=bank_details.bank_name,
            account_number=bank_details.account_no,
            account_holder_name=bank_details.account_holder_name,
            account_type=bank_details.account_type,
            ifsc_code=bank_details.ifsc_code,
            micr_code=bank_details.micr_code,
            swift_code=bank_details.swift_code,
            branch_address=bank_details.branch_address,
            tds_percentage=tds_percentage,
            gross_amount=total_amount.amount,
            net_income=total_net_income,
        )
        logger.info('PayRecordRegister created for payee: %s',payee.full_name )

    if error_log:
        pay_run.error_log = '\n'.join(error_log)
    else:
        pay_run.error_log = 'PayRecordRegister created successfully for every payee.'

    pay_run.status = PayRunStatusChoices.COMPLETED
    pay_run.save()

    logger.info('PayRun %s processing completed.', payrun_id)


