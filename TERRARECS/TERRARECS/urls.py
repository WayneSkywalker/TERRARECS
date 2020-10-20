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
from recommender.views import index, detail, recommend_default, recommend_with_setting
from recommender.views import showSetting, addSetting, editSetting, updateSetting, deleteSetting
from recommender.views import upload_address, upload_pages, upload_txns, upload_places, upload_transits

urlpatterns = [
    path('', index, name = 'index'),
    path('admin/', admin.site.urls),
    path('<int:page_id>', detail, name = 'detail'),
    path('recommend_default/<int:page_id>', recommend_default, name = 'recommend_default'),
    # path('recommend/<int:page_id>/<str:setting_name>', recommend, name = 'recommend'),
    path('recommend_with_setting/<int:page_id>/<str:setting_name>', recommend_with_setting, name = 'recommend_with_setting'),
    path('settings', showSetting, name = 'showSetting'),
    path('settings/add', addSetting, name = 'addSetting'),
    path('settings/edit/<int:id>', editSetting, name = 'editSetting'),
    path('settings/update/<int:id>', updateSetting, name = 'updateSetting'),
    path('settings/delete/<int:id>', deleteSetting, name = 'deleteSetting'),
    path('upload-address-data/', upload_address, name = 'upload_address'),
    path('upload-pages-data/', upload_pages, name = 'upload_pages'),
    path('upload-txns-data/', upload_txns, name = 'upload_txns'),
    path('upload-places-data/', upload_places, name = 'upload_places'),
    path('upload-transits-data/', upload_transits, name = 'upload_transits'),
]