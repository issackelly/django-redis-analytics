Django Analytics with Redis
===========================

Requires
--------

* redis running on your server
* redis-py
* django-staticfiles
    
    # settings.py
    # REDIS
    REDIS_CONNECTION = {
        "host": "localhost",
        "port": 6379,
        "databases": {
            "analytics": 0,
        }
    }
    
Setup
------

* Add analytics.middleware.AnalyticsMiddleware
* add analytics to INSTALLED_APPS
* syncdb