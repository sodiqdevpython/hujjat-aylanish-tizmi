from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import AddRequirement, PlanResponse, WorkPlanSummary, Document, Notification
from .choices import Role, DocumentStatus
from django.db.models import Sum
from django.urls import reverse


def _refresh_summary(teacher, sub):
    mp = sub.parent
    planned = AddRequirement.objects.filter(teacher=teacher, sub_plan=sub)\
                                    .aggregate(s=Sum('quantity_planned'))['s'] or 0
    actual  = PlanResponse.objects.filter(requirement__teacher=teacher,
                                          requirement__sub_plan=sub)\
                                   .aggregate(s=Sum('quantity_actual'))['s'] or 0
    obj, _ = WorkPlanSummary.objects.get_or_create(
        teacher=teacher, main_plan=mp, sub_plan=sub)
    obj.total_planned, obj.total_actual = planned, actual
    obj.save()

@receiver([post_save, post_delete], sender=AddRequirement)
def sync_requirement(sender, instance, **kw):
    if instance.sub_plan:
        _refresh_summary(instance.teacher, instance.sub_plan)

@receiver([post_save, post_delete], sender=PlanResponse)
def sync_response(sender, instance, **kw):
    req = instance.requirement
    if req.sub_plan:
        _refresh_summary(req.teacher, req.sub_plan)

# @receiver(post_save, sender=Document)
# def create_pending_notification(sender, instance, created, **kw):
#     if created:
#         teacher = instance.upload_user
#         mudir   = teacher.department.user_set.filter(role=Role.MUDIR).first()
#         if mudir:
#             Notification.objects.create(
#                 recipient=mudir,
#                 title="Yangi hujjat tasdiqlash uchun",
#                 message=f"{teacher.get_full_name()} hujjat yukladi: «{instance.title}»",
#                 url=reverse("doc_approve_detail", args=[instance.id])
#             )


@receiver(pre_save, sender=Document)
def remember_old_status(sender, instance, **kwargs):
    """save() dan oldin eski status ni eslab qolamiz"""
    if instance.pk:
        instance._old_status = (
            sender.objects.filter(pk=instance.pk)
            .values_list("status", flat=True)
            .first()
        )
    else:
        instance._old_status = None


# --- tasdiqlanganda PlanResponse + xabar ----------------------------
@receiver(post_save, sender=Document)
def handle_document_status(sender, instance, created, **kwargs):
    old = getattr(instance, "_old_status", None)
    new = instance.status

    # faqat status o‘zgarganda ishlaydi
    if old == new:
        return

    # == 1) Tasdiqlangan ------------------------------------------------
    if new == DocumentStatus.APPROVED:
        instance.is_confirmed = True        # shunchaki ishonch uchun
        instance.save(update_fields=["is_confirmed"])

        # Talab bog‘langan bo‘lsa → PlanResponse
        if instance.requirement:
            PlanResponse.objects.get_or_create(
                requirement=instance.requirement,
                document=instance,
                defaults={"quantity_actual": 1}
            )

        # O‘qituvchiga xabar
        Notification.objects.create(
            recipient=instance.upload_user,
            title="Hujjat tasdiqlandi",
            message=f"«{instance.title}» tasdiqlandi.",
            url=reverse("ilmiy_ish_detail", args=[instance.pk])
        )

    # == 2) Rad etilgan -------------------------------------------------
    elif new == DocumentStatus.REJECTED:
        instance.is_confirmed = False
        instance.save(update_fields=["is_confirmed"])

        Notification.objects.create(
            recipient=instance.upload_user,
            title="Hujjat rad etildi",
            message="Hujjatingiz mudir tomonidan rad etildi. Izohni ko‘rib, tuzatib qayta yuboring.",
            url=reverse("ilmiy_ish_detail", args=[instance.pk])
        )