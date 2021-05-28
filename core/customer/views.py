import requests
import stripe
import firebase_admin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.base import View
from firebase_admin import credentials, auth, messaging

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from core.customer import forms
from . import forms
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, login
from django.conf import settings
from django.http import JsonResponse
from core.models import *

from core.models import Job

from core.models import Courier

from core.models import Transaction
from . import forms

import stripe

# stripe.api_key = "AIzaSyAzwAUOM6rzCK_xaTcJQsJ5WZn81VhVMME"

cred = credentials.Certificate(settings.FIREBASE_ADMIN_CREDENTIAL)
firebase_admin.initialize_app(cred)

stripe.api_key = settings.STRIPE_API_SECRET_KEY

decorators = [login_required, ]


@method_decorator(decorators, name='dispatch')
class CustomHome(View):

    def get(self, request, *args, **kwargs):
        return redirect(reverse('customer:profile'))


@method_decorator(decorators, name='dispatch')
class ProfilePge(View):

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        if request.POST.get('action') == 'update_profile':
            user_form = forms.BasicUserForm(request.POST, instance=request.user)
            customer_form = forms.BasicCustomerForm(request.POST, request.FILES, instance=request.user.customer)

            if user_form.is_valid() and customer_form.is_valid():
                user_form.save()
                customer_form.save()

                messages.success(request, 'Your profile has been updated')
                return redirect(reverse('customer:profile'))

        elif request.POST.get('action') == 'update_password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)

                messages.success(request, 'Your password has successfully been updated')
                return redirect(reverse('customer:profile'))

        elif request.POST.get('action') == 'update_phone':
            # Get Firebase User Data
            firebase_user = auth.verify_id_token(request.POST.get('id_token'))

            request.user.customer.phone_number = firebase_user['phone_number']
            request.user.customer.save()
            return redirect(reverse('customer:profile'))

    def get(self, request, *args, **kwargs):
        user_form = forms.BasicUserForm(instance=request.user)
        customer_form = forms.BasicCustomerForm(instance=request.user.customer)
        password_form = PasswordChangeForm(request.user)

        context = {
            'user_form': user_form,
            'customer_form': customer_form,
            'password_form': password_form
        }
        return render(request, 'customer/profile.html', context)


@method_decorator(decorators, name='dispatch')
class PaymentMethod(View):

    def post(self, request, *args, **kwargs):
        current_customer = request.user.customer

        stripe.PaymentMethod.detach(current_customer.stripe_payment_method_id)
        current_customer.stripe_payment_method_id = ""
        current_customer.stripe_card_last4 = ""
        current_customer.save()
        return redirect(reverse('customer:payment_method'))

    # Save Stripe Customer Info

    def get(self, request, *args, **kwargs):
        current_customer = request.user.customer
        if not current_customer.stripe_customer_id:
            customer = stripe.Customer.create()
            current_customer.stripe_customer_id = customer['id']
            current_customer.save()

        # Get Stripe Payment Method
        stripe_payment_methods = stripe.PaymentMethod.list(
            customer=current_customer.stripe_customer_id,
            type='card',
        )

        if stripe_payment_methods and len(stripe_payment_methods.data) > 0:
            payment_method = stripe_payment_methods.data[0]
            current_customer.stripe_payment_method_id = payment_method.id
            current_customer.stripe_card_last4 = payment_method.card.last4
            current_customer.save()
        else:
            current_customer.stripe_payment_method_id = ''
            current_customer.stripe_card_last4 = ''
            current_customer.save()

        if not current_customer.stripe_payment_method_id:
            intent = stripe.SetupIntent.create(
                customer=current_customer.stripe_customer_id
            )

            return render(request, 'customer/payment_method_page.html', {
                'client_secret': intent.client_secret,
                'STRIPE_API_PUBLIC_KEY': settings.STRIPE_API_PUBLIC_KEY,
            })
        else:
            return render(request, 'customer/payment_method_page.html')


@method_decorator(decorators, name='dispatch')
class CreatejobPage(View):

    def get(self, request, *args, **kwargs):
        current_customer = request.user.customer

        # if not current_customer.stripe_payment_method_id:
        # return redirect(reverse('customer:payment_method'))
        # BLOCKS USER CREATING SECOND JOB IF EXISTING IN STATUS BELOW
        has_current_job = Job.objects.filter(
            customer=current_customer,
            status__in=[
                Job.PROCESSING_STATUS,
                Job.PICKING_STATUS,
                Job.DELIVERING_STATUS
            ]
        ).exists()

        if has_current_job:
            messages.warning(request,
                             "Existing job pending completion - Please retry when current job is set to complete. ")
            return redirect(reverse('customer:current_jobs'))
        # END MESSAGE

        creating_job = Job.objects.filter(customer=current_customer, status=Job.CREATING_STATUS).last()
        step1_form = forms.JobCreateStep1Form(instance=creating_job)
        step2_form = forms.JobCreateStep2Form(instance=creating_job)
        step3_form = forms.JobCreateStep3Form(instance=creating_job)
        if not creating_job:
            current_step = 1
        elif creating_job.delivery_name:
            current_step = 4
        elif creating_job.pickup_name:
            current_step = 3
        else:
            current_step = 2
        return render(request, 'customer/create_job.html', {
            'job': creating_job,
            'step': current_step,
            'step1_form': step1_form,
            'step2_form': step2_form,
            'step3_form': step3_form,
            'GOOGLE_MAP_API_KEY': settings.GOOGLE_MAP_API_KEY
        })

    def post(self, request, *args, **kwargs):
        current_customer = request.user.customer
        creating_job = Job.objects.filter(customer=current_customer, status=Job.CREATING_STATUS).last()
        if request.POST.get('step') == '1':
            step1_form = forms.JobCreateStep1Form(request.POST, request.FILES, instance=creating_job)
            if step1_form.is_valid():
                creating_job = step1_form.save(commit=False)
                creating_job.customer = current_customer
                creating_job.save()
                return redirect(reverse('customer:create_job'))

        elif request.POST.get('step') == '2':
            step2_form = forms.JobCreateStep2Form(request.POST, instance=creating_job)
            if step2_form.is_valid():
                creating_job = step2_form.save()
                return redirect(reverse('customer:create_job'))

        elif request.POST.get('step') == '3':
            step3_form = forms.JobCreateStep3Form(request.POST, instance=creating_job)
            if step3_form.is_valid():
                creating_job = step3_form.save()

                try:
                    r = requests.get(
                        "api".format(
                            creating_job.pickup_address,
                            creating_job.delivery_address,
                            settings.GOOGLE_MAP_API_KEY,
                        ))

                    print(r.json()['rows'])

                    distance = r.json()['rows'][0]['elements'][0]['distance']['value']
                    duration = r.json()['rows'][0]['elements'][0]['duration']['value']
                    creating_job.distance = round(distance / 1000, 2)
                    creating_job.duration = int(duration / 60)
                    creating_job.price = creating_job.distance * 1  # €1 per km
                    creating_job.save()

                except Exception as e:
                    print(e)
                    messages.error(request, "Unfortunately, we do not support shipping at this distance")

                return redirect(reverse('customer:create_job'))

        elif request.POST.get('step') == '4':
            if creating_job.price:
                try:
                    payment_intent = stripe.PaymentIntent.create(
                        amount=int(creating_job.price * 100),
                        currency='eur',
                        customer=current_customer.stripe_customer_id,
                        payment_method=current_customer.stripe_payment_method_id,
                        off_session=True,
                        confirm=True,
                    )

                    Transaction.objects.create(
                        stripe_payment_intent_id=payment_intent['id'],
                        job=creating_job,
                        amount=creating_job.price,
                    )

                    creating_job.status = Job.PROCESSING_STATUS
                    creating_job.save()

                    # Send Push Notification to all Couriers
                    couriers = Courier.objects.all()
                    registration_tokens = [i.fcm_token for i in couriers if i.fcm_token]

                    message = messaging.MulticastMessage(
                        notification=messaging.Notification(
                            title=creating_job.order_no,
                            body=creating_job.order_no,
                        ),
                        webpush=messaging.WebpushConfig(
                            notification=messaging.WebpushNotification(
                            ),
                            fcm_options=messaging.WebpushFCMOptions(
                                link=settings.NOTIFICATION_URL + reverse('courier:available_jobs'),
                            ),
                        ),
                        tokens=registration_tokens
                    )
                    response = messaging.send_multicast(message)
                    print('{0} messages were sent successfully'.format(response.success_count))

                    return redirect(reverse('customer:home'))

                except stripe.error.CardError as e:
                    err = e.error
                    # Error code will be authentication_required if authentication is needed
                    print("Code is: %s" % err.code)
                    payment_intent_id = err.payment_intent['id']
                    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Determine the current step
        creating_job = Job.objects.filter(customer=current_customer, status=Job.CREATING_STATUS).last()
        step1_form = forms.JobCreateStep1Form(instance=creating_job)
        step2_form = forms.JobCreateStep2Form(instance=creating_job)
        step3_form = forms.JobCreateStep3Form(instance=creating_job)
        if not creating_job:
            current_step = 1
        elif creating_job.delivery_name:
            current_step = 4
        elif creating_job.pickup_name:
            current_step = 3
        else:
            current_step = 2
        return render(request, 'customer/create_job.html', {
            'job': creating_job,
            'step': current_step,
            'step1_form': step1_form,
            'step2_form': step2_form,
            'step3_form': step3_form,
            'GOOGLE_MAP_API_KEY': settings.GOOGLE_MAP_API_KEY
        })


@method_decorator(decorators, name='dispatch')
class CurrentJobpage(View):
    def get(self, request, *args, **kwargs):
        jobs = Job.objects.filter(
            customer=request.user.customer,
            status__in=[
                Job.PROCESSING_STATUS,
                Job.PICKING_STATUS,
                Job.DELIVERING_STATUS
            ]
        )

        return render(request, 'customer/jobs.html', {
            "jobs": jobs
        })


@method_decorator(decorators, name='dispatch')
class ArchivedjobsPage(View):
    def get(self, request, *args, **kwargs):
        jobs = Job.objects.filter(
            customer=request.user.customer,
            is_deleted_by_customer=False,
            status__in=[
                Job.COMPLETED_STATUS,
                Job.CANCELED_STATUS
            ]
        )

        return render(request, 'customer/jobs.html', {
            "jobs": jobs
        })


@method_decorator(decorators, name='dispatch')
class JobPage(View):

    def get(self, request, *args, **kwargs):
        job_id = kwargs.get("job_id")
        job = Job.objects.get(id=job_id)
        return render(request, 'customer/job.html', {
            "job": job,
            "GOOGLE_MAP_API_KEY": settings.GOOGLE_MAP_API_KEY
        })

    def post(self, request, *args, **kwargs):
        job_id = kwargs.get("job_id")
        job = Job.objects.get(id=job_id)

        if job.status == Job.PROCESSING_STATUS:
            job.status = Job.CANCELED_STATUS
            job.save()
            return redirect(reverse('customer:archived_jobs'))

        return render(request, 'customer/job.html', {
            "job": job,
            "GOOGLE_MAP_API_KEY": settings.GOOGLE_MAP_API_KEY
        })


@method_decorator(decorators, name='dispatch')
class DeleteJobPage(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "success": True
        })

    def post(self, request, *args, **kwargs):
        job_id = kwargs.get("job_id")
        job = Job.objects.get(id=job_id)
        job.is_deleted_by_customer = True
        job.save()

        return JsonResponse({
            "success": True
        })
