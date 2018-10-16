from django.db import models

# Create your models here.
#
class Prices(models.Model):
    """
    Model to store the prices from different exchanges
    """
    id = models.AutoField(primary_key=True)
    exchange_name = models.CharField(max_length=50, null=False)
    bid =  models.FloatField(default=0)
    ask =  models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    class Meta:
        db_table = 'prices'
        verbose_name_plural = "Prices"
