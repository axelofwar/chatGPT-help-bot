from django.db import models

# Create your models here.


class Tweet(models.Model):
    index = models.CharField(
        max_length=255, primary_key=True, default='defaultUser')
    Name = models.CharField(max_length=255)
    Favorites = models.IntegerField()
    Retweets = models.IntegerField()
    Replies = models.IntegerField()
    Impressions = models.IntegerField()

    class Meta:
        # managed = False
        db_table = 'pfp_table'
        verbose_name_plural = 'pfp_table'

    def __str__(self):
        print(f"{self.Name} has {self.Favorites} favorites, {self.Retweets} retweets, {self.Replies} replies, and {self.Impressions} impressions")
        return f"{self.Name} has {self.Favorites} favorites, {self.Retweets} retweets, {self.Replies} replies, and {self.Impressions} impressions"
