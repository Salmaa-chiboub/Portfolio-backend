from django.urls import path
from .views import (
    HeroListView,
    HeroAdminListCreateView,
    HeroAdminDetailView,
    PublicAboutView,
    AboutDetailView,
    AboutCreateView,
    ContactCreateView,
    ContactListAdminView,
    ContactDetailAdminView,
)

urlpatterns = [
    # Public
    path('hero/', HeroListView.as_view(), name='hero_list'),
    path('about/', PublicAboutView.as_view(), name='about_public'),
    path('contact/', ContactCreateView.as_view(), name='contact_create'),

    # Admin
    path('admin/hero/', HeroAdminListCreateView.as_view(), name='hero_admin_list_create'),
    path('admin/hero/<int:pk>/', HeroAdminDetailView.as_view(), name='hero_admin_detail'),
    path('admin/about/<int:pk>/', AboutDetailView.as_view(), name='about_admin_detail'),
    path('admin/about/', AboutCreateView.as_view(), name='about_admin_create'),
    path('admin/contacts/', ContactListAdminView.as_view(), name='contact_admin_list'),
    path('admin/contacts/<int:pk>/', ContactDetailAdminView.as_view(), name='contact_admin_detail'),
]
