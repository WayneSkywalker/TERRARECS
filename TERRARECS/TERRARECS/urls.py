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
from recommender.views import index, detailPage, recommend_default, recommend_with_params, recommend_with_setting
from recommender.views import getPages, detailPage, addPage, deletePage, updatePage
from recommender.views import getPlaces, detailPlaces, addPlace, updatePlace, deletePlace
from recommender.views import getTransits, detailTransit, addTransit, updateTransit, deleteTransit
from recommender.views import getProvinces, detailProvince, addProvince, updateProvince, deleteProvince
from recommender.views import getAmphurs, detailAmphur, addAmphur, updateAmphur, deleteAmphur
from recommender.views import getDistricts, detailDistrict, addDistrict, updateDistrict, deleteDistrict
from recommender.views import showSettings, detailSetting, addSetting, updateSetting, deleteSetting
from recommender.views import upload_address, upload_pages, upload_txns, upload_places, upload_transits

urlpatterns = [
    path('', index, name = 'index'),
    path('admin/', admin.site.urls),
    path('recommend/<int:page_id>', recommend_with_params, name = 'recommend_with_params'),
    path('recommend_default/<int:page_id>', recommend_default, name = 'recommend_default'),
    path('recommend_with_setting/<int:page_id>/<str:setting_name>', recommend_with_setting, name = 'recommend_with_setting'),
    path('settings', showSettings, name = 'showSettings'),
    path('settings/<str:setting_name>', detailSetting, name = 'detailSetting'),
    path('settings/add/', addSetting, name = 'addSetting'),
    path('settings/update/<int:id>', updateSetting, name = 'updateSetting'),
    path('settings/delete/<int:id>', deleteSetting, name = 'deleteSetting'),
    path('upload-address-data/', upload_address, name = 'upload_address'),
    path('upload-pages-data/', upload_pages, name = 'upload_pages'),
    path('upload-txns-data/', upload_txns, name = 'upload_txns'),
    path('upload-places-data/', upload_places, name = 'upload_places'),
    path('upload-transits-data/', upload_transits, name = 'upload_transits'),
    path('page', getPages, name = 'getPages'),
    path('page/<int:page_id>', detailPage, name = 'detailPage'),
    path('page/add/', addPage, name = 'addPage'),
    path('page/update/<int:page_id>', updatePage, name = 'updatePage'),
    path('page/delete/<int:page_id>', deletePage, name = 'deletePage'),
    path('place', getPlaces, name = 'getPlaces'),
    path('place/<int:id>', detailPlaces, name = 'detailPlaces'),
    path('place/add/', addPlace, name = 'addPlace'),
    path('place/update/<int:id>', updatePlace, name = 'updatePlace'),
    path('place/delete/<int:id>', deletePlace, name = 'deletePlace'),
    path('transit', getTransits, name = 'getTransits'),
    path('transit/<int:id>', detailTransit, name = 'detailTransit'),
    path('transit/add/', addTransit, name = 'addTransit'),
    path('transit/update/<int:id>', updateTransit, name = 'updateTransit'),
    path('transit/delete/<int:id>', deleteTransit, name = 'deleteTransit'),
    path('province', getProvinces, name = 'getProvinces'),
    path('province/<int:province_id>', detailProvince, name = 'detailProvince'),
    path('province/add/', addProvince, name = 'addProvince'),
    path('province/update/<int:province_id>', updateProvince, name = 'updateProvince'),
    path('province/delete/<int:province_id>', deleteProvince, name = 'deleteProvince'),
    path('amphur', getAmphurs, name = 'getAmphurs'),
    path('amphur/<int:amphur_id>', detailAmphur, name = 'detailAmphur'),
    path('amphur/add/', addAmphur, name = 'addAmphur'),
    path('amphur/update/<int:amphur_id>', updateAmphur, name = 'updateAmphur'),
    path('amphur/delete/<int:amphur_id>', deleteAmphur, name = 'deleteAmphur'),
    path('district', getDistricts, name = 'getDistricts'),
    path('district/<int:district_id>', detailDistrict, name = 'detailDistrict'),
    path('district/add/', addDistrict, name = 'addDistrict'),
    path('district/update/<int:district_id>', updateDistrict, name = 'updateDistrict'),
    path('district/delete/<int:district_id>', deleteDistrict, name = 'deleteDistrict'),
]