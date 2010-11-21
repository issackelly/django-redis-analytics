"""
Analytics Middleware
"""

from datetime import date, datetime
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
import hashlib
import redis

class AnalyticsMiddleware(object):
    
    def __init__(self, *args, **kwargs):
        try:
            self.c = settings.REDIS_CONNECTION
        except:
            raise ImproperlyConfigured("You need a REDIS_CONNECTION in your settings")
        self.r = redis.Redis(host=self.c["host"], port=self.c["port"], db=self.c["databases"]["analytics"])
    
    def process_response(self, request, response):
        today = datetime.now()
        
        if response.status_code == 200 and \
        (not request.path.startswith(reverse('admin:index'))):
            # Integer representation of the current date
            # Feels like a clever way to use the sorted set field
            # to create a group of keys for a specific event
            score = int(today.strftime("%Y%m%d"))

            key = "response:%s:by.date:%s" % (
                request.path,
                score
            )
            self.r.incr(key)
            self.r.zadd("response:path:by.date:keys", key, score)

            key = "response:by.date:%s" % (
                score
            )
            self.r.incr(key)
            self.r.zadd("response:by.date:keys", key, score)

            if request.META.get("HTTP_REFERER") and request.META["HTTP_REFERER"]:
                key = "referred.by:%s:%s:" % (
                    request.path,
                    score,
                )
                key += hashlib.sha1(request.path+request.META["HTTP_REFERER"]).hexdigest()
                self.r.sadd(key+":site", request.META["HTTP_REFERER"])
                self.r.incr(key+":count")
                self.r.zadd("referred.by:by.date:keys", key, score)

            if request.user and request.user.is_authenticated():
                score = int(today.strftime("%Y%m%d"))                
                key = "response:%s:user:%s:by.date:%s" % (
                    request.path,
                    request.user.pk,
                    score
                )
                self.r.incr(key)
                self.r.zadd("response:path:user:%s:by.date:keys" % request.user.pk, key, score)
                
        return response