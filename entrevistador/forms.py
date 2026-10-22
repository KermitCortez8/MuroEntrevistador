from django import forms

from entrevistador.domain.documents import MAX_FILE_BYTES
from entrevistador.integrations.gemini import MAX_AUDIO_BYTES


class PreparationForm(forms.Form):
    context = forms.CharField(required=False, max_length=20_000)
    document = forms.FileField(required=False)
    level = forms.ChoiceField(
        choices=[(x, x) for x in ["Inicial", "Intermedio", "Avanzado"]],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    language = forms.ChoiceField(
        choices=[("es", "Español"), ("en", "English")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    question_limit = forms.IntegerField(
        min_value=1, max_value=15, widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    mode = forms.ChoiceField(
        choices=[("Texto", "Texto"), ("Audio", "Audio")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_document(self):
        document = self.cleaned_data["document"]
        if document and document.size > MAX_FILE_BYTES:
            raise forms.ValidationError("El archivo supera el límite de 5 MB.")
        return document


class AnswerForm(forms.Form):
    mode = forms.ChoiceField(choices=[("Texto", "Texto"), ("Audio", "Audio")])
    written = forms.CharField(required=False, max_length=12_000, strip=False)
    transcript = forms.CharField(required=False, max_length=12_000, strip=False)
    recording = forms.FileField(required=False)

    def clean_recording(self):
        recording = self.cleaned_data["recording"]
        if recording and recording.size > MAX_AUDIO_BYTES:
            raise forms.ValidationError("Graba una respuesta de hasta 14 MB.")
        return recording
