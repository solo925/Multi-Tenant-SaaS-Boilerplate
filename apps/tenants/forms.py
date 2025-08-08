from django import forms
from .models import Client, Domain


class CreateTenantForm(forms.Form):
    name = forms.CharField(max_length=100, label="Tenant Name")
    schema_name = forms.SlugField(max_length=63, label="Schema Name")
    domain = forms.CharField(max_length=253, label="Primary Domain")
    on_trial = forms.BooleanField(label="Start on trial", required=False, initial=True)

    def clean_schema_name(self):
        schema = self.cleaned_data['schema_name']
        # Basic guard: public schema is reserved
        if schema.lower() == 'public':
            raise forms.ValidationError("'public' is a reserved schema name.")
        if Client.objects.filter(schema_name=schema).exists():
            raise forms.ValidationError("Schema name already in use.")
        return schema

    def clean_domain(self):
        domain = self.cleaned_data['domain'].strip().lower()
        if Domain.objects.filter(domain=domain).exists():
            raise forms.ValidationError("Domain already exists.")
        return domain


class EditTenantForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'name',
            'on_trial',
        ]


class AddDomainForm(forms.Form):
    domain = forms.CharField(max_length=253, label="Domain")
    is_primary = forms.BooleanField(required=False, initial=False, label="Set as primary")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_domain(self):
        value = self.cleaned_data['domain'].strip().lower()
        if Domain.objects.filter(domain=value).exists():
            raise forms.ValidationError("Domain already exists.")
        return value


