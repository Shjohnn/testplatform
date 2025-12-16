from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Teacher, Test, Question, StudentResult, StudentAnswer
from django.contrib.auth.hashers import make_password, check_password
import docx
import uuid
import json


# ==================== HOME PAGE ====================
def home(request):
    """Bosh sahifa"""
    return render(request, 'home.html')


# ==================== ADMIN PANEL ====================
def admin_login(request):
    """Admin login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Simple admin credentials (username: admin, password: admin123)
        if username == 'admin' and password == 'admin123':
            request.session['admin_logged_in'] = True
            return redirect('main:admin_dashboard')
        else:
            messages.error(request, 'Noto\'g\'ri username yoki parol!')
    
    return render(request, 'admin_login.html')


def admin_dashboard(request):
    """Admin dashboard - O'qituvchilar ro'yxati"""
    if not request.session.get('admin_logged_in'):
        return redirect('main:admin_login')
    
    teachers = Teacher.objects.all().order_by('-created_at')
    return render(request, 'admin_dashboard.html', {'teachers': teachers})


def add_teacher(request):
    """O'qituvchi qo'shish"""
    if not request.session.get('admin_logged_in'):
        return redirect('main:admin_login')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if username already exists
        if Teacher.objects.filter(username=username).exists():
            messages.error(request, 'Bu username allaqachon mavjud!')
        else:
            teacher = Teacher.objects.create(
                full_name=full_name,
                username=username,
                password=make_password(password)
            )
            messages.success(request, f'{full_name} muvaffaqiyatli qo\'shildi!')
            return redirect('main:admin_dashboard')
    
    return render(request, 'add_teacher.html')


def admin_logout(request):
    """Admin logout"""
    request.session.flush()
    return redirect('main:home')


# ==================== TEACHER PANEL ====================
def teacher_login(request):
    """O'qituvchi login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            teacher = Teacher.objects.get(username=username)
            if check_password(password, teacher.password):
                request.session['teacher_id'] = teacher.id
                request.session['teacher_name'] = teacher.full_name
                return redirect('main:teacher_profile')
            else:
                messages.error(request, 'Noto\'g\'ri parol!')
        except Teacher.DoesNotExist:
            messages.error(request, 'O\'qituvchi topilmadi!')
    
    return render(request, 'teacher_login.html')


def teacher_profile(request):
    """O'qituvchi profil"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    teacher = get_object_or_404(Teacher, id=teacher_id)
    tests = Test.objects.filter(teacher=teacher).order_by('-created_at')
    
    return render(request, 'teacher_profile.html', {
        'teacher': teacher,
        'tests': tests
    })


def create_test(request):
    """Test yaratish (manual)"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        test_id = request.POST.get('test_id')
        password = request.POST.get('password')
        timer = request.POST.get('timer')
        
        # Check if test_id exists
        if Test.objects.filter(test_id=test_id).exists():
            messages.error(request, 'Bu Test ID allaqachon mavjud!')
            return render(request, 'create_test.html')
        
        # Create test
        test = Test.objects.create(
            teacher=teacher,
            name=name,
            description=description,
            test_id=test_id,
            password=make_password(password),
            timer=int(timer)
        )
        
        # Create questions
        question_count = int(request.POST.get('question_count', 0))
        for i in range(1, question_count + 1):
            question_text = request.POST.get(f'question_{i}')
            option_a = request.POST.get(f'option_a_{i}')
            option_b = request.POST.get(f'option_b_{i}')
            option_c = request.POST.get(f'option_c_{i}')
            option_d = request.POST.get(f'option_d_{i}')
            correct_answer = request.POST.get(f'correct_{i}')
            
            Question.objects.create(
                test=test,
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=correct_answer,
                order=i
            )
        
        messages.success(request, 'Test muvaffaqiyatli yaratildi!')
        return redirect('main:teacher_profile')
    
    return render(request, 'create_test.html')


def upload_word_test(request):
    """Word file orqali test yuklash"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        test_id = request.POST.get('test_id')
        password = request.POST.get('password')
        timer = request.POST.get('timer')
        word_file = request.FILES.get('word_file')
        
        if Test.objects.filter(test_id=test_id).exists():
            messages.error(request, 'Bu Test ID allaqachon mavjud!')
            return render(request, 'upload_word_test.html')
        
        # Create test
        test = Test.objects.create(
            teacher=teacher,
            name=name,
            description=description,
            test_id=test_id,
            password=make_password(password),
            timer=int(timer),
            word_file=word_file
        )
        
        # Parse Word file
        try:
            import re
            doc = docx.Document(word_file)
            questions_data = []
            current_question = None
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                # Regex patterns for options
                # Matches: "A)", "A) text", "* A)", "* A) text", "*A)", "*A) text"
                option_pattern = r'^(\*\s*)?([A-D])\)\s*(.*)$'
                match = re.match(option_pattern, text)
                
                if match:
                    # It's an option
                    if current_question is None:
                        continue
                    
                    is_correct = match.group(1) is not None  # Has asterisk
                    option_letter = match.group(2)  # A, B, C, or D
                    option_text = match.group(3).strip()  # Option text
                    
                    current_question['options'][option_letter] = option_text
                    if is_correct:
                        current_question['correct'] = option_letter
                else:
                    # It's a question (or title/header - skip if short or no previous question yet)
                    if current_question and current_question.get('question'):
                        questions_data.append(current_question)
                    current_question = {
                        'question': text,
                        'options': {'A': '', 'B': '', 'C': '', 'D': ''},
                        'correct': None
                    }
            
            # Add last question
            if current_question and current_question.get('question'):
                questions_data.append(current_question)
            
            # Validate questions
            valid_questions = []
            for q in questions_data:
                if not q.get('correct'):
                    continue  # Skip questions without correct answer
                if not q.get('question'):
                    continue  # Skip empty questions
                # Check if all 4 options exist and not empty
                if all(q['options'].get(opt) for opt in ['A', 'B', 'C', 'D']):
                    valid_questions.append(q)
            
            if not valid_questions:
                raise ValueError("Word faylda to'g'ri formatted savollar topilmadi. Iltimos formatni tekshiring.")
            
            # Create questions in database
            for idx, q_data in enumerate(valid_questions, 1):
                Question.objects.create(
                    test=test,
                    question_text=q_data['question'],
                    option_a=q_data['options']['A'],
                    option_b=q_data['options']['B'],
                    option_c=q_data['options']['C'],
                    option_d=q_data['options']['D'],
                    correct_answer=q_data['correct'],
                    order=idx
                )
            
            messages.success(request, f'Test muvaffaqiyatli yaratildi! {len(valid_questions)} ta savol qo\'shildi.')
            return redirect('main:teacher_profile')
            
        except Exception as e:
            test.delete()
            messages.error(request, f'Word faylni o\'qishda xatolik: {str(e)}')
    
    return render(request, 'upload_word_test.html')


def teacher_tests(request):
    """O'qituvchi testlari ro'yxati"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    teacher = get_object_or_404(Teacher, id=teacher_id)
    tests = Test.objects.filter(teacher=teacher).order_by('-created_at')
    
    return render(request, 'teacher_tests.html', {'tests': tests})


def test_results(request, test_id):
    """Test natijalari"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    test = get_object_or_404(Test, id=test_id)
    results = StudentResult.objects.filter(test=test, is_completed=True).order_by('-percentage')
    
    return render(request, 'test_results.html', {
        'test': test,
        'results': results
    })


def analyze_result(request, test_id, result_id):
    """Natijani tahlil qilish"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    result = get_object_or_404(StudentResult, id=result_id, test_id=test_id)
    answers = StudentAnswer.objects.filter(student_result=result).select_related('question').order_by('question__order')
    
    return render(request, 'analyze_result.html', {
        'result': result,
        'answers': answers
    })


def start_test(request, test_id):
    """Testni boshlash (o'qituvchi tomonidan)"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    test = get_object_or_404(Test, id=test_id)
    test.is_active = True
    test.save()
    
    messages.success(request, 'Test faollashtirildi! O\'quvchilar endi testni boshlashlari mumkin.')
    return redirect('main:teacher_profile')


def stop_test(request, test_id):
    """Testni to'xtatish (o'qituvchi tomonidan)"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    test = get_object_or_404(Test, id=test_id)
    test.is_active = False
    test.save()
    
    messages.warning(request, 'Test to\'xtatildi!')
    return redirect('main:teacher_profile')


def delete_test(request, test_id):
    """Testni o'chirish (o'qituvchi tomonidan)"""
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('main:teacher_login')
    
    test = get_object_or_404(Test, id=test_id, teacher_id=teacher_id)
    test_name = test.name
    test.delete()
    
    messages.success(request, f'"{test_name}" testi o\'chirildi!')
    return redirect('main:teacher_profile')


def teacher_logout(request):
    """O'qituvchi logout"""
    request.session.flush()
    return redirect('main:home')


# ==================== STUDENT PANEL ====================
def student_join(request):
    """O'quvchi test join"""
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        test_id = request.POST.get('test_id')
        password = request.POST.get('password')
        
        try:
            test = Test.objects.get(test_id=test_id)
            if check_password(password, test.password):
                # Create student result
                session_id = str(uuid.uuid4())
                student_result = StudentResult.objects.create(
                    test=test,
                    student_name=student_name,
                    total_questions=test.questions.count(),
                    session_id=session_id
                )
                
                # Create empty answers for all questions
                for question in test.questions.all():
                    StudentAnswer.objects.create(
                        student_result=student_result,
                        question=question
                    )
                
                request.session['student_session_id'] = session_id
                return redirect('main:student_waiting', session_id=session_id)
            else:
                messages.error(request, 'Noto\'g\'ri parol!')
        except Test.DoesNotExist:
            messages.error(request, 'Test topilmadi!')
    
    return render(request, 'student_join.html')


def student_waiting(request, session_id):
    """Kutish sahifasi"""
    result = get_object_or_404(StudentResult, session_id=session_id)
    
    if result.test.is_active:
        return redirect('main:take_test', session_id=session_id)
    
    return render(request, 'student_waiting.html', {
        'result': result,
        'session_id': session_id
    })


def take_test(request, session_id):
    """Test yechish"""
    result = get_object_or_404(StudentResult, session_id=session_id)
    
    if not result.test.is_active:
        return redirect('main:student_waiting', session_id=session_id)
    
    questions = result.test.questions.all().order_by('order')
    answers = StudentAnswer.objects.filter(student_result=result).select_related('question')
    
    # Create a dict for easier template access
    answer_dict = {ans.question_id: ans.student_answer for ans in answers}
    
    return render(request, 'take_test.html', {
        'result': result,
        'questions': questions,
        'session_id': session_id,
        'answer_dict': answer_dict
    })


@csrf_exempt
def submit_answer(request):
    """Javobni saqlash (AJAX)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        try:
            result = StudentResult.objects.get(session_id=session_id)
            student_answer = StudentAnswer.objects.get(
                student_result=result,
                question_id=question_id
            )
            student_answer.student_answer = answer
            student_answer.check_answer()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})


def finish_test(request, session_id):
    """Testni yakunlash"""
    result = get_object_or_404(StudentResult, session_id=session_id)
    
    # Calculate results
    answers = StudentAnswer.objects.filter(student_result=result)
    correct_count = answers.filter(is_correct=True).count()
    wrong_count = answers.filter(student_answer__isnull=False, is_correct=False).count()
    
    result.correct_answers = correct_count
    result.wrong_answers = wrong_count
    result.is_completed = True
    result.completed_at = timezone.now()
    result.calculate_result()
    
    return redirect('main:student_result', session_id=session_id)


def student_result(request, session_id):
    """O'quvchi natijasi"""
    result = get_object_or_404(StudentResult, session_id=session_id)
    
    return render(request, 'student_result.html', {'result': result})


# ==================== AJAX ====================
def check_test_status(request, session_id):
    """Test faolligini tekshirish (AJAX)"""
    try:
        result = StudentResult.objects.get(session_id=session_id)
        return JsonResponse({
            'is_active': result.test.is_active
        })
    except StudentResult.DoesNotExist:
        return JsonResponse({'is_active': False})
