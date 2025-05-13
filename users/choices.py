from django.db import models


class Role(models.TextChoices):
    SUPERADMIN = "superadmin", "Superadmin"
    PROREKTOR = "prorektor", "Prorektor"
    DEKAN = "dekan", "Dekan"
    MUDIR = "mudir", "Kafedra mudiri"
    OQITUVCHI = "oqituvchi", "O‘qituvchi"

class DocumentStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    APPROVED = "approved", "Tasdiqlangan"
    REJECTED = "rejected", "Rad etilgan"