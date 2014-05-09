# NOTE: Using django.forms directly instead of splunkdj.setup.forms
from django import forms
import os.path
import splunklib.client as client
import subprocess
import sys

_PYTHON_FILEPATH = sys.executable
_VERIFY_SCRIPT_FILEPATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'bin', 'verify_twitter_oauth_settings.py')

class SetupForm(forms.Form):
    api_key = forms.CharField(
        label="API Key",
        max_length=100)
    api_secret = forms.CharField(
        label="API Secret",
        max_length=100)
    access_token = forms.CharField(
        label="Access Token",
        max_length=100)
    access_token_secret = forms.CharField(
        label="Access Token Secret",
        max_length=100)
    enabled = forms.BooleanField(
        label="Enable Twitter Input",
        required=False)     # needed for BooleanFields to permit value of False
    
    @classmethod
    def load(cls, request):
        """Loads this form's persisted state, returning a new Form."""
        
        service = request.service
        
        # Locate the storage/passwords entity that contains the Twitter
        # credentials, if available.
        # 
        # It is only stored in storage/passwords because older versions of
        # this app put it there. If writing this app from scratch,
        # I'd probably put it in a conf file instead because it
        # is a lot easier to access.
        passwords_endpoint = client.Collection(service, 'storage/passwords')
        passwords = passwords_endpoint.list()
        first_password = passwords[0] if len(passwords) > 0 else None
        
        # Locate the scripted input that extracts events from Twitter.
        # 
        # If writing this app from scratch I would probably use a modular
        # input instead because they are easier to configure.
        twitter_input = SetupForm._get_twitter_scripted_input(service)
        
        settings = {}
        
        # Read credentials from the password entity.
        # NOTE: Reading from 'password' setting just gives a bunch of asterisks,
        #       so we need to read from the 'clear_password' setting instead.
        # NOTE: Reading from 'name' setting gives back a string in the form
        #       '<realm>:<username>', when we only want the username.
        #       So we need to read from the 'username' setting instead.
        settings['api_key'] = \
            first_password['realm'] if first_password else ''
        settings['api_secret'] = \
            first_password['clear_password'].split(':')[0] if first_password else ''
        settings['access_token'] = \
            first_password['username'] if first_password else ''
        settings['access_token_secret'] = \
            first_password['clear_password'].split(':')[1] if first_password else ''
        
        # Read state of the Twitter input
        settings['enabled'] = (twitter_input['disabled'] == '0')
        
        # Create a SetupForm with the settings
        return cls(settings)
    
    def clean(self):
        """Perform validations that require multiple fields."""
        
        cleaned_data = super(SetupForm, self).clean()
        
        # Verify that the credentials are valid by connecting to Twitter
        credentials = [
            cleaned_data.get('api_key', None),
            cleaned_data.get('api_secret', None),
            cleaned_data.get('access_token', None),
            cleaned_data.get('access_token_secret', None)
        ]
        if None in credentials:
            # One of the credential fields didn't pass validation,
            # so don't even try connecting to Twitter.
            pass
        else:
            if not SetupForm._validate_twitter_credentials(credentials):
                raise forms.ValidationError('Invalid Twitter credentials.')
        
        return cleaned_data
    
    def save(self, request):
        """Saves this form's persisted state."""
        
        service = request.service
        settings = self.cleaned_data
        
        first_password_settings = {
            'realm': settings['api_key'],
            'name': settings['access_token'],
            'password': \
                settings['api_secret'] + ':' + settings['access_token_secret']
        }
        
        # Replace old password entity with new one
        passwords_endpoint = client.Collection(service, 'storage/passwords')
        passwords = passwords_endpoint.list()
        if len(passwords) > 0:
            first_password = passwords[0]
            first_password.delete()
        first_password = passwords_endpoint.create(**first_password_settings)
        
        # Update state of the Twitter input
        twitter_input = SetupForm._get_twitter_scripted_input(service)
        twitter_input.update(**{
            'disabled': '0' if settings['enabled'] else '1'
        })
    
    @staticmethod
    def _get_twitter_scripted_input(service):
        # Locate the scripted input that extracts events from Twitter.
        # 
        # NOTE: Can't fetch the scripted input using an exact name because
        #       the name is the absolute path of the script, meaning that it
        #       varies based on the location where Splunk is installed.
        # NOTE: The pathname separator also varies based on the operating
        #       system of the Splunk server.
        inputs = service.inputs.list()
        for input in inputs:
            if input.name.endswith(os.path.join('twitter2', 'bin', 'stream_tweets.py')):
                return input
        raise ValueError('Could not locate the Twitter scripted input.')
    
    @staticmethod
    def _validate_twitter_credentials(credentials):
        # HACK: Shell out to a new Python subprocess because the
        #       verify script depends on a different version of the
        #       'requests' library than the Splunk Web Framework uses.
        #       (The subprocess will use its own version of 'requests'.)
        return_code = subprocess.call(
            [_PYTHON_FILEPATH, _VERIFY_SCRIPT_FILEPATH] +
            credentials)
        return (return_code == 0)
