from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from core import views, consumers
from core.courier.views import CourierHome, AvailableJobPage, AvailableJobsPage, CurrentJobPage, \
    CurrentJobTakephotoPage, JobComplete, ArchivedJobsPage, ProfilePage, PayoutMethodPage, ChangeavatarPage, \
    DeletejobPage


from core.courier import views as courier_views, apis as courier_apis
from core.customer.views import CustomHome, ProfilePge, PaymentMethod, CreatejobPage, CurrentJobpage, ArchivedjobsPage, \
    JobPage, DeleteJobPage
from core.views import Homes, SignUp
from core.courier.views import Driverdetails
from django.contrib.auth import views as auth_views

customer_urlpatters = [
    path('',  CustomHome.as_view(), name="home"),

    #path('driver_details',  Driverdetails.as_view(), name="driver_details"),
    path('profile/', ProfilePge.as_view(), name="profile"),
    path('payment_method/', PaymentMethod.as_view(), name="payment_method"),
    path('create_job/', CreatejobPage.as_view(), name="create_job"),
    path('jobs/current/', CurrentJobpage.as_view(), name="current_jobs"),
    path('jobs/archived/', ArchivedjobsPage.as_view(), name="archived_jobs"),
    path('jobs/<job_id>/', JobPage.as_view(), name="job"),
    path('delete-job/<job_id>/',  DeleteJobPage.as_view(), name="delete_job"),
]


courier_urlpatters = [
    path('', CourierHome.as_view(), name="home"),
    path('jobs/available/', AvailableJobsPage.as_view(), name="available_jobs"),
    #path('jobe/available/', JobsPage.as_view(), name="available_jobe"),

    path('jobs/available/<id>/', AvailableJobPage.as_view(), name="available_job"),
    path('jobs/current/', CurrentJobPage.as_view(), name="current_job"),
    path('jobs/current/<id>/take_photo/',  CurrentJobTakephotoPage.as_view(), name="current_job_take_photo"),
    path('jobs/complete/', JobComplete.as_view(), name="job_complete"),
    path('jobs/archived/',  ArchivedJobsPage.as_view(), name="archived_jobs"),
    path('delete-job/<job_id>/', DeletejobPage.as_view(), name="delete_job"),
    path('profile/', ProfilePage.as_view(), name="profile"),
    path('details/', Driverdetails.as_view(), name="driver_details"),
   
    path('payout_method/', PayoutMethodPage.as_view(), name="payout_method"),
    path('change_avatar/', ChangeavatarPage.as_view(), name="change_avatar"),
    path('api/jobs/available/', courier_apis.available_jobs_api, name="available_jobs_api"),
    path('api/jobs/current/<id>/update/', courier_apis.current_job_update_api, name="current_job_update_api"),
    path('api/fcm-token/update/', courier_apis.fcm_token_update_api, name="fcm_token_update_api"),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Homes.as_view()),

    path('sign-in/', auth_views.LoginView.as_view(template_name="sign_in.html"),name='sign-in'),
    path('sign-out/', auth_views.LogoutView.as_view(next_page="/")),
    path('sign-up/', SignUp.as_view(),name="sign-up"),
    path('customer/', include((customer_urlpatters, 'customer'))),
    path('courier/', include((courier_urlpatters, 'courier'))),
    path('firebase-messaging-sw.js', (TemplateView.as_view(template_name="firebase-messaging-sw.js", content_type="application/javascript",))),

    path('reset_password/',
        auth_views.PasswordResetView.as_view(template_name="password_reset.html"),name='reset_password'),
    path('reset_password_sent/',auth_views.PasswordResetDoneView.as_view(template_name="password_reset_sent.html"),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_form.html"),name='password_reset_confirm'),
    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_done.html"),name='password_reset_complete'),
]

websocket_urlpatterns = [
    path("ws/jobs/<job_id>/", consumers.JobConsumer.as_asgi())
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "ONDMND.io"