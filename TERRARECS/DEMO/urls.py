from django.urls import path

from .views import index, getSettings, addSetting, editSetting, updateSetting, deleteSetting
from .views import index_upload, uploadPages, uploadTxns, uploadAddress, uploadPlaces, uploadTransits
from .views import index_recommender, recommender_default, recommender_with_params, recommender_with_setting
from .views import recommend_default, recommend_with_params, recommend_with_setting

urlpatterns = [
    path('', index, name = 'index'),
    path('recommender/', index_recommender, name = 'index_recommender'),
    path('recommender/default', recommender_default, name = 'recommender_default'),
    path('recommender/params', recommender_with_params, name = 'recommender_with_params'),
    path('recommender/setting', recommender_with_setting, name = 'recommender_with_setting'),
    path('recommender/default/recommend', recommend_default, name = 'recommend_default'),
    path('recommender/params/recommend', recommend_with_params, name = 'recommend_with_params'),
    path('recommender/setting/recommend', recommend_with_setting, name = 'recommend_with_setting'),
    path('upload_data/', index_upload, name = 'index_upload'),
    path('upload_data/property_posts', uploadPages, name = 'uploadPages'),
    path('upload_data/txns', uploadTxns, name = 'uploadTxns'),
    path('upload_data/address', uploadAddress, name = 'uploadAddress'),
    path('upload_data/places', uploadPlaces, name = 'uploadPlaces'),
    path('upload_data/transits', uploadTransits, name = 'uploadTransits'),
    path('setting/', getSettings, name = 'getSettings'),
    path('setting/add/', addSetting, name = 'addSetting'),
    path('setting/edit/<int:id>', editSetting, name = 'editSetting'),
    path('setting/update/<int:id>', updateSetting, name = 'updateSetting'),
    path('setting/delete/<int:id>', deleteSetting, name = 'deleteSetting'),
]