from django.urls import path
from db_api.views import TweetList, TweetDetail

app_name = 'db_api'

'''
This is the URL configuration for the db_api app - contains functions for:
    - TweetList = pfp_table
    - TweetDetail = pfp_table detail 

TODO:
    - Add more views for other tables
    - Add views for viewing a specific user's data(?)
    - Change api names from Tweet to PFP_Table and propagate changes
'''
urlpatterns = [
    path('Tweet/', TweetList.as_view(), name='Tweet_list'),
    path('Tweet/<int:pk>/', TweetDetail.as_view(), name='Tweet_detail'),
]
