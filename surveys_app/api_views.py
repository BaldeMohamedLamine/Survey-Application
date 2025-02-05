from rest_framework import viewsets
from .models import Response, Survey
from .serializers import ResponseSerializer, SurveySerializer

class ResponseViewSet(viewsets.ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer

class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all().order_by('')
    serializer_class = SurveySerializer