from django.urls import path
from .views import (
    PropListView, PropCreateView, PropUpdateView, PropDeleteView,
    borrower_list, borrower_add, borrower_edit,
    dashboard, use_prop, prop_use_history,
    login_view, logout_view, home, my_borrowings,
    borrowed_props_list, return_prop, reports
)

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('props/', PropListView.as_view(), name='prop_list'),
    path('props/add/', PropCreateView.as_view(), name='prop_add'),
    path('props/<int:pk>/edit/', PropUpdateView.as_view(), name='prop_edit'),
    path('props/<int:pk>/delete/', PropDeleteView.as_view(), name='prop_delete'),

    path('borrowers/', borrower_list, name='borrower_list'),
    path('borrowers/add/', borrower_add, name='borrower_add'),
    path('borrowers/<int:borrower_id>/edit/', borrower_edit, name='borrower_edit'),

    path('dashboard/', dashboard, name='dashboard'),
    path('reports/', reports, name='reports'),
    path('props/<int:prop_id>/use/', use_prop, name='use_prop'),
    path('props/<int:prop_id>/usage/', prop_use_history, name='prop_use_history'),

    path('my-borrowings/', my_borrowings, name='my_borrowings'),

    path('borrowed-props/', borrowed_props_list, name='borrowed_props_list'),
    path('return-prop/<int:prop_use_id>/', return_prop, name='return_prop'),

    # other URLs...
]
