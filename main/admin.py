from django.contrib import admin
from .models import Teacher, Test, Question, StudentResult, StudentAnswer


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'username', 'created_at']
    search_fields = ['full_name', 'username']
    list_filter = ['created_at']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['name', 'test_id', 'teacher', 'timer', 'is_active', 'created_at']
    search_fields = ['name', 'test_id', 'teacher__full_name']
    list_filter = ['is_active', 'created_at', 'teacher']
    readonly_fields = ['created_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['test', 'question_text', 'correct_answer', 'order']
    search_fields = ['question_text', 'test__name']
    list_filter = ['test', 'correct_answer']
    ordering = ['test', 'order']


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'test', 'correct_answers', 'total_questions', 'percentage', 'is_completed', 'started_at']
    search_fields = ['student_name', 'test__name']
    list_filter = ['is_completed', 'started_at', 'test']
    readonly_fields = ['started_at', 'completed_at', 'session_id']


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['student_result', 'question', 'student_answer', 'is_correct', 'answered_at']
    search_fields = ['student_result__student_name', 'question__question_text']
    list_filter = ['is_correct', 'answered_at']
    readonly_fields = ['answered_at']
