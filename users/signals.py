from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AddRequirement, PlanResponse, WorkPlanSummary
from django.db.models import Sum

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
