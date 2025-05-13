from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import User, Department, AddRequirement, SubWorkPlan, MainWorkPlan
from users.choices import Role

class LoginForm(forms.Form):
    username = forms.CharField(
        label="ID raqam",
        max_length=9,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'login',
            'placeholder': 'ID raqam'
        })
    )
    password = forms.CharField(
        label="Parol",
        max_length=32,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password',
            'placeholder': 'Parol'
        })
    )


class TeacherCreateForm(UserCreationForm):
    # Ikkinchi parol maydoni kerak emas
    password2 = None

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name',
            'phone_number', 'image', 'department',
            'password1'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # view orqali keladigan request.user
        super().__init__(*args, **kwargs)

        self.fields['image'].required = True
        self.fields['phone_number'].required = True
        self.fields['department'].required = True
        self.instance.role = Role.OQITUVCHI  # Doim o'qituvchi rolida saqlanadi

        if user and user.role == Role.MUDIR:
            # Faqat o‘z kafedrasiga foydalanuvchi qo‘shadi
            self.fields['department'].initial = user.department
            self.fields['department'].queryset = Department.objects.filter(id=user.department.id)
            self.fields['department'].disabled = True
        else:
            self.fields['department'].queryset = Department.objects.none()

    def clean_department(self):
        # Disabled bo‘lgan maydon POST bilan kelmaydi, lekin initial dan olish mumkin
        return self.initial.get('department')

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    

class TeacherUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'phone_number',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].disabled = True
        self.fields['phone_number'].widget.attrs['maxlength'] = 9



class AddRequirementForm(forms.ModelForm):
    class Meta:
        model = AddRequirement
        fields = ['main_plan', 'sub_plan', 'quantity_planned']
        widgets = {
            'main_plan': forms.Select(attrs={'class': 'form-control', 'id': 'id_main_plan'}),
            'sub_plan': forms.Select(attrs={'class': 'form-control', 'id': 'id_sub_plan'}),
            'quantity_planned': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        self.fields['main_plan'].queryset = MainWorkPlan.objects.all()
        
        main_id = None
        if 'main_plan' in self.data:
            try:
                main_id = int(self.data.get('main_plan'))
            except (ValueError, TypeError):
                main_id = None
        elif self.instance.pk and self.instance.main_plan_id:
            main_id = self.instance.main_plan_id

        if main_id:
            # faqat shu main_plan ostidagi subworklarni ko‘rsatamiz
            self.fields['sub_plan'].queryset = SubWorkPlan.objects.filter(parent_id=main_id)
        else:
            # boshida bo‘sh yoki main_plan tanlanmaganda
            self.fields['sub_plan'].queryset = SubWorkPlan.objects.none()

    def clean(self):
        cleaned = super().clean()
        main = cleaned.get('main_plan')
        sub = cleaned.get('sub_plan')
        # agar main_plan uchun child sub_planlar bor va sub tanlanmasa
        if main and SubWorkPlan.objects.filter(parent=main).exists() and not sub:
            self.add_error('sub_plan', "Iltimos, qo‘shimcha reja turini tanlang.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.teacher = self.teacher
        # agar sub_plan tanlangan bo‘lsa, main_plan ga ham avtomatik o‘rnatamiz
        sub = self.cleaned_data.get('sub_plan')
        if sub:
            obj.main_plan = sub.parent
        if commit:
            obj.save()
        return obj
