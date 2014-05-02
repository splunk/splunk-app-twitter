from django.conf.urls import patterns, include, url
from splunkdj.utility.views import render_template as render

urlpatterns = patterns('',
    # NOTE: The framework always expects the default view to be called 'home'.
    #       And it expects the default view to be a framework view.
    #       In this case the default view is actually a non-framework view,
    #       so an explicit redirect needs to be inserted to make the
    #       framework happy.
    url(r'^home/$', 'twitter2.views.home', name='home'),
    url(r'^setup/$', 'twitter2.views.setup', name='setup'),
)
