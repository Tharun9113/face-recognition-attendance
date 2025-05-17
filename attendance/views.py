from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView
from .forms import UserRegisterForm, StudentProfileForm, TeacherProfileForm, FaceImageForm
from .models import Student, Teacher, Attendance, Profile, PasswordResetOTP
import face_recognition
import cv2
import numpy as np
from datetime import datetime
import os
from django.contrib.auth import logout, authenticate, login
from django.core.mail import send_mail
from django.contrib.auth.models import User
import random
import string
from django.conf import settings
from django.contrib.auth.views import LoginView

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}!')
            
            # Redirect based on role
            if user.profile.is_student:
                return redirect('student-profile')
            elif user.profile.is_teacher:
                return redirect('teacher-profile')
    else:
        form = UserRegisterForm()
    return render(request, 'attendance/register.html', {'form': form})

@login_required
def student_profile(request):
    # Check if user already has a student profile
    try:
        existing_student = Student.objects.get(profile=request.user.profile)
        messages.info(request, 'You already have a student profile.')
        return redirect('face-registration')
    except Student.DoesNotExist:
        pass

    if request.method == 'POST':
        form = StudentProfileForm(request.POST)
        if form.is_valid():
            try:
                student = form.save(commit=False)
                student.profile = request.user.profile
                student.save()
                messages.success(request, 'Student profile created successfully!')
                return redirect('face-registration')
            except Exception as e:
                messages.error(request, f'Error creating profile: {str(e)}')
    else:
        form = StudentProfileForm()
    return render(request, 'attendance/student_profile.html', {'form': form})

@login_required
def teacher_profile(request):
    if request.method == 'POST':
        form = TeacherProfileForm(request.POST)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.profile = request.user.profile
            teacher.save()
            messages.success(request, 'Teacher profile created successfully!')
            return redirect('dashboard')
    else:
        form = TeacherProfileForm()
    return render(request, 'attendance/teacher_profile.html', {'form': form})

@login_required
def face_registration(request):
    profile = request.user.profile
    # Restrict students without a Student profile
    if profile.is_student:
        try:
            Student.objects.get(profile=profile)
        except Student.DoesNotExist:
            messages.error(request, 'You must complete your student profile before registering your face.')
            return redirect('student-profile')
    if request.method == 'POST':
        form = FaceImageForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()
                # Process face encoding
                if profile.face_image:
                    image = face_recognition.load_image_file(profile.face_image.path)
                    face_encodings = face_recognition.face_encodings(image)
                    if face_encodings:
                        profile.face_encoding = face_encodings[0].tobytes()
                        profile.save()
                        messages.success(request, 'Face registered successfully!')
                        return redirect('dashboard')
                    else:
                        messages.error(request, 'No face detected in the image. Please try again.')
                else:
                    messages.error(request, 'No image file was uploaded. Please try again.')
            except Exception as e:
                messages.error(request, f'Error processing image: {str(e)}')
    else:
        form = FaceImageForm(instance=profile)
    return render(request, 'attendance/face_registration.html', {'form': form})

@login_required
def mark_attendance(request):
    if not request.user.profile.is_teacher:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Initialize webcam
        video_capture = cv2.VideoCapture(0)
        
        # Load known face encodings (only students)
        known_face_encodings = []
        known_face_names = []
        for profile in Profile.objects.filter(face_encoding__isnull=False, is_student=True):
            known_face_encodings.append(np.frombuffer(profile.face_encoding, dtype=np.float64))
            known_face_names.append(profile.user.username)
        
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
                
            # Find all faces in the frame
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]
                    
                    # Mark attendance for the recognized student if department matches
                    try:
                        student = Student.objects.get(profile__user__username=name)
                        teacher = Teacher.objects.get(profile=request.user.profile)
                        if student.department == teacher.department:
                            attendance, created = Attendance.objects.get_or_create(
                                student=student,
                                date=datetime.now().date(),
                                marked_by=teacher,
                                defaults={
                                    'time': datetime.now().time(),
                                    'status': True,
                                    'marked_by': teacher
                                }
                            )
                            if not created and not attendance.status:
                                attendance.status = True
                                attendance.save()
                    except (Student.DoesNotExist, Teacher.DoesNotExist):
                        pass
                
                # Draw rectangle around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Video', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        video_capture.release()
        cv2.destroyAllWindows()
        return redirect('dashboard')
    
    return render(request, 'attendance/mark_attendance.html')

class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    
    def get_queryset(self):
        if self.request.user.profile.is_student:
            return Attendance.objects.filter(student__profile=self.request.user.profile)
        elif self.request.user.profile.is_teacher:
            return Attendance.objects.filter(marked_by__profile=self.request.user.profile)
        return Attendance.objects.none()

@login_required
def dashboard(request):
    if request.user.profile.is_teacher:
        # For teachers, show all recent attendances
        recent_attendances = Attendance.objects.all().order_by('-date', '-time')[:10]
        return render(request, 'attendance/teacher_dashboard.html', {'recent_attendances': recent_attendances})
    elif request.user.profile.is_student:
        try:
            # Get student object
            student = Student.objects.get(profile=request.user.profile)
            
            # Get recent attendances
            recent_attendances = Attendance.objects.filter(
                student__profile=request.user.profile
            ).order_by('-date', '-time')[:10]
            
            # Calculate attendance statistics
            total_attendance = Attendance.objects.filter(student=student).count()
            total_present = Attendance.objects.filter(student=student, status=True).count()
            total_absent = total_attendance - total_present
            attendance_percentage = (total_present / total_attendance * 100) if total_attendance > 0 else 0
            
            context = {
                'student': student,
                'recent_attendances': recent_attendances,
                'total_attendance': total_attendance,
                'total_present': total_present,
                'total_absent': total_absent,
                'attendance_percentage': attendance_percentage,
            }
            
            return render(request, 'attendance/student_dashboard.html', context)
        except Student.DoesNotExist:
            messages.warning(request, 'Please complete your student profile first.')
            return redirect('student-profile')
    return redirect('login')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.get_user()
        role = self.request.POST.get('role')
        if role == 'student' and not user.profile.is_student:
            messages.error(self.request, 'You selected Student, but this account is not a student account.')
            return self.form_invalid(form)
        if role == 'teacher' and not user.profile.is_teacher:
            messages.error(self.request, 'You selected Teacher, but this account is not a teacher account.')
            return self.form_invalid(form)
        return super().form_valid(form)

@login_required
def view_profile(request):
    if request.user.profile.is_teacher:
        teacher = Teacher.objects.get(profile=request.user.profile)
        return render(request, 'attendance/view_teacher_profile.html', {'teacher': teacher})
    elif request.user.profile.is_student:
        student = Student.objects.get(profile=request.user.profile)
        return render(request, 'attendance/view_student_profile.html', {'student': student})
    return redirect('dashboard')

@login_required
def attendance_summary(request):
    if not request.user.profile.is_teacher:
        return redirect('dashboard')
    
    # Get attendance summary for all students
    students = Student.objects.all()
    summary = []
    
    for student in students:
        total_attendance = Attendance.objects.filter(student=student).count()
        present_count = Attendance.objects.filter(student=student, status=True).count()
        attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
        
        summary.append({
            'student': student,
            'total_attendance': total_attendance,
            'present_count': present_count,
            'attendance_percentage': attendance_percentage
        })
    
    return render(request, 'attendance/attendance_summary.html', {'summary': summary})

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'registration/password_reset_form.html')
        try:
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                messages.error(request, f'No account found with email: {email}')
                return render(request, 'registration/password_reset_form.html')
            try:
                profile = user.profile
                if not (profile.is_student or profile.is_teacher):
                    messages.error(request, 'This account is not properly set up. Please contact support.')
                    return render(request, 'registration/password_reset_form.html')
                otp = generate_otp()
                PasswordResetOTP.objects.filter(user=user, is_used=False).delete()
                otp_obj = PasswordResetOTP.objects.create(user=user, otp=otp)
                try:
                    send_mail(
                        'Password Reset OTP - Face Recognition Attendance',
                        f'Your OTP for password reset is: {otp}\n\nThis OTP is valid for 10 minutes.',
                        settings.EMAIL_HOST_USER,
                        [email],
                        fail_silently=False,
                    )
                    request.session['reset_email'] = email
                    request.session['otp_sent'] = True
                    messages.success(request, 'An OTP has been sent to your email.')
                    return redirect('verify_otp')
                except Exception as e:
                    messages.error(request, f'Failed to send OTP email: {str(e)}')
                    return render(request, 'registration/password_reset_form.html')
            except Profile.DoesNotExist:
                messages.error(request, f'No profile found for user {user.username}')
                return render(request, 'registration/password_reset_form.html')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'registration/password_reset_form.html')
    return render(request, 'registration/password_reset_form.html')

def verify_otp(request):
    reset_email = request.session.get('reset_email')
    otp_sent = request.session.get('otp_sent', False)
    
    if not reset_email or not otp_sent:
        messages.error(request, 'Please request a password reset first.')
        return redirect('password_reset')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        
        # Verify the email matches the one in session
        if email != reset_email:
            messages.error(request, 'Invalid email address.')
            return redirect('password_reset')
            
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, 'No user found for this email.')
                return redirect('verify_otp')
            try:
                otp_obj = PasswordResetOTP.objects.filter(
                    user=user,
                    otp=otp,
                    is_used=False
                ).latest('created_at')
            except PasswordResetOTP.DoesNotExist:
                messages.error(request, 'Invalid or expired OTP. Please request a new one.')
                return redirect('verify_otp')

            if otp_obj.is_valid():
                # Set new password
                user.set_password(new_password)
                user.save()
                # Mark OTP as used
                otp_obj.is_used = True
                otp_obj.save()
                # Clear session
                del request.session['reset_email']
                del request.session['otp_sent']
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('login')
            else:
                messages.error(request, 'Invalid or expired OTP. Please request a new one.')
                return redirect('verify_otp')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
            return redirect('verify_otp')
    
    return render(request, 'registration/verify_otp.html', {'email': reset_email})
