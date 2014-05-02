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
    return create_setup_view_context(
        request,
        SetupForm,
        reverse('twitter2:home'))
