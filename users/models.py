from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from utils.models import BaseModel
from . import choices

nb = dict(null=True, blank=True)

# Fakultet
class Faculty(BaseModel):
    title = models.CharField(max_length=256, unique=True)

    def __str__(self):
        return self.title

# Kafedra
class Department(BaseModel):
    title = models.CharField(max_length=256, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

# Foydalanuvchi rollari
class User(AbstractUser):
    first_name = models.CharField("Ism", max_length=100)
    last_name = models.CharField("Familiya", max_length=100)
    phone_number = models.CharField("Telefon raqam", max_length=20)
    image = models.ImageField("Rasm", upload_to="user_images/", **nb)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Kafedra", **nb)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, **nb)
    role = models.CharField("Roli", max_length=20, choices=choices.Role.choices, default=choices.Role.OQITUVCHI)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Ilmiy ish turi
class DocumentType(BaseModel):
    title = models.CharField(max_length=256, unique=True)

    def __str__(self):
        return self.title

# Ilmiy ish (hujjat)
class Document(BaseModel):
    title = models.CharField(max_length=1024)
    status = models.CharField(
        max_length=20,
        choices=choices.DocumentStatus.choices,
        default=choices.DocumentStatus.PENDING
    )
    url = models.URLField(**nb)
    short_description = models.TextField(**nb)
    file = models.FileField(upload_to="document/")
    image = models.ImageField(upload_to="document_image/", **nb)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    upload_user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

# Ish rejasining asosiy guruhi (Scopus, Konferensiya va h.k.)
class MainWorkPlan(BaseModel):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

# Har bir rejaning pastki toifasi (Respublika konferensiyasi, Darslik, Dasturiy guvohnoma)
class SubWorkPlan(BaseModel):
    name = models.CharField(max_length=64, unique=True)
    parent = models.ForeignKey(MainWorkPlan, on_delete=models.CASCADE, null=True, blank=True, related_name='subwork')

    def __str__(self):
        return self.name

# Reja biriktirish (kafedra mudiri -> o'qituvchi)
class AddRequirement(BaseModel):
    author = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='requirements_authored')
    teacher = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='requirements_received')
    sub_plan = models.ForeignKey(SubWorkPlan, on_delete=models.CASCADE, **nb)
    main_plan = models.ForeignKey(MainWorkPlan, on_delete=models.CASCADE, null=True)
    quantity_planned = models.DecimalField("Reja (miqdor)", max_digits=3, decimal_places=1,
        validators=[
            MaxValueValidator(5, message="5 tadan ortiq bo'lishi mumkin emas"),
            MinValueValidator(0.3, message="0.3 dan past bo'lishi mumkin emas")
        ]
    )

    def __str__(self):
        return f"{self.teacher} - {self.sub_plan} - {self.quantity_planned}"

# Amalda bajarilgan ishlar (tasdiqlangan hujjat asosida)
class PlanResponse(BaseModel):
    requirement = models.ForeignKey(AddRequirement, on_delete=models.CASCADE, related_name='responses')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, limit_choices_to={'is_confirmed': True})
    quantity_actual = models.DecimalField("Amalda (miqdor)", max_digits=3, decimal_places=1, default=1)

    def __str__(self):
        return f"{self.document} => {self.quantity_actual}"

# Hujjatni tasdiqlash jarayoni (SendRequest orqali)
class SendRequest(BaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    requirement = models.ForeignKey(AddRequirement, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=choices.DocumentStatus.choices,
        default=choices.DocumentStatus.PENDING
    )
    rejected_message = models.TextField(**nb)
    who_rejected = models.ForeignKey(User, on_delete=models.CASCADE, **nb)

    def __str__(self):
        return f"{self.document} - {self.status}"
