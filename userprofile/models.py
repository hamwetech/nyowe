# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.dispatch import receiver
from datetime import datetime, date
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token
from conf.models import District


class AccessLevel(models.Model):
    name = models.CharField(max_length=15, unique=True)
    create_date = models.DateTimeField(auto_now=True)
    update_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'access_level'
    
    def __unicode__(self):
        return self.name
    

class AccessLevelGroup(models.Model):
    access_level = models.OneToOneField(AccessLevel, unique=True)
    group = models.ManyToManyField(Group)
    
    class Meta:
        db_table = 'access_levell_group'
    
    def __unicode__(self):
        return "%s" % self.access_level


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    sex = models.CharField('Sex', max_length=10, choices=(('Male', 'Male'), ('Female', 'Female')), null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    msisdn = models.CharField(max_length=12, unique=True, null=True, blank=True)
    date_recruited = models.DateField(null=True)
    nin = models.CharField(max_length=255,  null=True, blank=True)
    access_level = models.ForeignKey(AccessLevel, null=True, blank=True, on_delete=models.CASCADE)
    district = models.ManyToManyField(District, blank=True)
    supervisor = models.ForeignKey(User, null=True, blank=True, related_name="supervisor")
    is_locked = models.BooleanField(default=0)
    receive_sms_notifications = models.BooleanField(default=0)
    create_date = models.DateTimeField(auto_now=True)
    update_date = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = 'user_profile'

    @property
    def age(self):
        if self.date_of_birth:
            m = date.today() - self.date_of_birth
            return m.days / 365
        return None
        
    def is_union(self):
        if self.access_level:
            if self.access_level.name.upper() == "UNION" or self.access_level.name.upper() == "AGENT":
                return True
        if self.user.is_superuser:
            return True
        return False
    
    def is_cooperative(self):
        if self.access_level:
            if self.access_level.name.upper() == "COOPERATIVE":
                return True
        if self.user.is_superuser:
            return True
        return False
    
    def is_partner(self):
        if self.access_level:
            if self.access_level.name.upper() == "PARTNER":
                return True
        if self.user.is_superuser:
            return True
        return False
    
    def is_union_admin(self):
        if self.access_level.name.upper() == "UNION" or self.user.is_superuser:
            return True
        return False

    def __str__(self):
        return self.user.get_full_name()
        

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Token.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()                           
                                    
