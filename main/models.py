from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Teacher(models.Model):
    """O'qituvchi modeli"""
    full_name = models.CharField(max_length=200, verbose_name="To'liq ism")
    username = models.CharField(max_length=100, unique=True, verbose_name="Foydalanuvchi nomi")
    password = models.CharField(max_length=128, verbose_name="Parol")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = "O'qituvchi"
        verbose_name_plural = "O'qituvchilar"


class Test(models.Model):
    """Test modeli"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='tests', verbose_name="O'qituvchi")
    name = models.CharField(max_length=300, verbose_name="Test nomi")
    description = models.TextField(blank=True, verbose_name="Izoh")
    test_id = models.CharField(max_length=50, unique=True, verbose_name="Test ID")
    password = models.CharField(max_length=128, verbose_name="Test paroli")
    timer = models.IntegerField(help_text="Daqiqalarda", verbose_name="Timer")
    word_file = models.FileField(upload_to='test_files/', blank=True, null=True, verbose_name="Word fayl")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    is_active = models.BooleanField(default=False, verbose_name="Test faolmi")
    
    def __str__(self):
        return f"{self.name} ({self.test_id})"
    
    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Testlar"
        ordering = ['-created_at']


class Question(models.Model):
    """Savol modeli"""
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', verbose_name="Test")
    question_text = models.TextField(verbose_name="Savol matni")
    option_a = models.CharField(max_length=500, verbose_name="A variant")
    option_b = models.CharField(max_length=500, verbose_name="B variant")
    option_c = models.CharField(max_length=500, verbose_name="C variant")
    option_d = models.CharField(max_length=500, verbose_name="D variant")
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], verbose_name="To'g'ri javob")
    order = models.IntegerField(default=0, verbose_name="Tartib")
    
    def __str__(self):
        return f"{self.test.name} - Savol {self.order}"
    
    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ['test', 'order']


class StudentResult(models.Model):
    """Talaba natijasi modeli"""
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results', verbose_name="Test")
    student_name = models.CharField(max_length=200, verbose_name="Talaba ismi")
    total_questions = models.IntegerField(verbose_name="Jami savollar soni")
    correct_answers = models.IntegerField(default=0, verbose_name="To'g'ri javoblar soni")
    wrong_answers = models.IntegerField(default=0, verbose_name="Noto'g'ri javoblar soni")
    percentage = models.FloatField(default=0, verbose_name="Natija (%)")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Boshlangan vaqt")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Yakunlangan vaqt")
    is_completed = models.BooleanField(default=False, verbose_name="Yakunlanganmi")
    session_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4, verbose_name="Session ID")
    
    def __str__(self):
        return f"{self.student_name} - {self.test.name}"
    
    def calculate_result(self):
        """Natijani hisoblash"""
        total_answered = self.correct_answers + self.wrong_answers
        if self.total_questions > 0:
            self.percentage = (self.correct_answers / self.total_questions) * 100
        else:
            self.percentage = 0
        self.save()
    
    class Meta:
        verbose_name = "Talaba natijasi"
        verbose_name_plural = "Talaba natijalari"
        ordering = ['-started_at']


class StudentAnswer(models.Model):
    """Talaba javoblari modeli"""
    student_result = models.ForeignKey(StudentResult, on_delete=models.CASCADE, related_name='answers', verbose_name="Talaba natijasi")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Savol")
    student_answer = models.CharField(max_length=1, blank=True, null=True, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], verbose_name="Talaba javobi")
    is_correct = models.BooleanField(default=False, verbose_name="To'g'rimi")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Javob berilgan vaqt")
    
    def __str__(self):
        return f"{self.student_result.student_name} - {self.question.question_text[:50]}"
    
    def check_answer(self):
        """Javobni tekshirish"""
        if self.student_answer:
            self.is_correct = (self.student_answer == self.question.correct_answer)
        else:
            self.is_correct = False
        self.save()
    
    class Meta:
        verbose_name = "Talaba javobi"
        verbose_name_plural = "Talaba javoblari"
        ordering = ['student_result', 'question__order']
