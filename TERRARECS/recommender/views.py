from django.shortcuts import render, redirect # unused
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.core import serializers
from django.db import IntegrityError
from .models import Province, Amphur, District, Page, Transaction, Place, Setting, Transit

from .cb_model import CBRecommender
from .cf_model import CFRecommender
from .hybrid_model import HybridRecommender

import pandas as pd
from math import sin, cos, sqrt, atan2, radians
import json

# just a function, not an API
def get_distance(x1,y1,x2,y2):
    # approximate radius of the earth in km.
    R = 6373.0
    latitude_1 = radians(x1)
    longitude_1 = radians(y1)
    latitude_2 = radians(x2)
    longitude_2 = radians(y2)

    d_longitude = longitude_2 - longitude_1
    d_latitude = latitude_2 - latitude_1

    a = sin(d_latitude / 2)**2 + cos(latitude_1) * cos(latitude_2) * sin(d_longitude / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance

###### APIs begin here. ######

#### CSV Upload APIs ####
def upload_address(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.csv'):
            response['status'] = '400'
            response['message'] = 'This is not the CSV file.'
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        df_address = pd.read_csv(csv_file)
        df_address_columns = ['district_id','district_th','amphur_id','amphur_th','province_id','province_th']
        check = all(column in df_address.columns.tolist() for column in df_address_columns)

        if not check:
            response['status'] = '400'
            response['message'] = 'Columns of the CSV should contain \'district_id\', \'district_th\', \'amphur_id\', \'amphur_th\' , \'province_id\', and \'province_th\'.'
            response['data'] = df_address.columns.tolist()
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        df_provinces = df_address[['province_id','province_th']].dropna().drop_duplicates().sort_values(by = ['province_id'])
        df_amphur = df_address[['amphur_id','amphur_th','province_id']].dropna().drop_duplicates().sort_values(by = ['amphur_id'])
        df_district = df_address.drop(columns = ['amphur_th','province_th']).drop_duplicates().sort_values(by = ['district_id'])

        for index, row in df_provinces.iterrows():
            _, created = Province.objects.update_or_create(province_id = row['province_id'], th = row['province_th'])

        for index, row in df_amphur.iterrows():
            province = Province.objects.get(province_id = row['province_id'])

            _, created = Amphur.objects.update_or_create(amphur_id = row['amphur_id'], th = row['amphur_th'], province = province)

        for index, row in df_district.iterrows():
            amphur = Amphur.objects.get(amphur_id = row['amphur_id'])

            _, created = District.objects.update_or_create(district_id = row['district_id'], th = row['district_th'], amphur = amphur)
        response['status'] = '200'
        response['message'] = 'Upload address data successfully'
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def upload_pages(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.csv'):
            response['status'] = '400'
            response['message'] = 'This is not the CSV file.'
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        df_pages = pd.read_csv(csv_file)
        df_pages_columns = df_pages.columns.tolist()
        df_pages_columns_amust = ['id','title_th','title_en','lat','lng','rent_price','sell_price','area_id'\
            ,'post_type','house_type','landarea_total_sqw','areasize_sqm','room_type','district_id','amphur_id','province_id']
        check = all(column in df_pages_columns for column in df_pages_columns_amust)

        if not check:
            response['status'] = '400'
            response['message'] = 'Columns of the CSV should contain \'id\', \'title_th\', \'title_en\', \'lat\', \'lng\', \'rent_price\', \'sell_price\', \'area_id\', \'post_type\', \'house_type\', \'landarea_total_sqw\', \'areasize_sqm\', \'room_type\', \'district_id\', \'amphur_id\', and \'province_id\'.'
            response['data'] = df_pages.columns.tolist()
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        # ['Supermarket/ Convenience Store', 'school, university, education places', 'Department Store']
        flag_distances = 0
        flag_supermarket = False    
        flag_department_store = False
        flag_education = False
        flag_transit = False
        distances_list = ['distances_supermarket','distances_department_store','distances_education','distances_transit']

        for e in distances_list:
            if e not in df_pages_columns:
                flag_distances += 1
        if flag_distances != 0:
            df_places = pd.DataFrame(list(Place.objects.all().values()))
            df_place_supermarket = df_places[df_places['poi_type'] == 'Supermarket/ Convenience Store']
            df_place_department_store = df_places[df_places['poi_type'] == 'Department Store']
            df_place_education = df_places[df_places['poi_type'] == 'school, university, education places']

            if 'distances_supermarket' not in df_pages_columns:
                flag_supermarket = True
            if 'distances_department_store' not in df_pages_columns:
                flag_department_store = True
            if 'distances_education' not in df_pages_columns:
                flag_education = True
            if 'distances_transit' not in df_pages_columns:
                flag_transit = True
                df_transits = pd.DataFrame(list(Transit.objects.all().values()))

            distances_supermarket = []
            distances_department_store = []
            distances_education = []
            distances_transit = []
            for index, row in df_pages.iterrows():
                supermarket_distance = 10000000
                department_store_distance = 10000000
                education_distance = 10000000
                transit_distance = 10000
                if flag_supermarket:
                    df_place_supermarket_temp = df_place_supermarket[df_place_supermarket.province_id == row['province_id']] 
                    for index_supermarket, row_supermarket in df_place_supermarket_temp.iterrows():
                        d = get_distance(row['lat'], row['lng'], row_supermarket['latitude'], row_supermarket['longitude'])
                        if d < supermarket_distance:
                            supermarket_distance = d
                    distances_supermarket.append(supermarket_distance)
                if flag_department_store:
                    df_place_department_store_temp = df_place_department_store[df_place_department_store.province_id == row['province_id']]
                    for index_department_store, row_department_store in df_place_department_store_temp.iterrows():
                        d = get_distance(row['lat'], row['lng'], row_department_store['latitude'], row_department_store['longitude'])
                        if d < department_store_distance:
                            department_store_distance = d
                    distances_department_store.append(department_store_distance)
                if flag_education:
                    df_place_education_temp = df_place_education[df_place_education.province_id == row['province_id']]
                    for index_education, row_education in df_place_education_temp.iterrows():
                        d = get_distance(row['lat'], row['lng'], row_education['latitude'], row_education['longitude'])
                        if d < education_distance:
                            education_distance = d
                    distances_education.append(education_distance)
                if flag_transit:
                    for index_transit, row_transit in df_transits.iterrows():
                        d = get_distance(row['lat'], row['lng'], row_transit['latitude'], row_transit['longitude'])
                        if d < transit_distance:
                            transit_distance = d
                    distances_transit.append(transit_distance)
            if flag_supermarket:
                df_pages['distances_supermarket'] = distances_supermarket
                del df_place_supermarket_temp
            if flag_department_store:
                df_pages['distances_department_store'] = distances_department_store
                del df_place_department_store_temp
            if flag_education:        
                df_pages['distances_education'] = distances_education
                del df_place_education_temp
            if flag_transit:
                df_pages['distances_transit'] = distances_transit
                del df_transits
            del df_places, distances_supermarket, distances_department_store, distances_education, distances_transit, supermarket_distance, department_store_distance, education_distance, transit_distance, d
        del distances_list, flag_distances, flag_supermarket, flag_department_store, flag_education, flag_transit

        for index, row in df_pages.iterrows():
            district = District.objects.get(district_id = row['district_id'])
            amphur = Amphur.objects.get(amphur_id = row['amphur_id'])
            province = Province.objects.get(province_id = row['province_id'])

            _, created = Page.objects.update_or_create(page_id = row['id'], title_th = row['title_th'], title_en = row['title_en'] \
                , lat = row['lat'], lng = row['lng'], rent_price = row['rent_price'], sale_price = row['sell_price'], area_id = row['area_id']\
                , post_type = row['post_type'], house_type = row['house_type'], landarea_total_sqw = row['landarea_total_sqw'] \
                , area_size_sqm = row['areasize_sqm'], room_type = row['room_type']\
                , distances_supermarket = row['distances_supermarket'], distances_department_store = row['distances_department_store']\
                , distances_education = row['distances_education'], distances_transit = row['distances_transit']\
                , province = province, amphur = amphur, district = district)
        response['status'] = '200'
        response['message'] = 'Upload pages data successfully'
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def upload_txns(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.csv'):
            response['status'] = '400'
            response['message'] = 'This is not the CSV file.'
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        df_txns = pd.read_csv(csv_file)

        # txns dataset preparation codes here.
        df_txns_true_columns = ['userID','page','event_strength']
        df_txns_raw_columns = ['ID', 'page', 'look_tel', 'look_information']
        check_1 = all(column in df_txns.columns.tolist() for column in df_txns_true_columns)
        check_2 = all(column in df_txns.columns.tolist() for column in df_txns_raw_columns)

        if not check_1:
            if check_2:
                df_txns = df_txns.rename(columns = {'ID':'userID'})
                df_txns_columns = df_txns.columns.tolist()

                event_type_list_1 = []
                event_type_list_2 = []
                event_type_list_3 = []
                df_txns_look_tel = pd.DataFrame(columns = df_txns_columns)
                df_txns_look_info = pd.DataFrame(columns = df_txns_columns)
                for index, row in df_txns.iterrows():
                    event_type_list_1.append('VIEW')
                    if row['look_tel'] != 0:
                        r = row.to_frame().T
                        df_txns_look_tel = df_txns_look_tel.append(r, ignore_index = True)
                        event_type_list_2.append('LOOK_TEL')
                    if row['look_information'] != 0:
                        r = row.to_frame().T
                        df_txns_look_info = df_txns_look_info.append(r, ignore_index = True)
                        event_type_list_3.append('LOOK_INFO')
                df_txns['event_type'] = event_type_list_1
                df_txns_look_tel['event_type'] = event_type_list_2
                df_txns_look_info['event_type'] = event_type_list_3
                if df_txns_look_tel.shape[0] != 0:
                    df_txns = df_txns.append(df_txns_look_tel, ignore_index = True)
                if df_txns_look_info.shape[0] != 0:
                    df_txns = df_txns.append(df_txns_look_info, ignore_index = True)
                df_txns = df_txns.drop(columns = ['look_tel','look_information'])

                event_type_strength = {
                    'VIEW': 1.0,
                    'LOOK_INFO': 2.0,
                    'LOOK_TEL': 2.5
                }
                df_txns['event_strength'] = df_txns['event_type'].apply(lambda x: event_type_strength[x])

                df_user_txns_count = df_txns.groupby(['userID','page']).size().groupby('userID').size()

                import math
                def smooth_user_preference(x):
                    return math.log(1 + x, 2)

                df_user_3_20 = df_user_txns_count[df_user_txns_count.isin(range(3,21))].reset_index()
                df_trans_from_user_3_20 = df_txns[df_txns.userID.isin(df_user_3_20.userID.tolist())]

                df_txns = df_trans_from_user_3_20.groupby(['userID','page'])['event_strength'].sum().apply(smooth_user_preference).reset_index()
            else:
                response['status'] = '400'
                response['message'] = 'Columns of the CSV should contain [\'userID\', \'page\', \'event_strength\'] or [\'ID\', \'page\', \'look_tel\', and \'look_information\'].'
                response['data'] = df_txns.columns.tolist()
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        for index, row in df_txns.iterrows():
            try:
                page = Page.objects.get(page_id = row['page'])
            except Page.DoesNotExist:
                continue

            _, created = Transaction.objects.update_or_create(userID = row['userID'], page = page, event_strength = row['event_strength'])
        response['status'] = '200'
        response['message'] = 'Upload transactions data successfully'
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def upload_places(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.csv'):
            response['status'] = '400'
            response['message'] = 'This is not the CSV file.'
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        df_places = pd.read_csv(csv_file)
        df_places_columns = ['name_th', 'latitude', 'longtitude', 'district_id', 'amphur_id', 'province_id']
        check = all(column in df_places.columns.tolist() for column in df_places_columns)

        if not check:
            response['status'] = '400'
            response['message'] = 'Columns of the CSV should contain \'name_th\', \'latitude\', \'longtitude\', \'district_id\', \'amphur_id\', , and \'province_id\'.'
            response['data'] = df_places.columns.tolist()
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        for index, row in df_places.iterrows():
            district = District.objects.get(district_id = row['district_id'])
            amphur = Amphur.objects.get(amphur_id = row['amphur_id'])
            province = Province.objects.get(province_id = row['province_id'])

            _, created = Place.objects.update_or_create(name_th = row['name_th'] \
                , latitude = row['latitude'], longitude = row['longitude'], poi_type = row['poi_type'], district = district \
                , amphur = amphur, province = province)
        response['status'] = '200'
        response['message'] = 'Upload places data successfully'
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def upload_transits(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':

        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.csv'):
            response['status'] = '400'
            response['message'] = 'This is not the CSV file.'
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        df_transits = pd.read_csv(csv_file)
        df_transits_columns = ['en', 'th', 'latitude', 'longitude']
        check = all(column in df_transits.columns.tolist() for column in df_transits_columns)

        if not check:
            response['status'] = '400'
            response['message'] = 'Columns of the CSV should contain \'en\', \'th\', \'latitude\', and \'longitude\'.'
            response['data'] = df_transits.columns.tolist()
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        for index, row in df_transits.iterrows():
            _, created = Transit.objects.update_or_create(name_th = row['th'], name_en = row['en'], latitude = row['latitude'], longitude = row['longitude'])
        response['status'] = '200'
        response['message'] = 'Upload transits data successfully'
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

#### Recommender APIs ####
def recommend_default(request, page_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':

        try:
            page = Page.objects.get(pk = page_id)
        except Page.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Page with id ' + str(page_id) + ' does not exist.'
            response['data'] = { 'page_id': page_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')

        df_pages = pd.DataFrame(list(Page.objects.all().values()))
        df_txns = pd.DataFrame(list(Transaction.objects.all().values()))

        cb_model = CBRecommender(df_pages)
        cf_model = CFRecommender(df_txns, df_pages)

        hybrid_model = HybridRecommender(cb_model, cf_model, df_pages)

        df_recs = hybrid_model.recommend(page_id)
        df_recs_list = df_recs['page_id'].tolist()

        data = {
            'recommendation_list': df_recs_list
        }

        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data

        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def recommend_with_params(request, page_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            page = Page.objects.get(pk = page_id)
        except Page.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Page with id ' + str(page_id) + ' does not exist.'
            response['data'] = { 'page_id': page_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')

        # error handlers
        try:
            recs_type = int(request.GET['recs_type'])
        except ValueError:
            response['message'] = 'Recommendation type value is not valid.'
            response['data'] = { 'recs_type': request.GET['recs_type'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        if recs_type not in list(range(1,4)): # 1, 2, 3
            response['message'] = 'Recommendation type does not exist.'
            response['data'] = { 'recs_type': recs_type }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            cb_ensemble_weight = float(request.GET['cb_ensemble_weight'])
        except ValueError:
            if request.GET['cb_ensemble_weight'] == "":
                cb_ensemble_weight = 1.0
            else:
                response['message'] = 'CB weight value is not valid.'
                response['data'] = { 'cb_ensemble_weight': request.GET['cb_ensemble_weight'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            cf_ensemble_weight = float(request.GET['cf_ensemble_weight'])
        except ValueError:
            if request.GET['cf_ensemble_weight'] == "":
                cf_ensemble_weight = 1.0
            else:
                response['message'] = 'CF weight value is not valid.'
                response['data'] = { 'cf_ensemble_weight': request.GET['cf_ensemble_weight'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            k = int(request.GET['k'])
        except ValueError:
            if request.GET['k'] == "":
                k = 10
            else:
                response['message'] = 'K value is not valid.'
                response['data'] = { 'k': request.GET['k'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        if k <= 0:
            response['message'] = 'K value must be a positive integer and not zero.'
            response['data'] = { 'k': int(request.GET['k']) }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            topn = int(request.GET['topn'])
        except ValueError:
            if request.GET['topn'] == "":
                topn = None
            else:
                response['message'] = 'topn value is not valid.'
                response['data'] = { 'topn': request.GET['topn'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        if topn:
            if topn <= 0:
                response['message'] = 'topn value must be a positive integer and not zero.'
                response['data'] = { 'topn': int(request.GET['topn']) }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            n_cb = int(request.GET['n_cb'])
        except ValueError:
            if request.GET['n_cb'] == "":
                n_cb = None
            else:
                response['message'] = 'n_cb value is not valid.'
                response['data'] = { 'n_cb': request.GET['n_cb'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        if n_cb:
            if n_cb <= 0:
                response['message'] = 'n_cb value must be a positive integer and not zero.'
                response['data'] = { 'n_cb': int(request.GET['n_cb']) }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        try:
            n_cf = int(request.GET['n_cf'])
        except ValueError:
            if request.GET['n_cf'] == "":
                n_cf = None
            else:
                response['message'] = 'n_cf value is not valid.'
                response['data'] = { 'n_cf': request.GET['n_cf'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        if n_cf:
            if n_cf <= 0:
                response['message'] = 'n_cf value must be a positive integer and not zero.'
                response['data'] = { 'n_cf': int(request.GET['n_cf']) }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        df_pages = pd.DataFrame(list(Page.objects.all().values()))
        df_txns = pd.DataFrame(list(Transaction.objects.all().values()))

        cb_model = CBRecommender(df_pages)
        cf_model = CFRecommender(df_txns, df_pages)

        hybrid_model = HybridRecommender(cb_model, cf_model, df_pages, cb_ensemble_weight, cf_ensemble_weight)

        if recs_type == 1:
            df_recs = hybrid_model.recommend(page_id, k, topn)
        elif recs_type == 2:
            df_recs = hybrid_model.recommend_with_top_3cb(page_id, k, topn)
        else:
            df_recs = hybrid_model.recommend_without_weights(page_id, k, n_cb, n_cf, topn)
        
        df_recs_list = df_recs['page_id'].tolist()

        data = {
            'recommendation_list': df_recs_list
        }

        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data

        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def recommend_with_setting(request, page_id, setting_name):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            page = Page.objects.get(pk = page_id)
        except Page.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Page with id ' + str(page_id) + ' does not exist.'
            response['data'] = { 'page_id': page_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')

        try:
            setting = Setting.objects.get(setting_name = setting_name)
        except Setting.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Setting name \'' + setting_name + '\' does not exist.'
            response['data'] = { 'setting_name': setting_name }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')

        df_pages = pd.DataFrame(list(Page.objects.all().values()))
        df_txns = pd.DataFrame(list(Transaction.objects.all().values()))

        cb_model = CBRecommender(df_pages)
        cf_model = CFRecommender(df_txns, df_pages)

        hybrid_model = HybridRecommender(cb_model, cf_model, df_pages, setting.cb_ensemble_weight, setting.cf_ensemble_weight)

        if setting.k is None or setting.k == 0:
            k = 10
        else:
            k = setting.k

        if setting.recs_type == 1:
            df_recs = hybrid_model.recommend(page_id, k, setting.topn)
        elif setting.recs_type == 2:
            df_recs = hybrid_model.recommend_with_top_3cb(page_id, k, setting.topn)
        else:
            df_recs = hybrid_model.recommend_without_weights(page_id, k, setting.n_cb, setting.n_cf, setting.topn)

        df_recs_list = df_recs['page_id'].tolist()

        data = {
            'recommendation_list': df_recs_list
        }

        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data

        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

#### CRUD page
# get pages does not work.
def getPages(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':

        data = {
            'pages': list(Page.objects.all().values())
        }
        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data
        return JsonResponse(response)

    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def detailPage(request, page_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            page = Page.objects.get(pk = page_id)
            data = {
                'page': {
                    'page_id': page.page_id,
                    'title_th': page.title_th,
                    'title_en': page.title_en,
                    'lat': page.lat,
                    'lng': page.lng,
                    'area_id': page.area_id,
                    'rent_price': page.rent_price,
                    'sale_price': page.sale_price,
                    'post_type': page.post_type,
                    'house_type': page.house_type,
                    'landarea_total_sqw': page.landarea_total_sqw,
                    'area_size_sqm': page.area_size_sqm,
                    'distances_supermarket': page.distances_supermarket,
                    'distances_department_store': page.distances_department_store,
                    'distances_education': page.distances_education,
                    'distances_transit': page.distances_transit,
                    'district': page.district.th,
                    'amphur': page.amphur.th,
                    'province': page.province.th,
                    'room_type': page.room_type,
                }
            }
            response['status'] = '200'
            response['message'] = 'Success'
            response['data'] = data
            return JsonResponse(response)
        except Page.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Page with id ' + str(page_id) + ' does not exist.'
            response['data'] = { 'page_id': page_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def addPage(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        data = json.loads(request.body)

        try:
            province = Province.objects.get(pk = data['province_id'])
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(data['province_id']) + '\' does not exist.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'province_id value is not valid.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            amphur = Amphur.objects.get(pk = data['amphur_id'])
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'amphur with id \'' + str(data['amphur_id']) + '\' does not exist.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'amphur_id value is not valid.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            district = District.objects.get(pk = data['district_id'])
        except District.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'district with id \'' + str(data['district_id']) + '\' does not exist.'
            response['data'] = { 'district_id': data['district_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'district_id value is not valid.'
            response['data'] = { 'district_id': data['district_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        page_columns_amust = ['id','title_th','title_en','lat','lng','rent_price','sell_price','area_id'\
            ,'post_type','house_type','landarea_total_sqw','areasize_sqm','room_type','district_id','amphur_id','province_id']
        page_column = list(data.keys())
        check = all(column in page_column for column in page_columns_amust)

        if not check:
            response['status'] = '400'
            response['message'] = 'Columns of the page should contain \'id\', \'title_th\', \'title_en\', \'lat\', \'lng\', \'rent_price\', \'sell_price\', \'area_id\', \'post_type\', \'house_type\', \'landarea_total_sqw\', \'areasize_sqm\', \'room_type\', \'district_id\', \'amphur_id\', and \'province_id\'.'
            response['data'] = page_column
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        not_str_columns = ['lat','lng','rent_price','sell_price','area_id','post_type','house_type','landarea_total_sqw'\
            ,'areasize_sqm','room_type','district_id','amphur_id','province_id']
        for column in not_str_columns:
            if type(data[column]) == str:
                response['message'] = column + ' cannot be string.'
                response['data'] = data[column]
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if data['area_id'] not in list(range(1,26)):
            response['status'] = '400'
            response['message'] = 'area_id should be in \'1 - 25\'.'
            response['data'] = { 'area_id': data['area_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if data['post_type'] not in list(range(1,6)):
            response['status'] = '400'
            response['message'] = 'post_type should be in \'1 - 5\'.'
            response['data'] = { 'post_type': data['post_type'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        if data['house_type'] not in [6,7,8,9,10,11,197,198,206,207,208,209,210]:
            response['status'] = '400'
            response['message'] = 'house_type should be in [6,7,8,9,10,11,197,198,206,207,208,209,210].'
            response['data'] = { 'house_type': data['house_type'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        if data['room_type'] not in [0,41,42,43,44,45,46,47,48,49,50,51,52,53]:
            response['status'] = '400'
            response['message'] = 'room_type should be in [0,41,42,43,44,45,46,47,48,49,50,51,52,53].'
            response['data'] = { 'room_type': data['room_type'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        if data['room_type'] in [49,50,51,52,53]:
            data['room_type'] = 48

        distances_list = ['distances_supermarket','distances_department_store','distances_education','distances_transit']
        check = all(column in page_column for column in distances_list)

        if not check:
            # compute distances code here
            flag_supermarket = False    
            flag_department_store = False
            flag_education = False
            flag_transit = False
            df_places = pd.DataFrame(list(Place.objects.all().values()))
            df_place_supermarket = df_places[df_places['poi_type'] == 'Supermarket/ Convenience Store']
            df_place_department_store = df_places[df_places['poi_type'] == 'Department Store']
            df_place_education = df_places[df_places['poi_type'] == 'school, university, education places']

            if 'distances_supermarket' not in page_column:
                flag_supermarket = True
            if 'distances_department_store' not in page_column:
                flag_department_store = True
            if 'distances_education' not in page_column:
                flag_education = True
            if 'distances_transit' not in page_column:
                flag_transit = True
                df_transits = pd.DataFrame(list(Transit.objects.all().values()))

            supermarket_distance = 10000000
            department_store_distance = 10000000
            education_distance = 10000000
            transit_distance = 10000
            if flag_supermarket:
                df_place_supermarket_temp = df_place_supermarket[df_place_supermarket.province_id == data['province_id']] 
                for index_supermarket, row_supermarket in df_place_supermarket_temp.iterrows():
                    d = get_distance(data['lat'], data['lng'], row_supermarket['latitude'], row_supermarket['longitude'])
                    if d < supermarket_distance:
                        supermarket_distance = d
            if flag_department_store:
                df_place_department_store_temp = df_place_department_store[df_place_department_store.province_id == data['province_id']]
                for index_department_store, row_department_store in df_place_department_store_temp.iterrows():
                    d = get_distance(data['lat'], data['lng'], row_department_store['latitude'], row_department_store['longitude'])
                    if d < department_store_distance:
                        department_store_distance = d
            if flag_education:
                df_place_education_temp = df_place_education[df_place_education.province_id == data['province_id']]
                for index_education, row_education in df_place_education_temp.iterrows():
                    d = get_distance(data['lat'], data['lng'], row_education['latitude'], row_education['longitude'])
                    if d < education_distance:
                        education_distance = d
            if flag_transit:
                for index_transit, row_transit in df_transits.iterrows():
                    d = get_distance(data['lat'], data['lng'], row_transit['latitude'], row_transit['longitude'])
                    if d < transit_distance:
                        transit_distance = d
            if flag_supermarket:
                data['distances_supermarket'] = supermarket_distance
                del df_place_supermarket_temp
            if flag_department_store:
                data['distances_department_store'] = department_store_distance
                del df_place_department_store_temp
            if flag_education:        
                data['distances_education'] = education_distance
                del df_place_education_temp
            if flag_transit:
                data['distances_transit'] = transit_distance
                del df_transits
            del df_places, supermarket_distance, department_store_distance, education_distance, transit_distance, d
            del df_place_supermarket, df_place_department_store, df_place_education
        else:
            for column in distances_list:
                if type(data[column]) != float:
                    response['message'] = column + ' should be floating point number.'
                    response['data'] = data[column]
                    return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        try:
            page = Page.objects.create(page_id = data['id'], title_th = data['title_th'], title_en = data['title_en'] \
                , lat = data['lat'], lng = data['lng'], rent_price = data['rent_price'], sale_price = data['sell_price'], area_id = data['area_id']\
                , post_type = data['post_type'], house_type = data['house_type'], landarea_total_sqw = data['landarea_total_sqw'] \
                , area_size_sqm = data['areasize_sqm'], room_type = data['room_type']\
                , distances_supermarket = data['distances_supermarket'], distances_department_store = data['distances_department_store']\
                , distances_education = data['distances_education'], distances_transit = data['distances_transit']\
                , province = province, amphur = amphur, district = district)
            page_created = {
                'page': data
            }
            response['status'] = '201'
            response['message'] = 'Created'
            response['data'] = page_created
            return JsonResponse(response)
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except IntegrityError:
            response['message'] = 'Page with id \'' + str(data['id']) + '\' is already exists.'
            response['data'] = { 'id': data['id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def updatePage(request, page_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'PUT':
        data = json.loads(request.body)
        
        try:
            province = Province.objects.get(pk = data['province_id'])
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(data['province_id']) + '\' does not exist.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'province_id value is not valid.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            amphur = Amphur.objects.get(pk = data['amphur_id'])
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'amphur with id \'' + str(data['amphur_id']) + '\' does not exist.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'amphur_id value is not valid.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            district = District.objects.get(pk = data['district_id'])
        except District.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'district with id \'' + str(data['district_id']) + '\' does not exist.'
            response['data'] = { 'district_id': data['district_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'district_id value is not valid.'
            response['data'] = { 'district_id': data['district_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        page_columns_amust = ['id','title_th','title_en','lat','lng','rent_price','sell_price','area_id'\
            ,'post_type','house_type','landarea_total_sqw','areasize_sqm','room_type','district_id','amphur_id'\
            ,'province_id', 'distances_supermarket','distances_department_store','distances_education','distances_transit']
        page_column = list(data.keys())
        check = all(column in page_column for column in page_columns_amust)

        if not check:
            response['status'] = '400'
            response['message'] = 'Columns of the page should contain \'id\', \'title_th\', \'title_en\', \'lat\', \'lng\', \'rent_price\', \'sell_price\', \'area_id\', \'post_type\', \'house_type\', \'landarea_total_sqw\', \'areasize_sqm\', \'room_type\', \'district_id\', \'amphur_id\', and \'province_id\'.'
            response['data'] = page_column
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        not_str_columns = ['lat','lng','rent_price','sell_price','area_id','post_type','house_type','landarea_total_sqw'\
            ,'areasize_sqm','room_type','district_id','amphur_id','province_id','distances_supermarket'\
            ,'distances_department_store','distances_education','distances_transit']
        for column in not_str_columns:
            if type(data[column]) == str:
                response['message'] = column + ' cannot be string.'
                response['data'] = data[column]
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if data['area_id'] not in list(range(1,26)):
            response['status'] = '400'
            response['message'] = 'area_id should be in \'1 - 25\'.'
            response['data'] = { 'area_id': data['area_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if data['post_type'] not in list(range(1,6)):
            response['status'] = '400'
            response['message'] = 'post_type should be in \'1 - 5\'.'
            response['data'] = { 'post_type': data['post_type'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        if data['house_type'] not in [6,7,8,9,10,11,197,198,206,207,208,209,210]:
            response['status'] = '400'
            response['message'] = 'house_type should be in [6,7,8,9,10,11,197,198,206,207,208,209,210].'
            response['data'] = { 'house_type': data['house_type'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        if data['room_type'] not in [0,41,42,43,44,45,46,47,48,49,50,51,52,53]:
            response['status'] = '400'
            response['message'] = 'room_type should be in [0,41,42,43,44,45,46,47,48,49,50,51,52,53].'
            response['data'] = { 'room_type': data['room_type'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        if data['room_type'] in [49,50,51,52,53]:
            data['room_type'] = 48

        try:
            page = Page.objects.get(pk = page_id)
            page = Page.objects.filter(page_id = page_id)
            page.update(page_id = page_id, title_th = data['title_th'], title_en = data['title_en'] \
                , lat = data['lat'], lng = data['lng'], rent_price = data['rent_price'], sale_price = data['sell_price'], area_id = data['area_id']\
                , post_type = data['post_type'], house_type = data['house_type'], landarea_total_sqw = data['landarea_total_sqw'] \
                , area_size_sqm = data['areasize_sqm'], room_type = data['room_type']\
                , distances_supermarket = data['distances_supermarket'], distances_department_store = data['distances_department_store']\
                , distances_education = data['distances_education'], distances_transit = data['distances_transit']\
                , province = province, amphur = amphur, district = district)
            page_updated = {
                'page': data
            }
            response['status'] = '200'
            response['message'] = 'Update Successfully.'
            response['data'] = page_updated
            return JsonResponse(response)
        except Page.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Page with id \'' + str(page_id) + '\' does not exist.'
            response['data'] = { 'page_id': page_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def deletePage(request, page_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'DELETE':
        try:
            page = Page.objects.get(pk = page_id)
            page.delete()
            response['status'] = '200'
            response['message'] = 'Delete Successfully.'
            return JsonResponse(response)
        except Page.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Page with id \'' + str(page_id) + '\' does not exist.'
            response['data'] = { 'page_id': page_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

#### CRUD place
def getPlaces(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        data = {
            'places': list(Place.objects.all().values())
        }
        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def detailPlaces(request, id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            place = Place.objects.get(pk = id)
            data = {
                'place': {
                    'name_th': place.name_th,
                    'latitude': place.latitude,
                    'longitude': place.longitude,
                    'poi_type': place.poi_type,
                    'district': place.district.th,
                    'amphur': place.amphur.th,
                    'province': place.province.th
                }
            }
            response['status'] = '200'
            response['message'] = 'Success'
            response['data'] = data
            return JsonResponse(response)
        except Place.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Place with id \'' + str(id) + '\' does not exist.'
            response['data'] = { 'place_id': id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def addPlace(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        data = json.loads(request.body)

        try:
            province = Province.objects.get(pk = data['province_id'])
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(data['province_id']) + '\' does not exist.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'province_id value is not valid.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            amphur = Amphur.objects.get(pk = data['amphur_id'])
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'amphur with id \'' + str(data['amphur_id']) + '\' does not exist.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'amphur_id value is not valid.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            district = District.objects.get(pk = data['district_id'])
        except District.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'district with id \'' + str(data['district_id']) + '\' does not exist.'
            response['data'] = { 'district_id': data['district_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'district_id value is not valid.'
            response['data'] = { 'district_id': data['district_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if 'poi_type' in data:
            poi_types = ['Supermarket/ Convenience Store', 'school, university, education places', 'Department Store']
            if data['poi_type'] not in poi_types:
                response['message'] = 'Place type ' + data['poi_type'] + \
                    ' does not exist. Place types consist of \'Supermarket/ Convenience Store\', \'school, university, education places\', and \'Department Store\''
                response['data'] = { 'poi_type': data['poi_type'] }
                return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        
        if 'latitude' in data:
            if type(data['latitude']) != float:
                response['message'] = 'latitude must be a floating point number.'
                response['data'] = { 'latitude': data['latitude'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if 'longitude' in data:
            if type(data['longitude']) != float:
                response['message'] = 'longitude must be a floating point number.'
                response['data'] = { 'longitude': data['longitude'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            place = Place.objects.create(name_th = data['name_th'], latitude = data['latitude'], longitude = data['longitude']\
                , poi_type = data['poi_type'], district = district, amphur = amphur, province = province)
            place_created = {
                'place': data
            }
            response['status'] = '201'
            response['message'] = 'Created'
            response['data'] = place_created
            return JsonResponse(response)
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def updatePlace(request, id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'PUT':
        data = json.loads(request.body)

        try:
            province = Province.objects.get(pk = data['province_id'])
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(data['province_id']) + '\' does not exist.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'province_id value is not valid.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            amphur = Amphur.objects.get(pk = data['amphur_id'])
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'amphur with id \'' + str(data['amphur_id']) + '\' does not exist.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'amphur_id value is not valid.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            district = District.objects.get(pk = data['district_id'])
        except District.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'district with id \'' + str(data['district_id']) + '\' does not exist.'
            response['data'] = { 'district_id': data['district_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'district_id value is not valid.'
            response['data'] = { 'district_id': data['district_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if 'poi_type' in data:
            poi_types = ['Supermarket/ Convenience Store', 'school, university, education places', 'Department Store']
            if data['poi_type'] not in poi_types:
                response['message'] = 'Place type ' + data['poi_type'] + \
                    ' does not exist. Place types consist of \'Supermarket/ Convenience Store\', \'school, university, education places\', and \'Department Store\''
                response['data'] = { 'poi_type': data['poi_type'] }
                return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        
        if 'latitude' in data:
            if type(data['latitude']) != float:
                response['message'] = 'latitude must be a floating point number.'
                response['data'] = { 'latitude': data['latitude'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if 'longitude' in data:
            if type(data['longitude']) != float:
                response['message'] = 'longitude must be a floating point number.'
                response['data'] = { 'longitude': data['longitude'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            place = Place.objects.get(pk = id)
            place = Place.objects.filter(id = id)
            place.update(name_th = data['name_th'], latitude = data['latitude'], longitude = data['longitude']\
                , poi_type = data['poi_type'], district = district, amphur = amphur, province = province)
            place_updated = {
                'place': data
            }
            response['status'] = '200'
            response['message'] = 'Update Successfully.'
            response['data'] = place_updated
            return JsonResponse(response)
        except Place.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Place with id \'' + str(id) + '\' does not exist.'
            response['data'] = { 'place_id': id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def deletePlace(request, id):
    response = {
        'status': '400',
        'message': 'Bad Request',
        'data': None
    }
    if request.method == 'DELETE':
        try:
            setting = Place.objects.get(pk = id)
            setting.delete()
            response['status'] = '200'
            response['message'] = 'Delete Successfully.'
            return JsonResponse(response)
        except Place.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Place with id \'' + str(id) + '\' does not exist.'
            response['data'] = { 'place_id': id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

#### CRUD transit
def getTransits(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        data = {
            'transits': list(Transit.objects.all().values())
        }
        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def detailTransit(request, id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            transit = Transit.objects.get(pk = id)
            data = {
                'transit': {
                    'name_th': transit.name_th,
                    'name_en': transit.name_en,
                    'latitude': transit.latitude,
                    'longitude': transit.longitude
                }
            }
            response['status'] = '200'
            response['message'] = 'Success'
            response['data'] = data
            return JsonResponse(response)
        except Transit.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Transit with id \'' + str(id) + '\' does not exist.'
            response['data'] = { 'transit_id': id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def addTransit(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        data = json.loads(request.body)

        if 'latitude' in data:
            if type(data['latitude']) != float:
                response['message'] = 'latitude must be a floating point number.'
                response['data'] = { 'latitude': data['latitude'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if 'longitude' in data:
            if type(data['longitude']) != float:
                response['message'] = 'longitude must be a floating point number.'
                response['data'] = { 'longitude': data['longitude'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            if 'name_en' in data:
                transit = Transit.objects.create(name_th = data['name_th'], name_en = data['name_en']\
                    , latitude = data['latitude'], longitude = data['longitude'])
            else:
                transit = Transit.objects.create(name_th = data['name_th'], latitude = data['latitude'], longitude = data['longitude'])
            transit_created = {
                'transit': data
            }
            response['status'] = '201'
            response['message'] = 'Created'
            response['data'] = transit_created
            return JsonResponse(response)
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def updateTransit(request, id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'PUT':
        data = json.loads(request.body)

        if 'latitude' in data:
            if type(data['latitude']) != float:
                response['message'] = 'latitude must be a floating point number.'
                response['data'] = { 'latitude': data['latitude'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        if 'longitude' in data:
            if type(data['longitude']) != float:
                response['message'] = 'longitude must be a floating point number.'
                response['data'] = { 'longitude': data['longitude'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            transit = Transit.objects.get(pk = id)
            transit = Transit.objects.filter(id = id)
            if 'name_en' in data:
                transit.update(name_th = data['name_th'], name_en = data['name_en'], latitude = data['latitude']\
                    , longitude = data['longitude'])
            else:
                transit.update(name_th = data['name_th'], latitude = data['latitude'], longitude = data['longitude'])
            transit_updated = {
                'transit': data
            }
            response['status'] = '200'
            response['message'] = 'Update successfully'
            response['data'] = transit_updated
            return JsonResponse(response)
        except Transit.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Transit with id \'' + str(id) + '\' does not exist.'
            response['data'] = { 'transit_id': id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def deleteTransit(request, id):
    response = {
        'status': '400',
        'message': 'Bad Request',
        'data': None
    }
    if request.method == 'DELETE':
        try:
            transit = Transit.objects.get(pk = id)
            transit.delete()
            response['status'] = '200'
            response['message'] = 'Delete Successfully.'
            return JsonResponse(response)
        except Transit.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Transit with id \'' + str(id) + '\' does not exist.'
            response['data'] = { 'transit_id': id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

#### CRUD province
def getProvinces(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        data = {
            'provinces': list(Province.objects.all().values())
        }
        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def detailProvince(request, province_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            province = Province.objects.get(province_id = province_id)
            data = {
                'province': {
                    'province_th': province.th,
                    'province_en': province.en
                }
            }
            response['status'] = '200'
            response['message'] = 'Success'
            response['data'] = data
            return JsonResponse(response)
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(province_id) + '\' does not exist.'
            response['data'] = { 'province_id': province_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def addProvince(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        data = json.loads(request.body)

        if 'province_id' in data:
            if type(data['province_id']) != int or data['province_id'] < 0:
                response['message'] = 'province_id must be a positive integer.'
                response['data'] = { 'province_id': data['province_id'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            if 'en' in data:
                province = Province.objects.create(province_id = data['province_id'], th = data['th'], en = data['en'])
            else:
                province = Province.objects.create(province_id = data['province_id'], th = data['th'])
            province_created = {
                'province': data
            }
            response['status'] = '201'
            response['message'] = 'Created'
            response['data'] = province_created
            return JsonResponse(response)
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except IntegrityError:
            response['message'] = 'This province is already exists.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def updateProvince(request, province_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'PUT':
        data = json.loads(request.body)

        if 'province_id' in data:
            if type(data['province_id']) != int:
                response['message'] = 'province_id must be a positive integer.'
                response['data'] = { 'province_id': data['province_id'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            province = Province.objects.get(pk = province_id)
            province = Province.objects.filter(province_id = province_id)
            if 'en' in data:
                province.update(province_id = data['province_id'], th = data['th'], en = data['en'])
            else:
                province.update(province_id = data['province_id'], th = data['th'])
            province_updated = {
                'province': data
            }
            response['status'] = '200'
            response['message'] = 'Update Successfully.'
            response['data'] = province_updated
            return JsonResponse(response)
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(province_id) + '\' does not exist.'
            response['data'] = { 'province_id': province_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except IntegrityError:
            response['message'] = 'This province is already exists.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def deleteProvince(request, province_id):
    response = {
        'status': '400',
        'message': 'Bad Request',
        'data': None
    }
    if request.method == 'DELETE':
        try:
            province = Province.objects.get(pk = province_id)
            province.delete()
            response['status'] = '200'
            response['message'] = 'Delete Successfully.'
            return JsonResponse(response)
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(province_id) + '\' does not exist.'
            response['data'] = { 'province_id': province_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

#### CRUD amphur
def getAmphurs(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        data = {
            'amphurs': list(Amphur.objects.all().values())
        }
        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def detailAmphur(request, amphur_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            amphur = Amphur.objects.get(amphur_id = amphur_id)
            data = {
                'amphur': {
                    'amphur_th': amphur.th,
                    'amphur_en': amphur.en,
                    'province': amphur.province.th
                }
            }
            response['status'] = '200'
            response['message'] = 'Success'
            response['data'] = data
            return JsonResponse(response)
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Amphur with id \'' + str(amphur_id) + '\' does not exist.'
            response['data'] = { 'amphur_id': amphur_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def addAmphur(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        data = json.loads(request.body)

        if 'amphur_id' in data:
            if type(data['amphur_id']) != int or data['amphur_id'] < 0:
                response['message'] = 'amphur_id must be a positive integer.'
                response['data'] = { 'amphur_id': data['amphur_id'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        try:
            province = Province.objects.get(pk = data['province_id'])
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(data['province_id']) + '\' does not exist.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'province_id value is not valid.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            if 'en' in data:
                amphur = Amphur.objects.create(amphur_id = data['amphur_id'], th = data['th'], en = data['en'], province = province)
            else:
                amphur = Amphur.objects.create(amphur_id = data['amphur_id'], th = data['th'], province = province)
            amphur_created = {
                'amphur': data
            }
            response['status'] = '201'
            response['message'] = 'Created'
            response['data'] = amphur_created
            return JsonResponse(response)
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except IntegrityError:
            response['message'] = 'This amphur is already exists.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
            
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def updateAmphur(request, amphur_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'PUT':
        data = json.loads(request.body)
        
        if 'amphur_id' in data:
            if type(data['amphur_id']) != int or data['amphur_id'] < 0:
                response['message'] = 'amphur_id must be a positive integer.'
                response['data'] = { 'amphur_id': data['amphur_id'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        try:
            province = Province.objects.get(pk = data['province_id'])
        except Province.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Province with id \'' + str(data['province_id']) + '\' does not exist.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'province_id value is not valid.'
            response['data'] = { 'province_id': data['province_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            amphur = Amphur.objects.get(pk = amphur_id)
            amphur = Amphur.objects.filter(amphur_id = amphur_id)
            if 'en' in data:
                amphur.update(amphur_id = data['amphur_id'], th = data['th'], en = data['en'], province = province)
            else:
                amphur.update(amphur_id = data['amphur_id'], th = data['th'], province = province)
            amphur_updated = {
                'amphur': data
            }
            response['status'] = '200'
            response['message'] = 'Update Successfully.'
            response['data'] = amphur_updated
            return JsonResponse(response)
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Amphur with id \'' + str(amphur_id) + '\' does not exist.'
            response['data'] = { 'amphur_id': amphur_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except IntegrityError:
            response['message'] = 'This amphur is already exists.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def deleteAmphur(request, amphur_id):
    response = {
        'status': '400',
        'message': 'Bad Request',
        'data': None
    }
    if request.method == 'DELETE':
        try:
            amphur = Amphur.objects.get(pk = amphur_id)
            amphur.delete()
            response['status'] = '200'
            response['message'] = 'Delete Successfully.'
            return JsonResponse(response)
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'amphur with id \'' + str(amphur_id) + '\' does not exist.'
            response['data'] = { 'amphur_id': amphur_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

#### CRUD district
def getDistricts(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        data = {
            'districts': list(District.objects.all().values())
        }
        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def detailDistrict(request, district_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            district = District.objects.get(district_id = district_id)
            data = {
                'district': {
                    'district_th': district.th,
                    'district_en': district.en,
                    'amphur': district.amphur.th
                }
            }
            response['status'] = '200'
            response['message'] = 'Success'
            response['data'] = data
            return JsonResponse(response)
        except District.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'District with id \'' + str(district_id) + '\' does not exist.'
            response['data'] = { 'district_id': district_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def addDistrict(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        data = json.loads(request.body)

        if 'district_id' in data:
            if type(data['district_id']) != int or data['district_id'] < 0:
                response['message'] = 'district_id must be a positive integer.'
                response['data'] = { 'district_id': data['district_id'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        try:
            amphur = Amphur.objects.get(pk = data['amphur_id'])
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'amphur with id \'' + str(data['amphur_id']) + '\' does not exist.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'amphur_id value is not valid.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            if 'en' in data:
                district = District.objects.create(district_id = data['district_id'], th = data['th'], en = data['en'], amphur = amphur)
            else:
                district = District.objects.create(district_id = data['district_id'], th = data['th'], amphur = amphur)
            district_created = {
                'district': data
            }
            response['status'] = '201'
            response['message'] = 'Created'
            response['data'] = district_created
            return JsonResponse(response)
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except IntegrityError:
            response['message'] = 'This district is already exists.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def updateDistrict(request, district_id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'PUT':
        data = json.loads(request.body)

        if 'district_id' in data:
            if type(data['district_id']) != int or data['district_id'] < 0:
                response['message'] = 'district_id must be a positive integer.'
                response['data'] = { 'district_id': data['district_id'] }
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        try:
            amphur = Amphur.objects.get(pk = data['amphur_id'])
        except Amphur.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'amphur with id \'' + str(data['amphur_id']) + '\' does not exist.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except ValueError:
            response['message'] = 'amphur_id value is not valid.'
            response['data'] = { 'amphur_id': data['amphur_id'] }
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            district = District.objects.get(pk = district_id)
            district = District.objects.filter(district_id = district_id)
            if 'en' in data:
                district.update(district_id = data['district_id'], th = data['th'], en = data['en'], amphur = amphur)
            else:
                district.update(district_id = data['district_id'], th = data['th'], amphur = amphur)
            district_updated = {
                'district': data
            }
            response['status'] = '200'
            response['message'] = 'Update Successfully.'
            response['data'] = district_updated
            return JsonResponse(response)
        except District.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'district with id \'' + str(district_id) + '\' does not exist.'
            response['data'] = { 'district_id': district_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except IntegrityError:
            response['message'] = 'This district is already exists.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def deleteDistrict(request, district_id):
    response = {
        'status': '400',
        'message': 'Bad Request',
        'data': None
    }
    if request.method == 'DELETE':
        try:
            district = District.objects.get(pk = district_id)
            district.delete()
            response['status'] = '200'
            response['message'] = 'Delete Successfully.'
            return JsonResponse(response)
        except District.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'district with id \'' + str(district_id) + '\' does not exist.'
            response['data'] = { 'district_id': district_id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

#### CRUD setting
def showSettings(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        data = {
            'setting': list(Setting.objects.all().values())
        }
        response['status'] = '200'
        response['message'] = 'Success'
        response['data'] = data
        return JsonResponse(response)
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def detailSetting(request, setting_name):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'GET':
        try:
            setting = Setting.objects.get(setting_name = setting_name)
            data = {
                'setting': {
                    'setting_name': setting.setting_name,
                    'recs_type': setting.recs_type,
                    'cb_ensemble_weight': setting.cb_ensemble_weight,
                    'cf_ensemble_weight': setting.cf_ensemble_weight,
                    'k': setting.k,
                    'topn': setting.topn,
                    'n_cb': setting.n_cb,
                    'n_cf': setting.n_cf,
                }
            }
            response['status'] = '200'
            response['message'] = 'Success'
            response['data'] = data
            return JsonResponse(response)
        except Setting.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Setting name \'' + setting_name + '\' does not exist.'
            response['data'] = { 'setting_name': setting_name }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def addSetting(request):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'POST':
        data = json.loads(request.body)
        
        if 'recs_type' in data:
            if data['recs_type'] not in list(range(1,4)):
                response['message'] = 'Recommender type must be 1 (NORMAL RECOMMENDER), 2 (RECOMMENDER WITH TOP 3 CONTENT - BASED), or 3 (RECOMMENDER WITHOUT WEIGHTS)'
                response['data'] = data['recs_type']
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        else:
            response['message'] = 'Recommender type is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        columns = ['cb_ensemble_weight','cf_ensemble_weight','k','topn','n_cb','n_cf']
        for column in columns:
            if column not in data:
                if column in ['cb_ensemble_weight', 'cf_ensemble_weight']:
                    data[column] = 1.0
                else:
                    data[column] = None
            elif type(data[column]) == str:
                response['message'] = column + ' has to be a positive integer or zero. not string'
                response['data'] = data[column]
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
            elif column not in ['cb_ensemble_weight', 'cf_ensemble_weight'] and data[column] < 0:
                if column == 'k' and data[column] == 0:
                    response['message'] = column + ' has to be a positive integer. not zero.'
                    response['data'] = data[column]
                    return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
                response['message'] = column + ' has to be a positive integer or zero.'
                response['data'] = data[column]
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            setting = Setting.objects.create(setting_name = data['setting_name'], recs_type = data['recs_type'], \
                cb_ensemble_weight = data['cb_ensemble_weight'], cf_ensemble_weight = data['cf_ensemble_weight'], k = data['k'], \
                topn = data['topn'], n_cb = data['n_cb'], n_cf = data['n_cf'])
            setting_created = {
                'setting': data
            }
            response['status'] = '201'
            response['message'] = 'Created'
            response['data'] = setting_created
            return JsonResponse(response)
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        except IntegrityError:
            response['message'] = 'This setting is already exists.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def updateSetting(request, id):
    response = {
        'status': '400',
        'message': '',
        'data': None
    }
    if request.method == 'PUT':
        data = json.loads(request.body)

        if 'recs_type' in data:
            if data['recs_type'] not in list(range(1,4)):
                response['message'] = 'Recommender type must be 1 (NORMAL RECOMMENDER), 2 (RECOMMENDER WITH TOP 3 CONTENT - BASED), or 3 (RECOMMENDER WITHOUT WEIGHTS)'
                response['data'] = data['recs_type']
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        else:
            response['message'] = 'Recommender type is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
        
        columns = ['cb_ensemble_weight','cf_ensemble_weight','k','topn','n_cb','n_cf']
        for column in columns:
            if column not in data:
                if column in ['cb_ensemble_weight', 'cf_ensemble_weight']:
                    data[column] = 1.0
                else:
                    data[column] = None
            elif type(data[column]) == str:
                response['message'] = column + ' has to be a positive integer or zero. not string'
                response['data'] = data[column]
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
            elif column not in ['cb_ensemble_weight', 'cf_ensemble_weight'] and data[column] < 0:
                if column == 'k' and data[column] == 0:
                    response['message'] = column + ' has to be a positive integer. not zero.'
                    response['data'] = data[column]
                    return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
                response['message'] = column + ' has to be a positive integer or zero.'
                response['data'] = data[column]
                return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

        try:
            setting = Setting.objects.get(pk = id)
            setting = Setting.objects.filter(id = id)
            setting.update(setting_name = data['setting_name'], recs_type = data['recs_type'], \
                cb_ensemble_weight = data['cb_ensemble_weight'], cf_ensemble_weight = data['cf_ensemble_weight'], k = data['k'], \
                topn = data['topn'], n_cb = data['n_cb'], n_cf = data['n_cf'])
            setting_updated = {
                'setting': data
            }
            response['status'] = '200'
            response['message'] = 'Update Successfully.'
            response['data'] = setting_updated
            return JsonResponse(response)
        except Setting.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Setting name \'' + setting_name + '\' does not exist.'
            response['data'] = { 'setting_name': setting_name }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
        except KeyError as e:
            response['message'] = str(e) + ' is required.'
            response['data'] = data
            return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')

def deleteSetting(request, id):
    response = {
        'status': '400',
        'message': 'Bad Request',
        'data': None
    }
    if request.method == 'DELETE':
        try:
            setting = Setting.objects.get(pk = id)
            setting.delete()
            response['status'] = '200'
            response['message'] = 'Delete Successfully.'
            return JsonResponse(response)
        except Setting.DoesNotExist:
            response['status'] = '404'
            response['message'] = 'Setting with id \'' + str(id) + '\' does not exist.'
            response['data'] = { 'setting_id': id }
            return HttpResponseNotFound(json.dumps(response), content_type = 'application/json')
    else:
        response['message'] = 'Wrong request method'
        return HttpResponseBadRequest(json.dumps(response), content_type = 'application/json')