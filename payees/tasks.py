import logging
from celery import shared_task
from .models import Payee
from zohopeople.utils import get_payees_details

# For getting the named logger
logger = logging.getLogger('celery_debug')


# To fetch payee details from zoho people
@shared_task
def fetch_details(payee_id):
    # Calling the function get_employee_details and return response
    try:
        response_data = get_payees_details(payee_id).json()
        response_data_list = response_data["response"]["result"][0]
    except Exception as e:
        logger.warning(e)
        response_data_list = {}
    if response_data_list:
        for data in response_data_list.values():
            fetched_data = data[0]
            payee = Payee.objects.get(hrm_id=payee_id)
            payee.full_name = fetched_data["FirstName"] + " " + fetched_data[
                "LastName"]
            payee.email = fetched_data["EmailID"]
            payee.pan_no = fetched_data["Pan_Number"]
            payee.address = fetched_data["Permanent_Address"]
            payee.date_of_joining = fetched_data["Dateofjoining"]
            payee.save()
