from datetime import datetime, timedelta, time
from django.conf import settings
from django.http import HttpResponse
from django.contrib import admin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf.urls.defaults import *
from analytics.models import Track
import json
import operator
import redis

class TrackAdmin(admin.ModelAdmin):
    def analytics(self, request, user=None):
        c = settings.REDIS_CONNECTION
        r = redis.Redis(host=c["host"], port=c["port"], db=c["databases"]["analytics"])
        
        today = datetime.now()
        last_month = datetime.now() - timedelta(days=30)
        frm = int(last_month.strftime("%Y%m%d"))
        to = int(today.strftime("%Y%m%d"))
        
        if user:
            user = get_object_or_404(User, pk=user)
            keys = r.zrangebyscore("response:path:user:%s:by.date:keys" %
                request.user.pk, frm, to)
            refer_keys = None
        else:
            keys = r.zrangebyscore("response:path:by.date:keys", frm, to)
            refer_keys = r.zrangebyscore("referred.by:by.date:keys", frm,to)
        if not keys:
            return HttpResponse("Nothing for Range")
        dates = dict()
        points = list()
        paths = dict()
        
        values = r.mget(keys)
        i = 0
        for key in keys:
            pieces = key.split(":")
            if pieces[1] in [paths]:
                paths[pieces[1]] += int(values[i])
            else:
                paths[pieces[1]] = int(values[i])
            if pieces[-1] in dates:
                dates[pieces[-1]]["count"] += int(values[i])
            else:
                dates[pieces[-1]] = dict()
                dates[pieces[-1]]["count"] = int(values[i])
                dates[pieces[-1]]["date"] = datetime(year=int(pieces[-1][:4]),
                    month=int(pieces[-1][4:6]), day=int(pieces[-1][-2:]))
            i += 1
        for d in dates:
            points.append([(int(dates[d]["date"].strftime("%s"))*1000), dates[d]["count"]])
        
        sorted_paths = sorted(paths.iteritems(), key=operator.itemgetter(1), reverse=True)
        paths = sorted_paths
        
        if refer_keys:
            refer_paths = {}
            refer_dates = {}
            refer_sites = {}
            refer_points = []
            i = 0
            site_keys = [key + ":site" for key in refer_keys]
            count_keys = [key + ":count" for key in refer_keys]
            sites = r.mget(site_keys)
            print sites
            counts = r.mget(count_keys)
            for key in refer_keys:
                pieces = key.split(":")
                if pieces[1] in [refer_paths]:
                    refer_paths[pieces[1]] += int(counts[i])
                else:
                    refer_paths[pieces[1]] = int(counts[i])
                if pieces[2] in refer_dates:
                    refer_dates[pieces[2]]["count"] += int(counts[i])
                else:
                    refer_dates[pieces[2]] = dict()
                    refer_dates[pieces[2]]["count"] = int(counts[i])
                    refer_dates[pieces[2]]["date"] = datetime(year=int(pieces[2][:4]),
                        month=int(pieces[2][4:6]), day=int(pieces[2][-2:]))
                if pieces[3] in refer_sites:
                    refer_sites[pieces[3]]["count"] += int(counts[i])
                else:
                    if sites[i]:
                        refer_sites[pieces[3]] = {}
                        refer_sites[pieces[3]]["count"] = int(counts[i])
                        refer_sites[pieces[3]]["site"] = sites[i]
                i += 1
            for d in refer_dates:
                refer_points.append([(int(refer_dates[d]["date"].strftime("%s"))*1000), refer_dates[d]["count"]])
        else:
            refer_paths = {}
            refer_dates = {}
            refer_sites = {}
            refer_points = []
        
        return render_to_response("analytics/admin/hashlist.html",{
            "other_user": user,
            "paths": paths,
            "user": request.user,
            "points": json.dumps(points),
            "refer_paths": refer_paths,
            "refer_dates": refer_dates,
            "refer_sites": refer_sites,
            "refer_points": json.dumps(refer_points),
        }, context_instance=RequestContext(request))

    def get_urls(self):
        urls = super(TrackAdmin, self).get_urls()
        extra = patterns('',
            url(r'^analytics/$', self.admin_site.admin_view(self.analytics)),
            url(r'^analytics/(?P<user>[\d+])/$', self.admin_site.admin_view(self.analytics)),
        )
        return extra + urls
admin.site.register(Track, TrackAdmin)