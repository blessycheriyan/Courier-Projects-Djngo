
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.generic.base import View
from . import forms

# Create your views here.


class Homes(View):
    def get(self, request):
        return render(request, 'home.html')


class SignUp(View):
    def get(self, request):
        form = forms.SignUpForm()
        context = {
            'form': form,

        }
        return render(request, 'sign_up.html', context)

    def post(self, request):
        form = forms.SignUpForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get('email').lower()

            user = form.save(commit=False)
            user.username = email
            user.save()
            login(request, user)

            return redirect('sign-in')

        return render(request, 'sign_up.html', {
            'form': form
        })
