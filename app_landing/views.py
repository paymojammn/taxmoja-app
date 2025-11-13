from django.shortcuts import render


def landing_page(request):
    """
    Landing page view for TaxMoja
    """
    return render(request, 'landing.html')
