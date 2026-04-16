from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Client
from .forms import ClientForm
from common.tenant import get_tenant_object_or_404
from users.plan_guard import PlanGuard


@login_required
def client_list(request):
    clients = Client.objects.filter(contractor=request.user)
    q = request.GET.get('q', '')
    if q:
        clients = clients.filter(name__icontains=q)
    return render(request, 'clients/list.html', {'clients': clients, 'q': q})


@login_required
def client_create(request):
    allowed, msg = PlanGuard.can_create_client(request.user)
    if not allowed:
        messages.warning(request, msg)
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
    client = get_tenant_object_or_404(Client, request, pk=pk)
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
    client = get_tenant_object_or_404(Client, request, pk=pk)
    if request.method == 'POST':
        name = client.name
        client.delete()
        messages.success(request, f'Cliente "{name}" eliminado.')
        return redirect('client_list')
    return render(request, 'clients/confirm_delete.html', {'client': client})


@login_required
def client_detail(request, pk):
    from budgets.models import Budget
    client = get_tenant_object_or_404(Client, request, pk=pk)
    budgets = (
        Budget.objects
        .filter(client=client, contractor=request.user)
        .select_related('contractor')
        .with_totals()
    )
    return render(request, 'clients/detail.html', {'client': client, 'budgets': budgets})
