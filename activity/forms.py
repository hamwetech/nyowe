from django import forms
from activity.models import ThematicArea, TrainingSession, ExternalTrainer
from conf.utils import bootstrapify
from coop.models import CooperativeMember


class ThematicAreaForm(forms.ModelForm):
    class Meta:
        model = ThematicArea
        fields = ['thematic_area', 'description']
        

class TrainingForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        exclude = ['create_date', 'update_date', 'created_by' , 'training_reference']
    
    def __init__(self, *args, **kwargs):
        super(TrainingForm, self).__init__(*args, **kwargs)
        self.fields['coop_member'].widget.attrs['id'] = 'selec_adv_1'
        self.fields['coop_member'].queryset = CooperativeMember.objects.none()

        if 'cooperative' in self.data:
            try:
                cooperative_id = int(self.data.get('cooperative'))
                self.fields['member'].queryset = CooperativeMember.objects.filter(cooperative=cooperative_id).order_by(
                    'first_name')
            except Exception as e:  # (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            if self.instance.cooperative:
                self.fields['member'].queryset = self.instance.cooperative.member_set.order_by('first_name')

        

class ExternaTrainerForm(forms.ModelForm):
    class Meta:
        model = ExternalTrainer
        exclude = ['create_date', 'update_date']
    
        
bootstrapify(ExternaTrainerForm)
bootstrapify(ThematicAreaForm)
bootstrapify(TrainingForm)