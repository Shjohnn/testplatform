from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # Bosh sahifa
    path('', views.home, name='home'),
    
    # Admin Panel URLs
    path('custom-admin/login/', views.admin_login, name='admin_login'),
    path('custom-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/add-teacher/', views.add_teacher, name='add_teacher'),
    path('custom-admin/logout/', views.admin_logout, name='admin_logout'),
    
    # O'qituvchi Panel URLs
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher/create-test/', views.create_test, name='create_test'),
    path('teacher/upload-word/', views.upload_word_test, name='upload_word_test'),
    path('teacher/tests/', views.teacher_tests, name='teacher_tests'),
    path('teacher/test/<int:test_id>/results/', views.test_results, name='test_results'),
    path('teacher/test/<int:test_id>/analyze/<int:result_id>/', views.analyze_result, name='analyze_result'),
    path('teacher/test/<int:test_id>/start/', views.start_test, name='start_test'),
    path('teacher/test/<int:test_id>/stop/', views.stop_test, name='stop_test'),
    path('teacher/test/<int:test_id>/delete/', views.delete_test, name='delete_test'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    
    # O'quvchi Panel URLs
    path('student/join/', views.student_join, name='student_join'),
    path('student/waiting/<str:session_id>/', views.student_waiting, name='student_waiting'),
    path('student/test/<str:session_id>/', views.take_test, name='take_test'),
    path('student/submit/', views.submit_answer, name='submit_answer'),
    path('student/finish/<str:session_id>/', views.finish_test, name='finish_test'),
    path('student/result/<str:session_id>/', views.student_result, name='student_result'),
    
    # AJAX URLs
    path('check-test-status/<str:session_id>/', views.check_test_status, name='check_test_status'),
]
