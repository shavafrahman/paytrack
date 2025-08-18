from decouple import config
from django.core.management.base import BaseCommand
from zohopeople.constants import (GRAND_TYPE, ZP_API_REDIR_URI,
                                  ZP_API_ATOKEN_DOM_URL)
from zohopeople.models import ZohoPeopleFormToken
from zohopeople.utils import tgeneration_call_api


def zoho_form_token_generation(grand_token):
    """
    Generate Access token for sending data to Zoho People
    and Refresh token to generate new Access token. Store both
    tokens in DB.
    """
    tgeneration_data = {
        'grant_type': GRAND_TYPE,
        'client_id': config('ZOHOPEOPLE_CLIENT_ID'),
        'client_secret': config('ZOHOPEOPLE_CLIENT_SECRET'),
        'redirect_uri': ZP_API_REDIR_URI,
        'code': grand_token
    }

    url = ZP_API_ATOKEN_DOM_URL
    # Send Post request for generating tokens.
    tgeneration_resp = tgeneration_call_api(url, tgeneration_data)

    if tgeneration_resp:
        # Convert response to json data.
        tgeneration_resp_val = tgeneration_resp.json()

        # Store tokens in the DB.
        tokens = ZohoPeopleFormToken(
            access_token=tgeneration_resp_val['access_token'],
            refresh_token=tgeneration_resp_val['refresh_token'])
        tokens.save()


class Command(BaseCommand):
    help = "Creates refresh tokens"

    def add_arguments(self, parser):
        parser.add_argument("grand_token", type=str)

    def handle(self, *args, **options):
        grand_token = options["grand_token"]
        zoho_form_token_generation(grand_token)
