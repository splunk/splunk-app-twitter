from .forms import SetupForm
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from splunkdj.decorators.render import render_to
from splunkdj.setup import create_setup_view_context

@login_required
def home(request):
    # Redirect to the default view, which happens to be a non-framework view
    return redirect('/en-us/app/twitter2/twitter_general')

@render_to('twitter2:setup.html')
@login_required
def setup(request):
    result = create_setup_view_context(
        request,
        SetupForm,
        reverse('twitter2:home'))
    
    # HACK: Workaround DVPL-4647 (Splunk 6.1 and below):
    #       Refresh current app's state so that non-framework views
    #       observe when the app becomes configured.
    service = request.service
    app_name = service.namespace['app']
    service.apps[app_name].post('_reload')
    
    return result
