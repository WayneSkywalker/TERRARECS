from django.urls import path

from .views import recommend_default, recommend_with_params, recommend_with_setting
from .views import getPages, detailPage, addPage, deletePage, updatePage
from .views import getPlaces, detailPlaces, addPlace, updatePlace, deletePlace
from .views import getTransits, detailTransit, addTransit, updateTransit, deleteTransit
from .views import getProvinces, detailProvince, addProvince, updateProvince, deleteProvince
from .views import getAmphurs, detailAmphur, addAmphur, updateAmphur, deleteAmphur
from .views import getDistricts, detailDistrict, addDistrict, updateDistrict, deleteDistrict
from .views import showSettings, detailSetting, addSetting, updateSetting, deleteSetting
from .views import upload_address, upload_pages, upload_txns, upload_places, upload_transits

app_name = 'recommender'

urlpatterns = [
    # path('', index, name = 'index'),
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