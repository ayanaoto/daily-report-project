from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse

def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # ログイン後の行き先（必要に応じて変更）
            return redirect("/reports/")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
