from django.shortcuts import render


def landing_page(request):
    """
    Landing page view for TaxMoja
    """
    return render(request, 'index.html')


def eula_page(request):
    """
    End-User License Agreement page
    """
    return render(request, 'eula.html')
