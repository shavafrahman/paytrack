import zipfile
from django.core.exceptions import ValidationError


def validate_zip_file(file):
    try:
        if not zipfile.is_zipfile(file):
            raise ValidationError("The uploaded file is not a valid ZIP file.")
    except Exception as e:
        raise ValidationError("Error validating ZIP file.")


def form16_extracted_path(instance, filename):
    """ Define path for extracted files """
    return f'uploads/payroll/form16/extracted/{instance.financial_year.financial_year}/{filename}'
