from django import forms
from .models import UsageLog, Prop

class PropForm(forms.ModelForm):
    class Meta:
        model = Prop
        fields = '__all__'



class UsageLogForm(forms.ModelForm):
    class Meta:
        model = UsageLog
        fields = ['prop', 'event_name', 'date_of_use', 'quantity_used', 'return_status']
        widgets = {
            'date_of_use': forms.DateInput(attrs={'type': 'date'}),
        }
