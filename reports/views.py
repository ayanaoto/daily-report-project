from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count, Sum
from django.http import HttpResponse
import csv
from datetime import timedelta

from .models import Report, Customer, Deal, Troubleshooting, RequiredItem
from .forms import ReportForm, CustomerForm, DealForm, TroubleshootingForm, RequiredItemForm, SignUpForm, ProfileForm

# ===================================================================
# アカウント関連 Views
# ===================================================================
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('reports:report_list')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)
        return response

@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('reports:report_list')
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'reports/profile_form.html', {'form': form})

# ===================================================================
# Report (日報) Views
# ===================================================================
class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = Report.objects.all()
        else:
            queryset = Report.objects.filter(author=self.request.user)
        
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(location__icontains=query) | Q(content__icontains=query))
        return queryset.order_by('-created_at')

class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'reports/report_detail.html'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Report.objects.all()
        return Report.objects.filter(author=self.request.user)

class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'reports/report_form.html'
    success_url = reverse_lazy('reports:report_list')

    def form_valid(self, form):
        hours = form.cleaned_data.get('hours', 0) or 0
        minutes = form.cleaned_data.get('minutes', 0) or 0
        form.instance.work_hours = timedelta(hours=hours, minutes=minutes)
        form.instance.author = self.request.user
        return super().form_valid(form)

class ReportUpdateView(LoginRequiredMixin, UpdateView):
    model = Report
    form_class = ReportForm
    template_name = 'reports/report_form.html'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Report.objects.all()
        return Report.objects.filter(author=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('reports:report_detail', kwargs={'pk': self.object.pk})
    
    def get_initial(self):
        initial = super().get_initial()
        if self.object.work_hours:
            total_seconds = self.object.work_hours.total_seconds()
            initial['hours'] = int(total_seconds // 3600)
            initial['minutes'] = int((total_seconds % 3600) // 60)
        return initial

    def form_valid(self, form):
        hours = form.cleaned_data.get('hours', 0) or 0
        minutes = form.cleaned_data.get('minutes', 0) or 0
        form.instance.work_hours = timedelta(hours=hours, minutes=minutes)
        return super().form_valid(form)

class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    template_name = 'reports/report_confirm_delete.html'
    success_url = reverse_lazy('reports:report_list')

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Report.objects.all()
        return Report.objects.filter(author=self.request.user)

# ===================================================================
# Customer (顧客) Views
# ===================================================================
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'reports/customer_list.html'
    context_object_name = 'customers'

class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'reports/customer_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        context['deals'] = Deal.objects.filter(customer=customer)
        return context

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'reports/customer_form.html'
    success_url = reverse_lazy('reports:customer_list')

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'reports/customer_form.html'
    
    def get_success_url(self):
        return reverse_lazy('reports:customer_detail', kwargs={'pk': self.object.pk})

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'reports/customer_confirm_delete.html'
    success_url = reverse_lazy('reports:customer_list')

# ===================================================================
# Deal (案件) Views
# ===================================================================
class DealListView(LoginRequiredMixin, ListView):
    model = Deal
    template_name = 'reports/deal_list.html'
    context_object_name = 'deals'

class DealDetailView(LoginRequiredMixin, DetailView):
    model = Deal
    template_name = 'reports/deal_detail.html'

class DealCreateView(LoginRequiredMixin, CreateView):
    model = Deal
    form_class = DealForm
    template_name = 'reports/deal_form.html'
    success_url = reverse_lazy('reports:deal_list')

class DealUpdateView(LoginRequiredMixin, UpdateView):
    model = Deal
    form_class = DealForm
    template_name = 'reports/deal_form.html'
    
    def get_success_url(self):
        return reverse_lazy('reports:deal_detail', kwargs={'pk': self.object.pk})

class DealDeleteView(LoginRequiredMixin, DeleteView):
    model = Deal
    template_name = 'reports/deal_confirm_delete.html'
    success_url = reverse_lazy('reports:report_list')

# ===================================================================
# Troubleshooting Views
# ===================================================================
class TroubleshootingListView(LoginRequiredMixin, ListView):
    model = Troubleshooting
    template_name = 'reports/troubleshooting_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(symptom__icontains=query) |
                Q(solution__icontains=query) | Q(keywords__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

class TroubleshootingDetailView(LoginRequiredMixin, DetailView):
    model = Troubleshooting
    template_name = 'reports/troubleshooting_detail.html'
    context_object_name = 'report'

class TroubleshootingCreateView(LoginRequiredMixin, CreateView):
    model = Troubleshooting
    form_class = TroubleshootingForm
    template_name = 'reports/troubleshooting_form.html'
    success_url = reverse_lazy('reports:troubleshooting_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class TroubleshootingUpdateView(LoginRequiredMixin, UpdateView):
    model = Troubleshooting
    form_class = TroubleshootingForm
    template_name = 'reports/troubleshooting_form.html'
    
    def get_success_url(self):
        return reverse_lazy('reports:troubleshooting_detail', kwargs={'pk': self.object.pk})

class TroubleshootingDeleteView(LoginRequiredMixin, DeleteView):
    model = Troubleshooting
    template_name = 'reports/troubleshooting_confirm_delete.html'
    success_url = reverse_lazy('reports:troubleshooting_list')
    context_object_name = 'report'

# ===================================================================
# ToDo (RequiredItem) Views
# ===================================================================
class TodoListView(LoginRequiredMixin, ListView):
    model = RequiredItem
    template_name = 'reports/todo_list.html'
    context_object_name = 'todos'

class TodoCreateView(LoginRequiredMixin, CreateView):
    model = RequiredItem
    form_class = RequiredItemForm
    template_name = 'reports/todo_form.html'
    success_url = reverse_lazy('reports:todo_list')

class TodoUpdateView(LoginRequiredMixin, UpdateView):
    model = RequiredItem
    form_class = RequiredItemForm
    template_name = 'reports/todo_form.html'
    success_url = reverse_lazy('reports:todo_list')

class TodoDeleteView(LoginRequiredMixin, DeleteView):
    model = RequiredItem
    template_name = 'reports/todo_confirm_delete.html'
    success_url = reverse_lazy('reports:todo_list')

@login_required
def todo_toggle(request, pk):
    todo = get_object_or_404(RequiredItem, pk=pk)
    todo.is_done = not todo.is_done
    todo.save()
    return redirect('reports:todo_list')

@login_required
def todo_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="todos.csv"'
    writer = csv.writer(response)
    writer.writerow(['Item', 'Deal', 'Status'])
    for todo in RequiredItem.objects.all():
        writer.writerow([todo.title, todo.deal, 'Done' if todo.is_done else 'Pending'])
    return response

# ===================================================================
# Dashboard
# ===================================================================
@login_required
def dashboard(request):
    # --- グラフ1：ユーザー別のレポート件数 ---
    reports_by_user = Report.objects.values('author__username').annotate(count=Count('id')).order_by('-count')
    user_chart_labels = [item['author__username'] for item in reports_by_user]
    user_chart_data = [item['count'] for item in reports_by_user]

    # --- グラフ2：個人の進捗件数（ログインユーザーのみ） ---
    progress_by_user = Report.objects.filter(author=request.user).values('progress').annotate(count=Count('id'))
    progress_map = dict(Report.PROGRESS_CHOICES)
    progress_chart_labels = [progress_map.get(item['progress'], '不明') for item in progress_by_user]
    progress_chart_data = [item['count'] for item in progress_by_user]

    # --- グラフ3：場所ごとの合計作業時間 ---
    hours_by_location = Report.objects.values('location').annotate(total_duration=Sum('work_hours')).order_by('-total_duration')
    location_chart_labels = []
    location_chart_data = []
    for item in hours_by_location:
        if item['total_duration']:
            hours = item['total_duration'].total_seconds() / 3600
            location_chart_labels.append(item['location'])
            location_chart_data.append(round(hours, 2))

    context = {
        'user_chart_labels': user_chart_labels,
        'user_chart_data': user_chart_data,
        'progress_chart_labels': progress_chart_labels,
        'progress_chart_data': progress_chart_data,
        'location_chart_labels': location_chart_labels,
        'location_chart_data': location_chart_data,
    }
    return render(request, 'reports/dashboard.html', context)