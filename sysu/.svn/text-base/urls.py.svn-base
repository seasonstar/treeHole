from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('sysu.secret.views',
    # (r'^mysite/', include('mysite.foo.urls')),
    url(r'^$', 'index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^log/$', 'log', name='weibo_log'),
    url(r'^logincheck', 'log_check', name='weibo_check'),
    url(r'^logout/$', 'logout', name='weibo_logout'),
    url(r'^follow/(\d+)/$', 'follow', name='follow'),
    url(r'^weibo/$', 'get_hole_timeline', name='timeline'),
    url(r'^weibo/(\d+)/$', 'get_comment', name='comments'),
    url(r'^reply/(\d+)/$', 'comment', name='reply'),
    url(r'^weibo/update', 'cron_test'),    
    url(r'^to_say8', 'suggest'),
)
