from django import forms
from django.contrib.auth.models import User
from credit.models import CreditManager, LoanRequest
from conf.utils import bootstrapify, internationalize_number, PHONE_REGEX


class CreditManagerForm(forms.ModelForm):
    class Meta:
        model = CreditManager
        exclude = ['create_date', 'update_date']

class CreditManagerUserForm(forms.ModelForm):
    confirm_password = forms.CharField(max_length=150, required=True, widget=forms.PasswordInput)
    password = forms.CharField(max_length=150, required=True, widget=forms.PasswordInput)
    msisdn = forms.CharField(max_length=150)

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance", None)
        print(instance)
        super(CreditManagerUserForm, self).__init__(*args, **kwargs)
        if instance:
            self.fields.pop('password')
            self.fields.pop('confirm_password')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'msisdn', 'is_active', 'username', 'password',
                  'confirm_password']


class LoanUploadForm(forms.Form):
    sheetChoice = (
        ('1', 'sheet1'),
        ('2', 'sheet2'),
        ('3', 'sheet3'),
        ('4', 'sheet4'),
        ('5', 'sheet5'),
    )

    rowchoices = (
        ('1', 'Row 1'),
        ('2', 'Row 2'),
        ('3', 'Row 3'),
        ('4', 'Row 4'),
        ('5', 'Row 5')
    )

    choices = list()
    for i in range(65, 91):
        choices.append([i - 65, chr(i)])

    excel_file = forms.FileField()
    sheet = forms.ChoiceField(label="Sheet", choices=sheetChoice, widget=forms.Select(attrs={'class': 'form-control'}))
    row = forms.ChoiceField(label="Row", choices=rowchoices, widget=forms.Select(attrs={'class': 'form-control'}))
    last_name_col = forms.ChoiceField(label='Last Name Column', initial=0, choices=choices,
                                 widget=forms.Select(attrs={'class': 'form-control'}),
                                 help_text='The column containing the Last Name')
    first_name_col = forms.ChoiceField(label='First Name Column', initial=1, choices=choices,
                                      widget=forms.Select(attrs={'class': 'form-control'}),
                                      help_text='The column containing the First Name')
    phone_number_col = forms.ChoiceField(label='Phone Number Column', initial=2, choices=choices,
                                       widget=forms.Select(attrs={'class': 'form-control'}),
                                       help_text='The column containing the Phone Number Name')
    village_col = forms.ChoiceField(label='Village Column', initial=3, choices=choices,
                                      widget=forms.Select(attrs={'class': 'form-control'}),
                                      help_text='The column containing the Village')
    district_col = forms.ChoiceField(label='District Column', initial=4, choices=choices,
                                    widget=forms.Select(attrs={'class': 'form-control'}),
                                    help_text='The column containing the District')
    loan_amount_col = forms.ChoiceField(label='Loan Amount Column', initial=5, choices=choices,
                                     widget=forms.Select(attrs={'class': 'form-control'}),
                                     help_text='The column containing the Loan Amount')


bootstrapify(LoanUploadForm)
bootstrapify(CreditManagerForm)
bootstrapify(CreditManagerUserForm)
