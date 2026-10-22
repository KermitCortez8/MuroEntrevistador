"""Retira las claves que la antigua interfaz guardaba en sesiones del servidor."""

from django.contrib.sessions.backends.db import SessionStore
from django.db import migrations


def remove_saved_keys(apps, schema_editor):
    session_model = apps.get_model("sessions", "Session")
    alias = schema_editor.connection.alias
    codec = SessionStore()
    for row in session_model.objects.using(alias).only("session_key", "session_data").iterator():
        data = codec.decode(row.session_data)
        if "api_key" in data:
            data.pop("api_key")
            session_model.objects.using(alias).filter(pk=row.pk).update(
                session_data=codec.encode(data)
            )


class Migration(migrations.Migration):
    dependencies = [("entrevistador", "0001_initial")]
    operations = [migrations.RunPython(remove_saved_keys, migrations.RunPython.noop)]
