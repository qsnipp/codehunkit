"""
Core models
@author: Faraz Masood Khan faraz@fanaticlab.com
@copyright: Copyright (c) 2013 FanaticLab
"""

import random
import hashlib

from django.db import models
from django.db.models import F, Q 
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse

from codehunkit.app import HunkitError


class Language(models.Model):
    """
    Programming language
    """    
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(unique=True)
    website = models.URLField(blank=True, null=True)
    icon_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.DateTimeField(max_length=100)
    
    class Meta:
        app_label = 'app'
    
    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        """
        Returns permanent link of lang
        """
        return ('app_lang', (self.slug,))
    
    @classmethod
    def get_all(cls):
        """
        Returns list of all languages
        """
        return list(cls.objects.order_by('name'))
    
    @classmethod
    def get_defaults(cls):
        """
        Returns list of default languages
        """
        return list(cls.objects.filter(is_default=True).order_by('name'))
    

class LanguageGraph(models.Model):
    """
    Language graph of activites. Separate graph allows faster loading while updates runs on this table
    """
    language = models.OneToOneField(Language, primary_key=True, related_name='graph')
    up_votes = models.IntegerField(default=0)
    down_votes = models.IntegerField(default=0)
    subscriptions_count = models.IntegerField(default=0)
    coders_count = models.IntegerField(default=0)
    snippets_count = models.IntegerField(default=0)
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'app'
        db_table = 'app_language_graph'
    
    def __unicode__(self):
        return unicode(self.language)


class Location(models.Model):
    """
    Location
    """
    name = models.CharField(max_length=100, unique=True)
    language = models.CharField(max_length=50, blank=True, null=True)    
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.DateTimeField(max_length=100)
    
    class Meta:
        app_label = 'app'
    
    def __unicode__(self):
        return self.name


class School(models.Model):
    """
    School of users
    """
    name = models.CharField(max_length=500, unique=True)
    slug = models.SlugField(unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.DateTimeField(max_length=100)
    
    class Meta:
        app_label = 'app'
    
    def __unicode__(self):
        return self.name


class SchoolGraph(models.Model):
    """
    School graph of user activaties, Separate graph allows faster loading while updates runs on this table
    """
    school = models.OneToOneField(School, primary_key=True, related_name='graph')
    up_votes = models.IntegerField(default=0)
    down_votes = models.IntegerField(default=0)
    coders_count = models.IntegerField(default=0)
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'app'
        db_table = 'app_school_graph'
    

class User(AbstractUser):
    """
    Extended user more basic information
    """
    MALE = 'M'
    FEMALE = 'F'
    GENDERS = ((MALE, 'Male'),
               (FEMALE, 'Female'))
    
    birthday = models.DateField(null=True, blank=True)    
    gender = models.CharField(max_length=1, choices=GENDERS)
    hometown = models.ForeignKey(Location, null=True, related_name='hometown_users', blank=True)
    location = models.ForeignKey(Location, null=True, blank=True)
    locale = models.CharField(max_length=10, blank=True, null=True)
    website = models.URLField(null=True, blank=True)
    has_activated = models.BooleanField(default=False)    
    activation_code = models.CharField(max_length=512, blank=True, null=True)
    
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    
    REQUIRED_FIELDS = [ 'email', 'updated_by', 'created_by', 'has_activated']
    
    class Meta:
        app_label = 'app'
    
    def activate(self):
        """
        Activate user account if not activated
        """
        User.objects.filter(id=self.id, has_activated=False).update(has_activated=True, updated_by=str(self))
                
    def change_password(self, password, new_password):        
        """
        Change user's password
        """
        if not self.check_password(password):            
            raise HunkitError('Wrong password! please enter your current password again.')
        
        self.set_password(new_password)
    
        
    @classmethod 
    def sign_up(cls, username, email, password, gender, hometown=None, location=None, locale=None, is_verified=False):
        """
        Creates a new non-admin user in database 
        """            
        try:
            user = cls.objects.get(Q(username=username) | Q(email=email))
            if user.username == username:
                raise HunkitError('Username "%s" already registered with us, if you forgotten your password? <a href="%s">Request new one</a> or choose a different username.' % (username, reverse('app_forgot_password')))
            
            raise HunkitError('Its seems to be that you are already registered with this email address, if you forgotten your password? <a href="%s">Request new one.</a>' % reverse('app_forgot_password'))            
        except cls.DoesNotExist:
                        
            activation_code = None
            if not is_verified:            
                algo = hashlib.md5()
                algo.update(str(random.randrange(100, 10000000)))
                activation_code = algo.hexdigest()
            
            if hometown: 
                hometown = Location.objects.get_or_create(name=hometown)
            
            if location:
                location = Location.objects.get_or_create(name=location)
                
            user = cls.objects.create_user(username=username,
                                           email=email,
                                           password=password,
                                           gender= gender,
                                           hometown=hometown,
                                           location=location,
                                           locale=locale,
                                           has_activated=is_verified,
                                           activation_code=activation_code,
                                           updated_by=email,
                                           created_by=email)
            
            UserGraph.objects.create(user=user, created_by=email)
            
            # Create subscriptions to default languages
            langs = []
            for lang in Language.objects.filter(is_default=True):
                langs.append(lang.id)
                Subscription.objects.create(user=user,language=lang, created_by=email)
            
            if langs:
                LanguageGraph.objects.filter(language_id__in=langs).updated(subscriptions_count=F('subscriptions_count') + 1)
                
            return user
    

class UserGraph(models.Model):
    """
    User graph of his activities
    """
    user = models.OneToOneField(User, primary_key=True, related_name='graph')    
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    up_votes = models.IntegerField(default=0) # Up votes received on user's snippets
    down_votes = models.IntegerField(default=0) # Down votes received on user's snippets
    snippets_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    followers_count = models.IntegerField(default=0)
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    
    class Meta:        
        app_label = 'app'
        db_table = 'app_user_graph'
    
    def __unicode__(self):
        return unicode(self.user)


class Education(models.Model):
    """
    User education
    """
    user = models.OneToOneField(User, primary_key=True)
    school = models.ForeignKey(School)
    degree = models.CharField(max_length=250, null=True)
    year = models.IntegerField(null=True)
    type = models.CharField(max_length=100)
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.DateTimeField(max_length=100)
    
    class Meta:
        app_label = 'app'


class Subscription(models.Model):
    """
    User subscription for languages
    """
    user = models.ForeignKey(User)
    language = models.ForeignKey(Language)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'app'
        unique_together = ('user', 'language')
        
        
class FacebookUser(models.Model):
    """
    Facebook user information
    """
    id = models.BigIntegerField(primary_key=True)
    user = models.OneToOneField(User, unique=True)
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=50)
    email = models.EmailField()
    access_token = models.CharField(max_length=2048,blank=True,null=True) # Sizes can grow and shrink therefore 2K should be enough
    access_expiry = models.DateTimeField(blank=True,null=True)
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=75)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=75)
    
    class Meta:
        app_label = 'app'
    
    def __unicode__(self):
        return self.username
    