from django.contrib import admin
from .models import Profile, Student, Teacher, Attendance, PasswordResetOTP
from django.contrib.auth.models import User

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_student', 'is_teacher')
    list_filter = ('is_student', 'is_teacher')
    search_fields = ('user__username', 'user__email')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'roll_number', 'department', 'semester')
    list_filter = ('department', 'semester')
    search_fields = ('profile__user__username', 'roll_number')

    def get_name(self, obj):
        return obj.profile.user.get_full_name() or obj.profile.user.username
    get_name.short_description = 'Name'

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'department', 'designation')
    list_filter = ('department',)
    search_fields = ('profile__user__username', 'designation')

    def get_name(self, obj):
        return obj.profile.user.get_full_name() or obj.profile.user.username
    get_name.short_description = 'Name'

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'time', 'status', 'marked_by')
    list_filter = ('date', 'status')
    search_fields = ('student__profile__user__username', 'marked_by__profile__user__username')
    date_hierarchy = 'date'

@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('otp', 'created_at')
