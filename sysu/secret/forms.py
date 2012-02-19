from django import forms
import sae.storage

class UploadForm(forms.Form):
    pic = forms.ImageField()

def handle_uploaded_file(f):
    s = sae.storage.Client()
    ob = sae.storage.Object(f.read())
    filename = 'pic/' + f.name.decode('utf-8')
    s.put('sysusecret', filename, ob)
    return filename
