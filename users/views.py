from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.http import HttpResponseForbidden
from . import forms
from .choices import Role, DocumentStatus
from .models import User, Faculty, Department, Document, DocumentType, AddRequirement, SubWorkPlan, MainWorkPlan, PlanResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Count
from datetime import datetime
from calendar import month_name
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.db.models import Sum

@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role == Role.OQITUVCHI:
        return redirect('teacher_dashboard')
    return render(request, 'index.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = forms.LoginForm(request.POST or None)
    error_message = None

    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                error_message = "Foydalanuvchi nomi yoki parol noto‘g‘ri"

    return render(request, 'login.html', {
        'form': form,
        'error_message': error_message
    })


class TeacherListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "read/teacher_list.html"           # ↓ 2-qismda shu nomdagi fayl
    context_object_name = "page_obj"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            User.objects.select_related("department__faculty")
            .filter(role__in=[Role.OQITUVCHI, Role.MUDIR, Role.PROREKTOR,
                              Role.DEKAN, Role.SUPERADMIN])        # xohlagan rollarni qoldiring
        )

        # Foydalanuvchi turi (role) bo‘yicha filtr
        role = self.request.GET.get("user_type")
        if role:
            qs = qs.filter(role=role)

        # Fakultet bo‘yicha filtr
        fac_id = self.request.GET.get("faculty_id")
        if fac_id:
            qs = qs.filter(department__faculty_id=fac_id)

        # Kafedra bo‘yicha filtr
        dep_id = self.request.GET.get("department_id")
        if dep_id:
            qs = qs.filter(department_id=dep_id)

        return qs.order_by("last_name", "first_name")

    # Sahifaga qo‘shimcha kontekst uzatamiz
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "user_types": Role.choices,
            "faculties": Faculty.objects.all(),
            "departments": Department.objects.all(),
            "selected_user_type": self.request.GET.get("user_type", ""),
            "selected_faculty_id": self.request.GET.get("faculty_id", ""),
            "selected_dept_id": self.request.GET.get("department_id", ""),
        })
        return ctx
    
@login_required
def create_teacher(request):
    if request.user.role != Role.MUDIR or not request.user.department:
        return HttpResponseForbidden("Faqat kafedra mudiri va kafedrasi mavjud foydalanuvchi qo‘shishi mumkin.")

    if request.method == 'POST':
        form = forms.TeacherCreateForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_user = form.save(commit=False)

            # Majburan kafedrani o‘zlashtiramiz
            new_user.department = request.user.department
            new_user.save()
            return redirect('teacher_list')
    else:
        form = forms.TeacherCreateForm(user=request.user)

    return render(request, 'create/teacher_create.html', {'form': form})

@login_required
def user_profile_detail(request, pk):
    user_profile = get_object_or_404(User, pk=pk)

    # Yuklangan hujjatlar
    documents_qs = (
        Document.objects
        .filter(upload_user=user_profile)
        .select_related("document_type")
    )

    # Hujjat turi bo‘yicha filtr
    doc_type_id = request.GET.get("doc_type")
    if doc_type_id:
        documents_qs = documents_qs.filter(document_type_id=doc_type_id)

    document_types = DocumentType.objects.all()

    # Oxirgi 6 oylik sana ro‘yxati (tuple -> (yil, oy))
    today = datetime.today()
    last_6_months = [(today.year if today.month - i > 0 else today.year - 1,
                      (today.month - i - 1) % 12 + 1) for i in range(6)]

    # Faollik statistikasi (created → NOT created_at)
    faollik_raw = (
        documents_qs
        .filter(created__year__in=[y for y, m in last_6_months],
                created__month__in=[m for y, m in last_6_months])
        .values("created__year", "created__month")
        .annotate(count=Count("id"))
    )

    # Chart uchun etiketkalar va sonlar
    month_labels = [f"{month_name[m]} {y}" for y, m in reversed(last_6_months)]
    month_counts = []
    for y, m in reversed(last_6_months):
        count = next((item["count"] for item in faollik_raw
                      if item["created__year"] == y and item["created__month"] == m), 0)
        month_counts.append(count)

    # Ruxsat: kafedra mudiri va shu kafedradan bo‘lsa
    has_permission_for_update_or_adding_work = (
        request.user.role == Role.MUDIR and
        request.user.department == user_profile.department
    )

    context = {
        "user_profile": user_profile,
        "documents": documents_qs,
        "document_types": document_types,
        "selected_type": doc_type_id,
        "faollik_months": month_labels,
        "faollik_counts": month_counts,
        "has_permission_for_update_or_adding_work": has_permission_for_update_or_adding_work
    }

    return render(request, 'read/user_profile_detail.html', context)

@login_required
def teacher_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = forms.TeacherUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Foydalanuvchi ma'lumotlari yangilandi.")
            return redirect('user_profile_detail', pk=user.pk)
    else:
        form = forms.TeacherUpdateForm(instance=user)

    return render(request, 'update/teacher_update.html', {'form': form})

@login_required
def ilmiy_ishlar_list(request):
    query = request.GET.get("q", "")
    doc_type = request.GET.get("doc_type", "")
    faculty_id = request.GET.get("faculty", "")
    department_id = request.GET.get("department", "")

    # Barcha ilmiy ishlar
    documents = Document.objects.select_related(
        'upload_user', 'document_type', 'upload_user__department__faculty'
    )

    # Qidiruv
    if query:
        documents = documents.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(upload_user__first_name__icontains=query) |
            Q(upload_user__last_name__icontains=query)
        )

    # Hujjat turi bo‘yicha filtr
    if doc_type:
        documents = documents.filter(document_type_id=doc_type)

    # Fakultet bo‘yicha filtr
    if faculty_id:
        documents = documents.filter(
            upload_user__department__faculty_id=faculty_id
        )

    # Kafedra bo‘yicha filtr
    if department_id:
        documents = documents.filter(
            upload_user__department_id=department_id
        )

    # Paginatsiya (9 kartochka / sahifa)
    paginator = Paginator(documents.order_by("-created"), 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,
        "doc_types": DocumentType.objects.all(),
        "selected_doc_type": doc_type,
        "faculties": Faculty.objects.all(),
        "departments": Department.objects.all(),
        "selected_faculty": faculty_id,
        "selected_department": department_id,
    }
    return render(request, "read/ilmiy_ishlar_list.html", context)


@login_required
def ilmiy_ish_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)

    # upload_user yuklagan boshqa 4 ta ish
    related_documents = (
        Document.objects
        .filter(upload_user=document.upload_user)
        .exclude(id=document.id)
        .order_by('-created')[:4]
    )

    return render(request, "read/document_detail.html", {
        "document": document,
        "related_documents": related_documents,
        "document_status_choices": DocumentStatus.choices,
    })


@require_POST
@login_required
def update_document_status(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.user.role != Role.MUDIR or request.user.department != doc.upload_user.department:
        return redirect('ilmiy_ish_detail', pk=pk)

    new_status = request.POST.get("status")
    if new_status in dict(DocumentStatus.choices):
        doc.status = new_status
        doc.is_confirmed = (new_status == DocumentStatus.APPROVED)
        doc.save()

    return redirect('ilmiy_ish_detail', pk=pk)



@login_required
def add_requirement(request, teacher_id):
    teacher = get_object_or_404(User, pk=teacher_id)
    # faqat o‘sha teacher kafedrasi mudiri qo‘shishi mumkin
    if request.user.role != Role.MUDIR or request.user.department != teacher.department:
        return HttpResponseForbidden("Siz bu foydalanuvchiga ish reja qo‘sha olmaysiz.")

    if request.method == 'POST':
        form = forms.AddRequirementForm(request.POST, teacher=teacher)
        if form.is_valid():
            form.save()
            return redirect('user_profile_detail', pk=teacher.pk)
    else:
        form = forms.AddRequirementForm(teacher=teacher)

    return render(request, 'create/add_requirement.html', {
        'form': form,
        'teacher': teacher
    })


@login_required
def work_plan_report(request):
    if request.user.role != Role.MUDIR:
        return HttpResponseForbidden()

    # Filtr parametrlar
    fac_id = request.GET.get("faculty", "")
    dept_id = request.GET.get("department", "")

    faculties = Faculty.objects.all()
    departments = Department.objects.filter(faculty_id=fac_id) if fac_id else Department.objects.none()

    teachers = User.objects.filter(role=Role.OQITUVCHI)
    if fac_id:
        teachers = teachers.filter(department__faculty_id=fac_id)
    if dept_id:
        teachers = teachers.filter(department_id=dept_id)
    teachers = teachers.order_by('last_name', 'first_name')

    main_plans = MainWorkPlan.objects.prefetch_related('subwork').all()

    # Reja yozuvlari (faqat parenti bor subplanlar)
    reqs = (
        AddRequirement.objects
        .filter(teacher__in=teachers, sub_plan__parent__isnull=False)
        .values('teacher_id', 'sub_plan_id', 'sub_plan__parent_id')
        .annotate(total_planned=Sum('quantity_planned'))
    )

    # Amalda bajarilganlar
    responses = (
        PlanResponse.objects
        .filter(requirement__teacher__in=teachers,
                requirement__sub_plan__parent__isnull=False)
        .values('requirement__teacher_id',
                'requirement__sub_plan_id',
                'requirement__sub_plan__parent_id')
        .annotate(total_actual=Sum('quantity_actual'))
    )

    # stats = {teacher->{main->{sub:{planned,actual}}}}
    stats = {
        t.id: {
            mp.id: {sp.id: {'planned': 0, 'actual': 0} for sp in mp.subwork.all()}
            for mp in main_plans
        }
        for t in teachers
    }

    # To‘ldirish: reja
    for r in reqs:
        tid = r.get('teacher_id')
        mid = r.get('sub_plan__parent_id')
        sid = r.get('sub_plan_id')
        if tid is None or mid is None or sid is None:
            continue
        # agar bunday kalitlar mavjud bo‘lsa, qiymat beramiz
        if tid in stats and mid in stats[tid] and sid in stats[tid][mid]:
            stats[tid][mid][sid]['planned'] = r['total_planned']

    # Amalda bajarilgan
    for r in responses:
        tid = r.get('requirement__teacher_id')
        mid = r.get('requirement__sub_plan__parent_id')
        sid = r.get('requirement__sub_plan_id')
        if tid is None or mid is None or sid is None:
            continue
        if tid in stats and mid in stats[tid] and sid in stats[tid][mid]:
            stats[tid][mid][sid]['actual'] = r['total_actual']

    # Footer hisobi
    footer = {}
    for mp in main_plans:
        footer[mp.id] = {}
        for sp in mp.subwork.all():
            p = sum(stats[t.id][mp.id][sp.id]['planned'] for t in teachers)
            a = sum(stats[t.id][mp.id][sp.id]['actual']  for t in teachers)
            footer[mp.id][sp.id] = {'planned': p, 'actual': a}

    return render(request, 'read/work_plan_report.html', {
        'teachers': teachers,
        'main_plans': main_plans,
        'stats': stats,
        'footer': footer,
        'faculties': faculties,
        'departments': departments,
        'selected_faculty': fac_id,
        'selected_department': dept_id,
    })

