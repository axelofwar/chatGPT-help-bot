from django.shortcuts import render
from rest_framework import generics
from .models import *
from .serializers import *

# Create your views here.


class TweetList(generics.ListCreateAPIView):
    queryset = Tweet.objects.all().order_by('index')
    serializer_class = TweetSerializer


class TweetDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tweet.objects.all()
    serializer_class = TweetSerializer
