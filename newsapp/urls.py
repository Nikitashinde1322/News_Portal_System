from django.urls import path   
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('landing/', views.landing, name='landing_page'),
    path('home/', views.home, name='home'),
    path('add-news/', views.add_news, name='add_news'),
    path('delete/<int:id>/', views.delete_news, name='delete'),
    path('edit/<int:id>/', views.edit_news, name='edit'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('approve-news/', views.approve_news, name='approve_news'),
    path('pending-news/', views.pending_news, name='pending_news'),
    path('approved-news/', views.approved_news, name='approved_news'),
    path('manage-categories/', views.manage_categories, name='manage_categories'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.custom_logout, name='logout'),
    path('like/<int:id>/', views.like_news, name='like_news'),
    path('comment/<int:id>/', views.add_comment, name='add_comment'),
    path('bookmark/<int:id>/', views.toggle_bookmark, name='bookmark'),
    path('redirect/', views.role_redirect, name='role_redirect'),
    path('api/news/',views.news_api),
    path('api/trending-news/', views.trending_news_api, name='trending_news_api'),
]