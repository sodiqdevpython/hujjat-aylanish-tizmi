from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import (
    Faculty, Department, User, DocumentType, Document,
    MainWorkPlan, SubWorkPlan, AddRequirement, PlanResponse, SendRequest
)

# Fakultet
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']


# Kafedra
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'faculty']
    list_filter = ['faculty']
    search_fields = ['title']


# Custom User admin (login o‘zgarmas, faqat parol yangilanishi mumkin)
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    model = User
    add_form = UserCreationForm
    form = UserChangeForm
    list_display = ['username', 'first_name', 'last_name', 'role', 'department']
    list_filter = ['role', 'department__faculty']
    search_fields = ['username', 'first_name', 'last_name', 'phone_number']

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'image', 'department', 'role')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'image', 'department', 'role')}),
    )



# Hujjat turi
@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']


# Hujjatlar (Document)
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'upload_user', 'document_type', 'status', 'is_confirmed']
    list_filter = ['document_type', 'status', 'is_confirmed']
    search_fields = ['title', 'upload_user__first_name', 'upload_user__last_name']


# Asosiy ish rejasi
@admin.register(MainWorkPlan)
class MainWorkPlanAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


# Sub ish rejasi
@admin.register(SubWorkPlan)
class SubWorkPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']
    list_filter = ['parent']
    search_fields = ['name']


# Reja belgilash (AddRequirement)
@admin.register(AddRequirement)
class AddRequirementAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'sub_plan','main_plan', 'quantity_planned', 'author']
    list_filter = ['sub_plan', 'teacher__department']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'author__first_name']
    autocomplete_fields = ['author', 'teacher', 'sub_plan']


# Amalda bajarilgan ish (PlanResponse)
@admin.register(PlanResponse)
class PlanResponseAdmin(admin.ModelAdmin):
    list_display = ['requirement', 'document', 'quantity_actual']
    list_filter = ['requirement__teacher__department', 'document__document_type']
    search_fields = ['document__title', 'requirement__teacher__first_name']


# Tasdiqlashlar (SendRequest)
@admin.register(SendRequest)
class SendRequestAdmin(admin.ModelAdmin):
    list_display = ['document', 'requirement', 'status', 'who_rejected']
    list_filter = ['status']
    search_fields = ['document__title', 'who_rejected__first_name']
    autocomplete_fields = ['document', 'requirement', 'who_rejected']
