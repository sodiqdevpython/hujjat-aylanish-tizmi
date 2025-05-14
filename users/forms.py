from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import User, Department, AddRequirement, SubWorkPlan, MainWorkPlan, Document
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


class ApproveForm(forms.Form):
    ACTIONS = [("approve", "Tasdiqlash"), ("reject", "Rad etish")]
    action  = forms.ChoiceField(choices=ACTIONS, widget=forms.RadioSelect)
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows":3}))


# ────────────────────────────────────────────────
# 1.  HUJJAT YARATISH  (o‘qituvchi)
# ────────────────────────────────────────────────
class DocumentCreateForm(forms.ModelForm):
    """
    O‘qituvchi hujjat yuklash formasi.
    requirement  —  o‘sha o‘qituvchiga tegishli AddRequirement lar.
    """
    quantity_actual = forms.DecimalField(
        label="Amalda bajarilgan miqdor",
        min_value=0.1, max_value=5, decimal_places=1,
        widget=forms.NumberInput(attrs={"step": "0.1"})
    )
    class Meta:
        model  = Document
        fields = [
            "title",
            "short_description",
            "document_type",
            "file",
            "image",
            "requirement",
            "quantity_actual"
        ]
        widgets = {
            "short_description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")           # request.user majburiy
        super().__init__(*args, **kwargs)
        initial = self.initial.get("quantity_actual", 0)
        self.initial["quantity_actual"] = float(initial) - 1.0
        print(self.initial["quantity_actual"], "Shu yerda")
        # Faqat shu o‘qituvchining rejalari
        self.fields["requirement"].queryset = (
            AddRequirement.objects
            .filter(teacher=user)
            .select_related("main_plan", "sub_plan")
            .order_by("main_plan__name", "sub_plan__name")
        )
        self.fields["requirement"].required = False
        self.fields["requirement"].label    = "Reja bandi (ixtiyoriy)"

        # Barcha maydonlarga Bootstrap form-control klassi
        for f in self.fields.values():
            default_cls = "form-control-file" if isinstance(f.widget, forms.FileInput) else "form-control"
            f.widget.attrs.setdefault("class", default_cls)


# ────────────────────────────────────────────────
# 2.  HUJJAT TAHRIRLASH  (pending holatda)
# ────────────────────────────────────────────────
class DocumentUpdateForm(DocumentCreateForm):
    """
    Pending hujjatni o‘zgartirish formasi.
    Kerak bo‘lsa title readonly qilinadi.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Misol: title ni o‘zgartirib bo‘lmasin desak:
        # self.fields["title"].disabled = True


# ────────────────────────────────────────────────
# 3.  TASDIQLASH / RAD ETISH  (kafedra mudiri)
# ────────────────────────────────────────────────
class ApproveForm(forms.Form):
    ACTION_CHOICES = (
        ("approve", "Tasdiqlash"),
        ("reject",  "Rad etish"),
    )

    action  = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect,
        label="Amal"
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label="Izoh (rad etish sababi)"
    )

    def clean(self):
        cd = super().clean()
        if cd.get("action") == "reject" and not cd.get("comment"):
            self.add_error("comment", "Rad etish sababini kiriting.")
        return cd