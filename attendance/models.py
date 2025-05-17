from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    face_encoding = models.BinaryField(null=True, blank=True)
    face_image = models.ImageField(upload_to='face_images/', null=True, blank=True)

    def __str__(self):
        return self.user.username

class Student(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    semester = models.IntegerField()

    def __str__(self):
        return f"{self.profile.user.username} - {self.roll_number}"

class Teacher(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.profile.user.username} - {self.designation}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.BooleanField(default=False)  # True for present, False for absent
    marked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('student', 'date', 'marked_by')

    def __str__(self):
        return f"{self.student} - {self.date} - {'Present' if self.status else 'Absent'}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # OTP is valid for 10 minutes
        return not self.is_used and self.created_at + timedelta(minutes=10) > timezone.now()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Profile)
def create_teacher_for_profile(sender, instance, created, **kwargs):
    if instance.is_teacher:
        # Only create if not already exists
        from .models import Teacher
        if not hasattr(instance, 'teacher'):
            Teacher.objects.create(profile=instance, department='', designation='')
