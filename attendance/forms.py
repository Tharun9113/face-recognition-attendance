from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, Teacher, Profile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="Register as",
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def save(self, commit=True):
        user = super().save(commit=True)
        role = self.cleaned_data.get('role')
        profile = user.profile
        # Explicitly set both to False first
        profile.is_student = False
        profile.is_teacher = False
        if role == 'student':
            profile.is_student = True
        elif role == 'teacher':
            profile.is_teacher = True
        profile.save()
        return user

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['roll_number', 'department', 'semester']

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['department', 'designation']

class FaceImageForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['face_image'] 