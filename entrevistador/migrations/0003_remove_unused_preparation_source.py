"""Limpia un dato de la interfaz anterior sin cambiar la práctica guardada."""

from django.db import migrations


def remove_unused_source(apps, schema_editor):
    workspace_model = apps.get_model("entrevistador", "Workspace")
    workspaces = workspace_model.objects.using(schema_editor.connection.alias)
    for workspace in workspaces.only("pk", "state").iterator():
        state = workspace.state
        preparation = state.get("preparation", {})
        if "source" in preparation:
            preparation.pop("source")
            workspaces.filter(pk=workspace.pk).update(state=state)


class Migration(migrations.Migration):
    dependencies = [("entrevistador", "0002_remove_saved_credentials")]
    operations = [migrations.RunPython(remove_unused_source, migrations.RunPython.noop)]
