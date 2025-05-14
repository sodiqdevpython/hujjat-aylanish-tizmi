"""
Signal’lar – reja/statistika sinxroni, hujjat tasdiqlash/reject va
bildirishnomalar.  Import faqat apps.py → ready() ichida!
"""
from decimal import Decimal
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum
from django.urls import reverse

from .models import (
    AddRequirement, PlanResponse, WorkPlanSummary,
    Document, Notification, choices
)

# ============================================================
#  YORDAMCHI:  WorkPlanSummary ni qayta hisoblash
# ============================================================
def _refresh_summary(teacher, sub):
    mp = sub.parent
    planned = AddRequirement.objects.filter(
        teacher=teacher, sub_plan=sub
    ).aggregate(s=Sum("quantity_planned"))["s"] or Decimal("0")

    actual  = PlanResponse.objects.filter(
        requirement__teacher=teacher, requirement__sub_plan=sub
    ).aggregate(s=Sum("quantity_actual"))["s"] or Decimal("0")
    print(actual)
    print(planned)

    obj, _ = WorkPlanSummary.objects.get_or_create(
        teacher=teacher, main_plan=mp, sub_plan=sub
    )
    obj.total_planned = planned
    obj.total_actual  = actual
    obj.save()

# ============================================================
#  1)  Requirement o‘zgarganda                               |
# ============================================================
@receiver([post_save, post_delete],
          sender=AddRequirement,
          dispatch_uid="addreq_sync")
def sync_requirement(sender, instance, **kw):
    if instance.sub_plan:
        _refresh_summary(instance.teacher, instance.sub_plan)

# ============================================================
#  2)  PlanResponse o‘zgarganda                               |
# ============================================================
@receiver([post_save, post_delete],
          sender=PlanResponse,
          dispatch_uid="planresp_sync")
def sync_response(sender, instance, **kw):
    req = instance.requirement
    if req and req.sub_plan:
        _refresh_summary(req.teacher, req.sub_plan)

# ============================================================
#  3)  Hujjat yaratilganda  →  mudirga xabar                  |
# ============================================================
@receiver(post_save, sender=Document,
          dispatch_uid="doc_create_notif")
def create_pending_notification(sender, instance, created, **kw):
    if created:
        teacher = instance.upload_user
        mudir   = teacher.department.user_set.filter(
                    role=choices.Role.MUDIR
                  ).first()
        if mudir:
            Notification.objects.create(
                recipient=mudir,
                title="Tasdiqlash uchun yangi hujjat",
                message=f"{teacher.get_full_name()} «{instance.title}» yukladi",
                url=reverse("doc_approve_detail", args=[instance.id])
            )

# ============================================================
#  4)  Old status ni eslab qolish (pre_save)                  |
# ============================================================
@receiver(pre_save, sender=Document,
          dispatch_uid="doc_remember_old_status")
def remember_old_status(sender, instance, **kw):
    instance._old_status = (
        sender.objects.filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
        if instance.pk else None
    )

# ============================================================
#  5)  Tasdiqlash / Rad etish                                 |
# ============================================================
@receiver(post_save, sender=Document,
          dispatch_uid="doc_status_handler")
def handle_document_status(sender, instance, **kw):
    old, new = getattr(instance, "_old_status", None), instance.status
    if old == new:      # status o‘zgarmagan
        return

    # ---------- TASDIQLANGAN --------------------------------
    if new == choices.DocumentStatus.APPROVED:
        instance.is_confirmed = True
        instance.save(update_fields=["is_confirmed"])

        # Talab bog‘langan bo‘lsa – PlanResponse
        if instance.requirement:
            PlanResponse.objects.get_or_create(
                requirement=instance.requirement,
                document=instance,
                defaults={"quantity_actual": instance.quantity_actual} #0.3 -0.7
            )

        Notification.objects.create(
            recipient=instance.upload_user,
            title="Hujjat tasdiqlandi",
            message=f"«{instance.title}» tasdiqlandi.",
            url=reverse("ilmiy_ish_detail", args=[instance.id])
        )

    # ---------- RAD ETILGAN ---------------------------------
    elif new == choices.DocumentStatus.REJECTED:
        instance.is_confirmed = False
        instance.save(update_fields=["is_confirmed"])

        Notification.objects.create(
            recipient=instance.upload_user,
            title="Hujjat rad etildi",
            message="Hujjatingiz rad etildi, iltimos tuzatib qayta yuboring.",
            url=reverse("ilmiy_ish_detail", args=[instance.id])
        )
