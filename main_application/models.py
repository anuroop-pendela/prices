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


class RestCallStatus(models.Model):
    """
    Model to stores api call details of bitmex
    """
    id = models.AutoField(primary_key=True)
    log_date = models.DateTimeField()
    path =  models.CharField(max_length=100)
    query = models.CharField(max_length= 100)
    verb = models.CharField(max_length = 100)
    response_code = models.FloatField(default = 0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    class Meta:
        db_table = 'rest_call_status'
        verbose_name_plural = "Rest Call Status"



class ApiCallLog(models.Model):
    """
    Model to records api call made by each exchanges.
    """
    id = models.AutoField(primary_key=True)
    log_date = models.DateTimeField()
    exchange_name = models.CharField(max_length = 100, null=True)
    end_point =  models.CharField(max_length=100,null=True)
    parameters = models.CharField(max_length= 500, null=True)
    response_code = models.FloatField(default = 0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    exchange_order_id = models.CharField(max_length = 100 , null = True)
    order_id =  models.CharField(max_length=100, null=True)
    routine_id =  models.CharField(max_length = 100, null = True)
    strategy_id =  models.CharField(max_length = 100, null=  True)
    response =  models.TextField(null=True)
    class Meta:
        db_table = 'api_call_log'
        verbose_name_plural = "Api call log"