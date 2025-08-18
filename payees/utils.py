from django.shortcuts import get_object_or_404
from .models import Payee
from .constants import RESTRICTED_PAYEE_GROUP
from django.contrib.auth import get_user_model


def restrict_queryset_by_group(qs, user, payee_field=None):
    # If user is in restricted group, limit their access
    if user.groups.filter(name__in=RESTRICTED_PAYEE_GROUP).exists():
        # Special case: if querying the User model directly
        if qs.model == get_user_model():
            return qs.filter(id=user.id)
        # Otherwise, restrict to related Payee or user field
        if payee_field:
            payee = get_object_or_404(Payee, user=user)
            return qs.filter(**{payee_field: payee})
        return qs.filter(user=user)  # fallback for generic models with user FK

    # If not in restricted group, return all
    return qs
