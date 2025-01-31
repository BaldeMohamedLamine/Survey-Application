from __future__ import annotations

from rest_framework import serializers

from .models import Answer
from .models import Choice
from .models import Question
from .models import Response
from .models import Survey
from account.models import User

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['uid', 'text']

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['uid', 'text', 'type', 'choices']

class SurveySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Survey
        fields = ['uid', 'title', 'description', 'start_date', 'end_date', 'creator', 'is_published', 'questions']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['question', 'choice', 'text']

class ResponseSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Response
        fields = ['survey', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        response = Response.objects.create(user=self.context['request'].user, **validated_data)

        for answer_data in answers_data:
            Answer.objects.create(response=response, **answer_data)

        return response

    def validate(self, data):
        user = self.context['request'].user
        survey = data['survey']

        # Vérifier si l'utilisateur peut participer
        if not survey.can_participate(user):
            raise serializers.ValidationError("Vous ne pouvez pas participer à ce sondage.")

        return data
