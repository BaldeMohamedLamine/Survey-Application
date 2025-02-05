from __future__ import annotations

import csv

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now
from django.views import View
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from .forms import ChoiceFormSet
from .forms import QuestionForm
from .forms import SurveyForm
from .models import Answer
from .models import Choice
from .models import Question
from .models import Response
from .models import Survey



class HomeView(ListView):
    model = Survey
    template_name = "surveys_app/index.html"
    context_object_name = 'surveys'
    paginate_by = 10

    def get_queryset(self):
        today = now()
        return Survey.objects.filter(
            is_published=True, 
            start_date__lte=today, 
            end_date__gte=today
        ).order_by('end_date')

        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(creator__username__icontains=search_query)
            )

        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())
        elif status == 'upcoming':
            queryset = queryset.filter(start_date__gt=timezone.now())
        elif status == 'ended':
            queryset = queryset.filter(end_date__lt=timezone.now())

        creator = self.request.GET.get('creator')
        if creator:
            queryset = queryset.filter(creator__username=creator)

        sort_by = self.request.GET.get('sort')
        if sort_by == 'recent':
            queryset = queryset.order_by('-start_date')
        elif sort_by == 'popular':
            queryset = queryset.annotate(response_count=Count('response')).order_by('-response_count')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        context['current_creator'] = self.request.GET.get('creator', '')

        context['creators'] = get_user_model().objects.filter(
            role='creator',
            survey__is_published=True
        ).distinct()

        return context


class SurveyListView(LoginRequiredMixin, ListView):
    model = Survey
    template_name = 'surveys_app/survey_list.html'
    context_object_name = 'surveys'
    paginate_by = 6

    def get_queryset(self):
        queryset = Survey.objects.filter(creator=self.request.user)
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_published=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_published=False)
        return queryset.order_by('end_date')


class SurveyStep1View(LoginRequiredMixin, CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys_app/survey_step1.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_creator():
            return HttpResponseForbidden("Seuls les créateurs peuvent créer des sondages.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.is_published = False 
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('surveys_app:survey-step2', kwargs={'uid': self.object.uid})
    
    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class SurveyStep2View(LoginRequiredMixin, TemplateView):
    template_name = "surveys_app/survey_step2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = get_object_or_404(Survey, uid=kwargs['uid'], creator=self.request.user)
        context['survey'] = survey
        context['questions'] = Question.objects.filter(survey=survey).prefetch_related('choices')
        context['question_form'] = QuestionForm()  
        context['choice_formset'] = ChoiceFormSet(queryset=Choice.objects.none()) 
        return context

    def post(self, request, *args, **kwargs):
        survey = get_object_or_404(Survey, uid=kwargs['uid'], creator=request.user)
        question_form = QuestionForm(request.POST)
        choice_formset = ChoiceFormSet(request.POST)

        if 'add_question' in request.POST:
            if question_form.is_valid():
                question = question_form.save(commit=False)
                question.survey = survey
                question.save()
                if question.type in ['single', 'multiple']:
                    if choice_formset.is_valid():
                        choice_formset.instance = question
                        choice_formset.save()
                messages.success(request, "Question ajoutée avec succès.")
            else:
                messages.error(request, "Erreur dans le formulaire de la question.")
        elif 'save_survey' in request.POST:
            messages.success(request, "Sondage enregistré avec succès.")
            return redirect('surveys_app:survey-list')

        return redirect('surveys_app:survey-step2', uid=survey.uid)


class SurveyUpdateView(LoginRequiredMixin, UpdateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys_app/survey_update.html'
    context_object_name = 'survey'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.creator != self.request.user:
            raise PermissionDenied("Vous n'avez pas la permission de modifier ce sondage.")
        return obj
    
    def get_queryset(self):
        return Survey.objects.all()

    def get_success_url(self):
        return reverse_lazy('surveys_app:survey-step2', kwargs={'uid': self.object.uid})

    def form_valid(self, form):
        if 'save' in self.request.POST:
            messages.success(self.request, "Les modifications ont été enregistrées avec succès.")
            return super().form_valid(form)
        return redirect('surveys_app:survey-step2', uid=self.object.uid)



class SurveyDeleteView(LoginRequiredMixin, DeleteView):
    model = Survey
    template_name = 'surveys_app/survey_confirm_delete.html'
    success_url = reverse_lazy('surveys_app:survey-list')

    def dispatch(self, request, *args, **kwargs):
        survey = self.get_object()
        if survey.is_published:
            return HttpResponseForbidden("Vous ne pouvez pas supprimer un sondage publié.")
        return super().dispatch(request, *args, **kwargs)


class PublishSurveyView(LoginRequiredMixin, View):
    def get(self, request, uid):
        survey = get_object_or_404(Survey, uid=uid, creator=request.user)
        return render(request, 'surveys_app/publish_confirm.html', {'survey': survey})

    def post(self, request, uid):
        survey = get_object_or_404(Survey, uid=uid, creator=request.user)
        if survey.end_date and survey.end_date < timezone.now():
            messages.error(request, "Impossible de publier le sondage : la date de fin est déjà passée.")
            return redirect("surveys_app:survey-list")
        survey.is_published = True
        survey.save()
        messages.success(request, "Le sondage a été publié avec succès.")
        return redirect("surveys_app:survey-list")


class SurveyResultsView(LoginRequiredMixin, View):
    template_name = "surveys_app/survey_results.html"

    def get(self, request, pk):
        survey = get_object_or_404(Survey, uid=pk)

        if not survey.can_view_results(request.user):
            return HttpResponseForbidden("Vous n'avez pas la permission de voir les résultats.")

        questions = Question.objects.filter(survey=survey).prefetch_related('choices')

        results = []
        for question in questions:
            question_data = {
                'text': question.text,
                'type': question.type,
                'total_responses': Answer.objects.filter(question=question).count(),
                'responses': []
            }

            if question.type in ['single', 'multiple']:
                total_answers = Answer.objects.filter(question=question).count()
                choices = Choice.objects.filter(question=question)

                for choice in choices:
                    count = Answer.objects.filter(question=question, choice=choice).count()
                    percentage = (count / total_answers * 100) if total_answers > 0 else 0

                    question_data['responses'].append({
                        'choice': choice.text,
                        'count': count,
                        'percentage': round(percentage, 1)
                    })

                question_data['chart_data'] = {
                    'labels': [resp['choice'] for resp in question_data['responses']],
                    'values': [resp['count'] for resp in question_data['responses']]
                }

            else:
                text_answers = Answer.objects.filter(
                    question=question
                ).exclude(text__isnull=True).exclude(text__exact='')

                question_data['responses'] = [{
                    'text': answer.text,
                    'user': answer.response.user.username,
                    'date': answer.response.created_at.strftime('%d/%m/%Y %H:%M')
                } for answer in text_answers]

            results.append(question_data)

        context = {
            'survey': survey,
            'results': results,
            'total_participants': Response.objects.filter(survey=survey).count()
        }
        return render(request, self.template_name, context)


class SurveyResponseView(LoginRequiredMixin, View):
    template_name = 'surveys_app/survey_response.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Vérifie les conditions préalables avant d'autoriser l'accès à la vue
        """
        self.survey = get_object_or_404(Survey, uid=kwargs['uid'])
        if not self.survey.can_participate(request.user):
            messages.error(request, self.get_error_message(request.user))
            return redirect("surveys_app:home")

        return super().dispatch(request, *args, **kwargs)

    def get_error_message(self, user):
        """
        Retourne le message d'erreur approprié selon le statut de participation
        """
        status = self.survey.get_participation_status(user)
        messages = {
            "login_required": "Vous devez être connecté pour participer à ce sondage.",
            "not_published": "Ce sondage n'est pas disponible actuellement.",
            "not_started": "Ce sondage n'a pas encore commencé.",
            "ended": "Ce sondage est terminé.",
            "already_responded": "Vous avez déjà répondu à ce sondage."
        }
        return messages.get(status, "Vous ne pouvez pas participer à ce sondage.")

    def get(self, request, uid):
        """
        Affiche le formulaire du sondage
        """
        questions = self.survey.questions.all().prefetch_related('choices').order_by('uid')
        context = {
            'survey': self.survey,
            'questions': questions,
            'today': timezone.now()
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, uid):
        """
        Traite la soumission des réponses au sondage
        """
        try:
            if Response.objects.filter(survey=self.survey, user=request.user).exists():
                messages.error(request, "Vous avez déjà répondu à ce sondage.")
                return redirect("surveys_app:home")

            response = Response.objects.create(
                user=request.user,
                survey=self.survey
            )

            questions = self.survey.questions.all().prefetch_related('choices')
            for question in questions:
                field_name = f"question_{question.uid}"

                if question.type == 'text':
                    answer_text = request.POST.get(field_name, '').strip()
                    if answer_text:
                        Answer.objects.create(
                            response=response,
                            question=question,
                            text=answer_text
                        )

                elif question.type == 'single':
                    choice_uid = request.POST.get(field_name)
                    if choice_uid:
                        try:
                            choice = question.choices.get(uid=choice_uid)
                            Answer.objects.create(
                                response=response,
                                question=question,
                                choice=choice
                            )
                        except Choice.DoesNotExist:
                            messages.warning(
                                request,
                                f"Une réponse invalide a été détectée pour la question : {question.text}"
                            )

                elif question.type == 'multiple':
                    choice_uids = request.POST.getlist(field_name)
                    valid_choices = question.choices.filter(uid__in=choice_uids)

                    for choice in valid_choices:
                        Answer.objects.create(
                            response=response,
                            question=question,
                            choice=choice
                        )

            messages.success(
                request,
                "Vos réponses ont été enregistrées avec succès. Merci de votre participation!"
            )
            return redirect('surveys_app:thank_you', uid=self.survey.uid)

        except Exception as e:
            if 'response' in locals():
                response.delete()

            messages.error(
                request,
                "Une erreur est survenue lors de l'enregistrement de vos réponses. "
                "Veuillez réessayer."
            )
            return redirect('surveys_app:survey-response', uid=self.survey.uid)

    def get_context_data(self, **kwargs):
        """
        Ajoute des données supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        context['questions'] = self.survey.questions.all().prefetch_related('choices')
        context['today'] = timezone.now()
        return context


def thank_you(request, uid):
    survey = get_object_or_404(Survey, uid=uid)
    return render(request, 'surveys_app/thank_you.html', {'survey': survey})


class DuplicateSurveyView(LoginRequiredMixin, View):
    def get(self, request, pk):
        original_survey = get_object_or_404(Survey, uid=pk, creator=request.user)
        new_survey = Survey.objects.create(
            title=f"{original_survey.title} (Copie)",
            description=original_survey.description,
            start_date=original_survey.start_date,
            end_date=original_survey.end_date,
            creator=request.user,
            is_published=False
        )

        for question in original_survey.questions.all():
            new_question = Question.objects.create(
                text=question.text,
                type=question.type,
                survey=new_survey
            )
            for choice in question.choices.all():
                Choice.objects.create(
                    text=choice.text,
                    question=new_question
                )

        messages.success(request, "Le sondage a été dupliqué avec succès.")
        return redirect('surveys_app:survey-list')


class ExportSurveyResultsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        survey = get_object_or_404(Survey, uid=pk, creator=request.user)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{survey.title}_results.csv"'

        writer = csv.writer(response)
        writer.writerow(['Question', 'Réponse', 'Utilisateur', 'Date'])
        answers = Answer.objects.filter(response__survey=survey)
        for answer in answers:
            writer.writerow([
                answer.question.text,
                answer.choice.text if answer.choice else answer.text,
                answer.response.user.username,
                answer.response.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
