from django import forms
from .models import Choice, Question, Survey

class SurveyForm(forms.ModelForm):
    """Form for creating and updating surveys."""
    class Meta:
        model = Survey
        fields = ["image", "title", "description", "start_date", "end_date"]
        labels = {
            "title": "Survey Title",
            "description": "Description",
            "start_date": "Start Date",
            "end_date": "End Date",
        }
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
        return cleaned_data


class QuestionForm(forms.ModelForm):
    """Form for creating and updating questions."""
    class Meta:
        model = Question
        fields = ["text", "type"]
        labels = {
            "text": "Question Text",
            "type": "Question Type",
        }

class ChoiceForm(forms.ModelForm):
    """Form for creating and updating choices."""
    class Meta:
        model = Choice
        fields = ["text"]
        labels = {
            "text": "Choice Text",
        }

    def clean_text(self):
        text = self.cleaned_data.get("text", "").strip()
        if not text:
            raise forms.ValidationError("Le texte du choix ne peut pas être vide.")
        return text


class BaseChoiceInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        for form in self.forms:
            if not form.cleaned_data.get("text", "").strip():
                raise forms.ValidationError("Tous les champs de choix doivent être remplis.")

        if self.instance.type in ["single", "multiple"] and len(self.forms) < 2:
            raise forms.ValidationError("Les questions à réponses multiples doivent avoir au moins deux choix.")


ChoiceFormSet = forms.inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    formset=BaseChoiceInlineFormSet,
    extra=2,
    can_delete=True,
)
