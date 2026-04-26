from django.shortcuts import render


def rate_limited_view(request, exception):
    return render(request, "429.html", status=429)
