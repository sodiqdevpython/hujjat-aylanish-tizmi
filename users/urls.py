from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    path("teachers/", views.TeacherListView.as_view(), name="teacher_list"),
    path('teachers/create/', views.create_teacher, name='teacher_create'),
    path('users/<int:pk>/', views.user_profile_detail, name='user_profile_detail'),
    path('users/edit/<int:pk>/', views.teacher_update_view, name='user_profile_update'),

    path('ilmiy_ishlar_list/', views.ilmiy_ishlar_list, name='ilmiy_ishlar_list'),
    path('ilmiy-ish/<int:pk>/', views.ilmiy_ish_detail, name='ilmiy_ish_detail'),
    path('ilmiy-ish/<int:pk>/status/', views.update_document_status, name='update_document_status'),
    

    path('users/<int:teacher_id>/requirements/add/', views.add_requirement, name='add_requirement'),
    path('work-plan/', views.work_plan_report, name='work_plan_report'),
    path("work-plan/export/", views.work_plan_export, name="work_plan_export"),

    path("notifications/", views.notification_list, name="notif_list"),
    path("doc/<int:pk>/approve/", views.doc_approve_detail, name="doc_approve_detail"),

    #teacher
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path("my-profile/", views.my_profile, name="my_profile"),
    path("my-documents/", views.my_documents, name="my_documents"),
    path("my-requirements/", views.my_requirements_view, name="my_requirements"),
    path('teacher-notifications/', views.my_notifications, name='my_notifications'),
    path('document-create', views.document_create, name='document_create')

]