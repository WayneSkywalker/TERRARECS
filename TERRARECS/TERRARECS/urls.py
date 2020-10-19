"""TERRARECS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from recommender.views import index, detail, recommend_default, recommend, upload_address, upload_pages, upload_txns, upload_places

urlpatterns = [
    path('', index, name = 'index'),
    path('admin/', admin.site.urls),
    path('<int:page_id>', detail, name = 'detail'),
    path('recommend_default/<int:page_id>', recommend_default, name = 'recommend_default'),
    path('recommend/<int:page_id>/<str:setting_name>', recommend, name = 'recommend'),
    path('upload-address-data/', upload_address, name = 'upload_address'),
    path('upload-pages-data/', upload_pages, name = 'upload_pages'),
    path('upload-txns-data/', upload_txns, name = 'upload_txns'),
    path('upload-places-data/', upload_places, name = 'upload_places'),
]
