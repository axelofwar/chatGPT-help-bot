from django.urls import path
from db_api.views import TweetList, TweetDetail

app_name = 'db_api'

urlpatterns = [
    path('Tweet/', TweetList.as_view(), name='Tweet_list'),
    path('Tweet/<int:pk>/', TweetDetail.as_view(), name='Tweet_detail'),
]
