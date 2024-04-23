from argus.incident.models import Incident
from django.shortcuts import get_object_or_404, render

def incident_details(request, incident_pk):
    incident = get_object_or_404(Incident.objects.prefetch_related("endpoint_events"), pk=incident_pk)
    return render(request, "incident_details.html", context={
        "incident": incident,
        "page_title": "Incident details"
    })