from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from sendgrid import SendGridAPIClient, Mail

from core.models import Job
from core.utils import send_sms


def send_sendgrid_emails(template_id, email, params):
    message = Mail(
        from_email='',
        to_emails="")
    message.dynamic_template_data = params
    message.template_id = template_id
    try:
        sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sendgrid_client.send(message)
        print(response.status_code)
    except Exception as e:
        print(e.message)


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created and instance.email:
        # Send Welcome Email
        full_name = instance.get_full_name()
        template_id = ''
        params = {
            'first_name': full_name}
        send_sendgrid_emails(template_id, instance.email, params)


@receiver(post_save, sender=Job)
def job_status_update(sender, instance, created, **kwargs):
    customer_full_name = instance.customer.user.get_full_name()
    order_no = instance.order_no
    if not instance.is_deleted_by_courier:
        if created:
            pass
        elif instance.status == Job.PROCESSING_STATUS:

            message = "Hi %s .Just a quick note to confirm that order reference: %s is now processing." % (
                customer_full_name, order_no)
            send_sms(message, '', instance.customer.phone_number)

        elif instance.status == Job.CANCELED_STATUS:

            message = "Hi %s .Just a quick note to confirm that order reference: %s is cancelled." % (
                customer_full_name, order_no)
            send_sms(message, '', instance.customer.phone_number)

            template_id = ""
            params = {
                'first_name': customer_full_name, "order_number": order_no}
            send_sendgrid_emails(template_id, instance.customer.user.email, params)

        elif instance.status == Job.PICKING_STATUS:

            message = "Hi %s .Just a quick note to confirm that order reference: %s is ready for pick." % (
                customer_full_name, order_no)
            send_sms(message, '', instance.customer.phone_number)

        elif instance.status == Job.DELIVERING_STATUS:

            message = "Hi %s .Just a quick note to confirm that order reference: %s is on the way to drop point." % (
                customer_full_name, order_no)
            send_sms(message, '', instance.customer.phone_number)

        elif instance.status == Job.COMPLETED_STATUS:

            message = "Hi %s .Just a quick note to confirm that order reference: %s has now been successfully delivered.." % (
                customer_full_name, order_no)
            send_sms(message, '', instance.customer.phone_number)

            template_id = ""
            params = {
                'first_name': customer_full_name, "order_number": order_no}
            send_sendgrid_emails(template_id, instance.customer.user.email, params)
