from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Client
from .forms import ClientForm


@login_required
def client_list(request):
    clients = Client.objects.filter(contractor=request.user)
    q = request.GET.get('q', '')
    if q:
        clients = clients.filter(name__icontains=q)
    return render(request, 'clients/list.html', {'clients': clients, 'q': q})


@login_required
def client_create(request):
    if not request.user.is_pro():
        count = Client.objects.filter(contractor=request.user).count()
        if count >= settings.PLAN_FREE_MAX_CLIENTS:
            messages.warning(request, f'Alcanzaste el límite de {settings.PLAN_FREE_MAX_CLIENTS} clientes del plan gratuito. ¡Actualiza a Pro!')
            return redirect('client_list')

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.contractor = request.user
            client.save()
            messages.success(request, f'Cliente "{client.name}" creado exitosamente.')
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'clients/form.html', {'form': form, 'action': 'Crear'})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, contractor=request.user)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado.')
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/form.html', {'form': form, 'action': 'Editar', 'client': client})


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, contractor=request.user)
    if request.method == 'POST':
        name = client.name
        client.delete()
        messages.success(request, f'Cliente "{name}" eliminado.')
        return redirect('client_list')
    return render(request, 'clients/confirm_delete.html', {'client': client})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk, contractor=request.user)
    budgets = client.budgets.all()
    return render(request, 'clients/detail.html', {'client': client, 'budgets': budgets})
