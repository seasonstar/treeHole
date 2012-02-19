# -*- coding:utf-8 -*-
from django.db import models
from django.contrib import admin


class Weibouser(models.Model):
    name = models.CharField("微博名", max_length=30)
    weiboid = models.CharField("微博ID", max_length=30)
    access_token_key = models.CharField(max_length=100)
    access_token_secret = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name
    
class Weibo(models.Model):
    user = models.ForeignKey(Weibouser)
    weibo = models.TextField("微博", max_length=140)
    added = models.DateTimeField("发布时间", auto_now_add=True)
    
    def __unicode__(self):
        return self.weibo[:20]

class Blacklist(models.Model):
    weiboid = models.CharField("黑名单ID", max_length=30)
    def __unicode__(self):
        return self.weiboid

class Suggest(models.Model):
    suggest = models.TextField("建议", max_length=500)

class WeibouserAdmin(admin.ModelAdmin):
    list_display = ('name', 'weiboid', 'access_token_key', 'access_token_secret')

class WeiboAdmin(admin.ModelAdmin):
    list_display = ('user', 'weibo', 'added')

admin.site.register(Blacklist)
admin.site.register(Suggest)
admin.site.register(Weibo, WeiboAdmin)
admin.site.register(Weibouser, WeibouserAdmin)
