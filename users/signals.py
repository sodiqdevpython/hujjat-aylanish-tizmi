from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AddRequirement, PlanResponse, WorkPlanSummary, Document, Notification
from .choices import Role
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

@receiver(post_save, sender=Document)
def create_pending_notification(sender, instance, created, **kw):
    if created:
        teacher = instance.upload_user
        mudir   = teacher.department.user_set.filter(role=Role.MUDIR).first()
        if mudir:
            Notification.objects.create(
                recipient=mudir,
                title="Yangi hujjat tasdiqlash uchun",
                message=f"{teacher.get_full_name()} hujjat yukladi: «{instance.title}»",
                url=reverse("doc_approve_detail", args=[instance.id])
            )
