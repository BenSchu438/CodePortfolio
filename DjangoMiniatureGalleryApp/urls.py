from django.urls import path

from . import views

app_name = 'MiniatureGallery'
urlpatterns = [
    path("", views.BatchIndexFunc, name='batchindex'),
    path("<int:pk>/", views.BatchDetailView.as_view(), name='batchdetail'),
    path("storage/", views.StorageIndexView.as_view(), name='storageindex'),
    path("storage/<str:storage_id>/", views.StorageDetailFunc, name='storagedetail'),
]
