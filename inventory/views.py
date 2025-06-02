from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from .models import Prop, UsageLog, PropUse, Borrower, UserProfile, User
from django.urls import reverse_lazy
from django.db.models import Count
from functools import wraps
from pprint import pprint
from django.utils import timezone
from django.db import models
from django.db.models.functions import TruncMonth
from datetime import timedelta

def is_admin(user):
    return user.is_authenticated and user.profile.is_admin

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        if not request.user.profile.is_admin:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def borrower_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        if not request.user.profile.is_borrower:
            messages.error(request, "This page is only for borrowers.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def login_view(request):
    # If user is already logged in, redirect to appropriate page
    if request.user.is_authenticated:
        if request.user.profile.is_admin:
            messages.info(request, "Welcome back, Administrator!")
            return redirect('dashboard')
        else:
            messages.info(request, f"Welcome back, {request.user.username}!")
            return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check if user is admin and set appropriate message
            if user.profile.is_admin:
                messages.success(request, f"Welcome, Administrator {user.username}!")
                return redirect('dashboard')
            else:
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('home')
        else:
            # Check if username exists to provide more specific error message
            try:
                User.objects.get(username=username)
                messages.error(request, "Invalid password. Please try again.")
            except User.DoesNotExist:
                messages.error(request, "Invalid username. Please check your credentials.")
    
    return render(request, 'inventory/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def home(request):
    if request.user.profile.is_admin:
        return render(request, 'inventory/home.html')
    else:
        # For borrowers, show only available props
        props = Prop.objects.filter(quantity__gt=0)
        return render(request, 'inventory/borrower_home.html', {'props': props})

# Prop Views
class PropListView(LoginRequiredMixin, ListView):
    model = Prop
    template_name = 'inventory/prop_list.html'
    context_object_name = 'props'

    def get_queryset(self):
        if self.request.user.profile.is_admin:
            return Prop.objects.all()
        else:
            # Borrowers can only see available props
            return Prop.objects.filter(quantity__gt=0)

    def get_template_names(self):
        if self.request.user.profile.is_admin:
            return ['inventory/prop_list.html']
        else:
            return ['inventory/borrower_prop_list.html']

class PropCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Prop
    template_name = 'inventory/prop_form.html'
    fields = ['name', 'category', 'quantity', 'condition', 'storage_location', 'image']
    success_url = reverse_lazy('prop_list')

    def test_func(self):
        return is_admin(self.request.user)

class PropUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Prop
    template_name = 'inventory/prop_form.html'
    fields = ['name', 'category', 'quantity', 'condition', 'storage_location', 'image']
    success_url = reverse_lazy('prop_list')

    def test_func(self):
        return is_admin(self.request.user)

class PropDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Prop
    template_name = 'inventory/prop_confirm_delete.html'
    success_url = reverse_lazy('prop_list')

    def test_func(self):
        return is_admin(self.request.user)

# Borrower Views
@login_required
@admin_required
def borrower_list(request):
    borrowers = Borrower.objects.all()
    return render(request, 'inventory/borrower_list.html', {'borrowers': borrowers})

@login_required
@admin_required
def borrower_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Borrower.objects.create(name=name)
            messages.success(request, f"Borrower '{name}' added successfully.")
            return redirect('borrower_list')
        else:
            messages.error(request, "Name cannot be empty.")
    return render(request, 'inventory/borrower_form.html', {'action': 'Add'})

@login_required
@admin_required
def borrower_edit(request, borrower_id):
    borrower = get_object_or_404(Borrower, id=borrower_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            borrower.name = name
            borrower.save()
            messages.success(request, f"Borrower '{name}' updated successfully.")
            return redirect('borrower_list')
        else:
            messages.error(request, "Name cannot be empty.")
    return render(request, 'inventory/borrower_form.html', {'borrower': borrower, 'action': 'Edit'})

# UsageLog Views
class UsageLogListView(ListView):
    model = UsageLog
    template_name = 'inventory/usagelog_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(date_of_use=date)
        return queryset

@login_required
@admin_required
def reports(request):
    # Most used props
    most_used = PropUse.objects.values('prop__name').annotate(
        total=Count('id'),
        active=Count('id', filter=models.Q(return_status='borrowed')),
        returned=Count('id', filter=models.Q(return_status='returned')),
        damaged=Count('id', filter=models.Q(return_status='damaged')),
        missing=Count('id', filter=models.Q(return_status='missing'))
    ).order_by('-total')[:10]

    # Category-wise statistics
    category_stats = Prop.objects.values('category').annotate(
        total_props=Count('id'),
        total_quantity=models.Sum('quantity'),
        low_stock=Count('id', filter=models.Q(quantity__lt=5))
    ).order_by('-total_props')

    # Monthly borrowing trends
    monthly_trends = PropUse.objects.annotate(
        month=TruncMonth('used_at')
    ).values('month').annotate(
        total_borrowings=Count('id'),
        unique_props=Count('prop', distinct=True),
        unique_users=Count('used_by', distinct=True)
    ).order_by('-month')[:12]

    # User borrowing statistics
    user_stats = PropUse.objects.values('used_by_name').annotate(
        total_borrowings=Count('id'),
        active_borrowings=Count('id', filter=models.Q(return_status='borrowed')),
        overdue_returns=Count('id', filter=models.Q(
            return_status='borrowed',
            used_at__lt=timezone.now() - timezone.timedelta(days=7)
        ))
    ).order_by('-total_borrowings')[:10]

    context = {
        'most_used': most_used,
        'category_stats': category_stats,
        'monthly_trends': monthly_trends,
        'user_stats': user_stats,
    }
    return render(request, 'inventory/reports.html', context)

@login_required
@admin_required
def dashboard(request):
    # Basic statistics
    total_props = Prop.objects.count()
    total_borrowers = Borrower.objects.count()
    
    # Active borrowings (currently borrowed props)
    active_borrowings = PropUse.objects.filter(return_status='borrowed').count()
    
    # Overdue returns (borrowed for more than 7 days)
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    overdue_returns = PropUse.objects.filter(
        return_status='borrowed',
        used_at__lt=seven_days_ago
    ).count()
    
    # Recent usage (last 5 borrowings)
    recent_usage = PropUse.objects.select_related('prop', 'used_by').order_by('-used_at')[:5]
    
    # Low stock items (quantity less than 5)
    low_stock_props = Prop.objects.filter(quantity__lt=5).order_by('quantity')
    
    # Most borrowed props (top 5)
    most_borrowed_props = Prop.objects.annotate(
        borrow_count=models.Count('propuse')
    ).order_by('-borrow_count')[:5]
    
    context = {
        'total_props': total_props,
        'total_borrowers': total_borrowers,
        'active_borrowings': active_borrowings,
        'overdue_returns': overdue_returns,
        'recent_usage': recent_usage,
        'low_stock_props': low_stock_props,
        'most_borrowed_props': most_borrowed_props,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
@borrower_required
def use_prop(request, prop_id):
    prop = get_object_or_404(Prop, id=prop_id)
    
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        event_name = request.POST.get('event_name')
        
        if quantity and quantity.isdigit() and event_name:
            quantity = int(quantity)
            if quantity > 0 and quantity <= prop.quantity:
                # Create usage record
                PropUse.objects.create(
                    prop=prop,
                    quantity=quantity,
                    used_by=request.user,
                    used_by_name=request.user.username,
                    event_name=event_name
                )
                # Update prop quantity
                prop.quantity -= quantity
                prop.save()
                messages.success(request, f"Successfully borrowed {quantity} {prop.name} for {event_name}.")
                return redirect('home')
            else:
                messages.error(request, "Invalid quantity. Please check available quantity.")
        else:
            messages.error(request, "Please enter a valid quantity and event name.")

    return render(request, 'inventory/borrower_use_prop.html', {'prop': prop})

@login_required
@borrower_required
def my_borrowings(request):
    # Base queryset for current user's borrowings
    queryset = PropUse.objects.filter(used_by=request.user)
    
    # Apply status filter
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(return_status=status)
    
    # Apply sorting
    sort = request.GET.get('sort', '-used_at')  # Default to newest first
    if sort:
        queryset = queryset.order_by(sort)
    
    # Add select_related for performance
    queryset = queryset.select_related('prop', 'used_by')
    
    # Check for recently returned props (within the last 24 hours)
    recent_returns = queryset.filter(
        return_status='returned',
        return_date__gte=timezone.now() - timedelta(days=1)
    )
    
    # Add success messages for recently returned props
    for prop_use in recent_returns:
        messages.success(
            request,
            f"Your prop '{prop_use.prop.name}' has been returned and confirmed by the administrator."
        )
    
    return render(request, 'inventory/my_borrowings.html', {
        'borrowings': queryset,
        'recent_returns': recent_returns,
        'current_filters': {
            'status': status,
            'sort': sort,
        }
    })

@login_required
def prop_use_history(request, prop_id):
    prop = get_object_or_404(Prop, id=prop_id)
    use_logs = PropUse.objects.filter(prop=prop).order_by('-timestamp')

    return render(request, 'inventory/prop_use_history.html', {
        'prop': prop,
        'use_logs': use_logs
    })

@login_required
def borrowed_props_list(request):
    # Base queryset
    if request.user.profile.is_borrower:
        queryset = PropUse.objects.filter(used_by=request.user)
    else:
        queryset = PropUse.objects.all()
    
    # Apply status filter
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(return_status=status)
    
    # Apply sorting
    sort = request.GET.get('sort', '-used_at')  # Default to newest first
    if sort:
        queryset = queryset.order_by(sort)
    
    # Add select_related for performance
    queryset = queryset.select_related('prop', 'used_by')
    
    return render(request, 'inventory/borrowed_props_list.html', {
        'borrowed_props': queryset,
        'current_filters': {
            'status': status,
            'sort': sort,
        }
    })

@login_required
@admin_required
def return_prop(request, prop_use_id):
    prop_use = get_object_or_404(PropUse, id=prop_use_id)
    
    if request.method == 'POST':
        status = request.POST.get('return_status', 'returned')
        notes = request.POST.get('return_notes', '')
        
        try:
            prop_use.mark_as_returned(status=status, notes=notes)
            messages.success(request, f"Successfully returned {prop_use.prop.name}")
            return redirect('borrowed_props_list')
        except Exception as e:
            messages.error(request, f"Error returning prop: {str(e)}")
    
    return render(request, 'inventory/return_prop.html', {
        'prop_use': prop_use
    })
