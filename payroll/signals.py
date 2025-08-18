import os
import zipfile
import logging
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Form16, Form16Entries
from payees.models import Payee

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Form16)
def extract_zip_and_create_entries(sender, instance, created, **kwargs):
    """
    This method extracts the uploaded ZIP file and assigns each Form16 PDF
    to the corresponding payee by matching the PAN number.
    """
    logger.debug(
        f"Signal triggered for Form16 ID {instance.pk} | Created: {created} | Already Extracted: {instance.is_extracted}")

    if not instance.form16_zip_file or instance.is_extracted:
        logger.debug(
            "Skipping extraction (already extracted or no zip file present).")
        return
    zip_path = instance.form16_zip_file

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():

                if file_name.startswith("._") or "__MACOSX" in file_name:
                    logger.debug(f"Skipping Apple metadata file: {file_name}")
                    continue

                if file_name.lower().endswith(('.pdf', '.xml')):
                    cleaned_filename = os.path.basename(file_name)
                    save_path = f'uploads/payroll/form16/extracted/{cleaned_filename}'

                    """
                    Deletes the file first if it already exists (avoids
                    duplicates).
                    """
                    if default_storage.exists(save_path):
                        default_storage.delete(save_path)

                    file_content = zip_ref.read(file_name)

                    if not file_content:
                        logger.warning(
                            f"File '{file_name}' is empty. Skipping.")
                        continue

                    pan_no = cleaned_filename.split('_')[0].upper()

                    try:
                        payee = Payee.objects.get(pan_no=pan_no)
                        logger.info(f"Matched Payee for PAN {pan_no}: {payee}")
                    except Payee.DoesNotExist:
                        logger.warning(f"No Payee found for PAN {pan_no}")
                        payee = None

                    """
                    Creates a new Form16Entries record, links it to Form16 and
                    (if found) to Payee, and saves the file content.
                    """
                    new_entry = Form16Entries(financial_year=instance,
                                              payee=payee)
                    new_entry.form_16.save(cleaned_filename,
                                           ContentFile(file_content),
                                           save=True)

                    logger.info(
                        f"Saved: {cleaned_filename} → Payee: {payee if payee else 'None'}")

        # Marks the ZIP as extracted so it doesn't process again later.
        instance.is_extracted = True
        instance.save(update_fields=['is_extracted'])
        logger.info(f"Extraction complete for Form16 ID {instance.pk}")

    except zipfile.BadZipFile:
        logger.error(f"Bad ZIP file encountered: {zip_path}")
