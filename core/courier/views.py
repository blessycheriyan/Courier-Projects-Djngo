from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.utils.decorators import method_decorator

from core.courier.forms import Driverdetailform
from core.models import *
from core.courier import forms

from django.views.generic import View, TemplateView

from django.views.generic import TemplateView

from core.models import Job

decorators = [login_required, ]


@method_decorator(decorators, name='dispatch')
class CourierHome(View):

    def get(self, request, *args, **kwargs):
        return redirect(reverse('courier:available_jobs'))


@method_decorator(decorators, name='dispatch')
class AvailableJobsPage(View):

    def get(self, request, *args, **kwargs):
        return render(request, 'courier/available_jobs.html', {
            "GOOGLE_MAP_API_KEY": settings.GOOGLE_MAP_API_KEY
        })


@method_decorator(decorators, name='dispatch')
class AvailableJobPage(View):

    def get(self, request, *args, **kwargs):
        vehicle_type = request.user.courier.vehicle

        job = Job.objects.filter(vehicle=vehicle_type,
                                 status=Job.PROCESSING_STATUS).last()

        if not job:
            return redirect(reverse('courier:available_jobs'))

        return render(request, 'courier/available_job.html', {
            "job": job
        })

    def post(self, request, *args, **kwargs):
        vehicle_type = request.user.courier.vehicle
        job = Job.objects.filter(id=kwargs.get("id"), vehicle=vehicle_type, status=Job.PROCESSING_STATUS).last()
        job.courier = request.user.courier
        job.status = Job.PICKING_STATUS
        job.save()
        job.save()

        try:
            layer = get_channel_layer()
            async_to_sync(layer.group_send)("job_" + str(job.id), {
                'type': 'job_update',
                'job': {
                    'status': job.get_status_display(),
                }
            })
        except:
            pass

        return redirect(reverse('courier:current_job'))


@method_decorator(decorators, name='dispatch')
class CurrentJobPage(View):

    def get(self, request, *args, **kwargs):
        job = Job.objects.filter(
            courier=request.user.courier,
            status__in=[
                Job.PICKING_STATUS,
                Job.DELIVERING_STATUS
            ]
        ).last()
        return render(request, 'courier/current_job.html', {
            "job": job,
            "GOOGLE_MAP_API_KEY": settings.GOOGLE_MAP_API_KEY
        })


@method_decorator(decorators, name='dispatch')
class CurrentJobTakephotoPage(View):
    def get(self, request, *args, **kwargs):
        job = Job.objects.filter(
            id=kwargs.get("id"),
            courier=request.user.courier,
            status__in=[
                Job.PICKING_STATUS,
                Job.DELIVERING_STATUS
            ]
        ).last()

        if not job:
            return redirect(reverse('courier:current_job'))

        return render(request, 'courier/current_job_take_photo.html', {
            "job": job
        })


@method_decorator(decorators, name='dispatch')
class JobComplete(TemplateView):
    template_name = "courier/job_complete.html"


@method_decorator(decorators, name='dispatch')
class ArchivedJobsPage(View):
    def get(self, request, *args, **kwargs):
        jobs = Job.objects.filter(
            courier=request.user.courier,
            is_deleted_by_courier=False,
            status=Job.COMPLETED_STATUS
        )

        return render(request, 'courier/archived_jobs.html', {
            "jobs": jobs
        })


@method_decorator(decorators, name='dispatch')
class ProfilePage(View):

    def get(self, request, *args, **kwargs):
        jobs = Job.objects.filter(
            courier=request.user.courier,
            status=Job.COMPLETED_STATUS
        )

        total_earnings = round(sum(job.price for job in jobs) * 0.7, 2)  # Platform Fee = 30%
        total_jobs = len(jobs)
        total_km = sum(job.distance for job in jobs)

        return render(request, 'courier/profile.html', {
            'total_earnings': total_earnings,
            'total_jobs': total_jobs,
            'total_km': total_km
        })

    def post(self, request):
        form = Driverdetailform(request.POST)
        if form.is_valid():
            form.save()

            return redirect('/')

        return render(request, 'courier/profile.html', {
            'form': form
        })


@method_decorator(decorators, name='dispatch')
class PayoutMethodPage(View):

    def get(self, request, *args, **kwargs):
        payout_form = forms.PayoutForm(instance=request.user.courier)

        return render(request, 'courier/payout_method.html', {'payout_form': payout_form})

    def post(self, request, *args, **kwargs):
        payout_form = forms.PayoutForm(request.POST, instance=request.user.courier)
        if payout_form.is_valid():
            payout_form.save()

            messages.success(request, "Payout email address updated!")
            return redirect(reverse('courier:profile'))

        return render(request, 'courier/payout_method.html', {
            'payout_form': payout_form
        })


@method_decorator(decorators, name='dispatch')
class ChangeavatarPage(View):

    def get(self, request, *args, **kwargs):
        avatar_form = forms.ChangeAvatarForm(instance=request.user.courier)
        return render(request, 'courier/change_avatar.html', {
            'avatar_form': avatar_form})

    def post(self, request, *args, **kwargs):
        avatar_form = forms.ChangeAvatarForm(request.POST, request.FILES, instance=request.user.courier)
        if avatar_form.is_valid():
            avatar_form.save()
            messages.success(request, "Avatar updated!")
            return redirect(reverse('courier:profile'))

        return render(request, 'courier/change_avatar.html', {
            'avatar_form': avatar_form})


@method_decorator(decorators, name='dispatch')
class DeletejobPage(View):

    def post(self, request, *args, **kwargs):
        job = Job.objects.get(id=kwargs.get("job_id"))
        job.is_deleted_by_courier = True
        job.save()
        return redirect(reverse('courier:archived_jobs'))


class Driverdetails(View):
    def get(self, request, *args, **kwargs):
        form = forms.Driverdetailform(instance=request.user.courier)

        context = {
            'form': form,
        }
        return render(request, 'courier/driverdetails.html', context)

    def post(self, request, *args, **kwargs):
        form = forms.Driverdetailform(request.POST, instance=request.user.courier)

        if form.is_valid():
            form.save()
            return redirect(reverse('courier:profile'))

        return render(request, 'driverdetails.html', {
            'form': form
        })

# class JobsPage(TemplateView):
#   def get(self, request, *args, **kwargs):
#      return redirect(reverse('courier:archived_jobs'))
