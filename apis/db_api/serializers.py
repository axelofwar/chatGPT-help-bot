from rest_framework import serializers
from .models import *

'''
A serializer is a class that converts a model instance into a Python native data type 
that can then be easily rendered into JSON, XML or other content types.

This is the serializer for the Tweet model - contains functions for:
    - TweetSerializer = pfp_table

TODO:
    - Add more serializers for other tables
    - Add serializers for viewing a specific user's data(?)
    - Change serializer names from Tweet to PFP_Table and propagate changes
'''


class TweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tweet
        fields = '__all__'
