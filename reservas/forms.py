from django import forms


class BulkUserUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Archivo Excel',
        help_text='Sube un archivo .xlsx con los datos de los usuarios'
    )
    send_welcome_email = forms.BooleanField(
        label='Enviar email de bienvenida',
        required=False,
        initial=True,
        help_text='Envía las credenciales por email a cada usuario creado'
    )