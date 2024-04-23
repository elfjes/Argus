from argus.geant.views import incident_details
from django.urls import path

urlpatterns = [
    path("<int:incident_pk>/", incident_details, name="incident-details")
]
