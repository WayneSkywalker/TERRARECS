from django.shortcuts import render, redirect
from recommender.models import Province, Amphur, District, Page, Transaction, Place, Setting, Transit
from recommender.forms import SettingForm

from recommender.cb_model import CBRecommender
from recommender.cf_model import CFRecommender
from recommender.hybrid_model import HybridRecommender

import pandas as pd
import json

def index(request):
    return render(request, 'index.html')

def index_upload(request):
    return render(request, 'upload_data/upload_index.html')

def index_recommender(request):
    return render(request, 'recommender/index_recs.html')

def recommender_default(request):
    return render(request, 'recommender/recs_default.html')

def recommender_with_params(request):
    return render(request, 'recommender/recs_params.html')

def recommender_with_setting(request):
    settings = Setting.objects.all()
    return render(request, 'recommender/recs_setting.html', {'settings': settings})

def recommend_default(request):
    template = 'recommender/recs_default.html'
    prompt = {
        'order': ''
    }
    if request.method == 'GET':
        try:
            page_id = int(request.GET['page_id'])
        except ValueError:
            prompt['order'] = 'Invalid page_id'
            return render(request, template, prompt)

        try:
            page = Page.objects.get(pk = page_id)
        except Page.DoesNotExist:
            prompt['order'] = 'Page with id ' + str(page_id) + ' does not exists.'
            return render(request, template, prompt)

        df_pages = pd.DataFrame(list(Page.objects.all().values()))
        df_txns = pd.DataFrame(list(Transaction.objects.all().values()))

        cb_model = CBRecommender(df_pages)
        cf_model = CFRecommender(df_txns, df_pages)

        hybrid_model = HybridRecommender(cb_model, cf_model, df_pages)

        df_recs = hybrid_model.recommend(page_id)
        df_recs = df_recs[['page_id','title_th','rent_price','sale_price']]

        df_recs_pre_json = df_recs.to_json(orient = 'split')
        df_recs_json = json.loads(df_recs_pre_json)

        result = {
            'page': page,
            'recommendations': df_recs_json
        }
        return render(request, 'recommender/result.html', result)

def recommend_with_params(request):
    template = 'recommender/recs_params.html'
    prompt = {
        'order': ''
    }
    if request.method == 'GET':
        try:
            page_id = int(request.GET['page_id'])
        except ValueError:
            prompt['order'] = 'Invalid page_id'
            return render(request, template, prompt)

        try:
            page = Page.objects.get(pk = page_id)
        except Page.DoesNotExist:
            prompt['order'] = 'Page with id ' + str(page_id) + ' does not exists.'
            return render(request, template, prompt)

        try:
            recs_type = int(request.GET['recs_type'])
        except ValueError:
            prompt['order'] = 'Invalid recommendation type value'
            return render(request, template, prompt)
        if recs_type not in list(range(1,4)): # 1, 2, 3
            prompt['order'] = 'Recommendation type does not exist.'
            return render(request, template, prompt)

        try:
            cb_ensemble_weight = float(request.GET['cb_ensemble_weight'])
        except ValueError:
            if request.GET['cb_ensemble_weight'] == "":
                cb_ensemble_weight = 1.0
            else:
                prompt['order'] = 'CB weight value is not valid.'
                return render(request, template, prompt)

        try:
            cf_ensemble_weight = float(request.GET['cf_ensemble_weight'])
        except ValueError:
            if request.GET['cf_ensemble_weight'] == "":
                cf_ensemble_weight = 1.0
            else:
                prompt['order'] = 'CF weight value is not valid.'
                return render(request, template, prompt)

        try:
            k = int(request.GET['k'])
        except ValueError:
            if request.GET['k'] == "":
                k = 10
            else:
                prompt['order'] = 'K value is not valid.'
                return render(request, template, prompt)
        if k <= 0:
            prompt['order'] = 'K value must be a positive integer and not zero.'
            return render(request, template, prompt)

        try:
            topn = int(request.GET['topn'])
        except ValueError:
            if request.GET['topn'] == "":
                topn = None
            else:
                prompt['order'] = 'topn value is not valid.'
                return render(request, template, prompt)
        if topn:
            if topn <= 0:
                prompt['order'] = 'topn value must be a positive integer and not zero.'
                return render(request, template, prompt)

        try:
            n_cb = int(request.GET['n_cb'])
        except ValueError:
            if request.GET['n_cb'] == "":
                n_cb = None
            else:
                prompt['order'] = 'n_cb value is not valid.'
                return render(request, template, prompt)
        if n_cb:
            if n_cb <= 0:
                prompt['order'] = 'n_cb value must be a positive integer and not zero.'
                return render(request, template, prompt)
        
        try:
            n_cf = int(request.GET['n_cf'])
        except ValueError:
            if request.GET['n_cf'] == "":
                n_cf = None
            else:
                prompt['order'] = 'n_cf value is not valid.'
                return render(request, template, prompt)
        if n_cf:
            if n_cf <= 0:
                prompt['order'] = 'n_cf value must be a positive integer and not zero.'
                return render(request, template, prompt)
        
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

        df_recs = df_recs[['page_id','title_th','rent_price','sale_price']]

        df_recs_pre_json = df_recs.to_json(orient = 'split')
        df_recs_json = json.loads(df_recs_pre_json)

        result = {
            'page': page,
            'recommendations': df_recs_json
        }
        return render(request, 'recommender/result.html', result)

def recommend_with_setting(request):
    template = 'recommender/recs_setting.html'
    prompt = {
        'order': ''
    }
    if request.method == 'GET':
        try:
            page_id = int(request.GET['page_id'])
        except ValueError:
            prompt['order'] = 'Invalid page_id'
            return render(request, template, prompt)

        try:
            page = Page.objects.get(pk = page_id)
        except Page.DoesNotExist:
            prompt['order'] = 'Page with id ' + str(page_id) + ' does not exists.'
            return render(request, template, prompt)

        try:
            setting = Setting.objects.get(setting_name = str(request.GET['setting_name']))
        except Setting.DoesNotExist:
            prompt['order'] = 'Setting name \'' + str(request.GET['setting_name']) + '\' does not exist.'
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

        df_recs = df_recs[['page_id','title_th','rent_price','sale_price']]

        df_recs_pre_json = df_recs.to_json(orient = 'split')
        df_recs_json = json.loads(df_recs_pre_json)

        result = {
            'page': page,
            'recommendations': df_recs_json
        }
        return render(request, 'recommender/result.html', result)

def uploadPages(request):
    template = 'upload_data/upload_pages.html'
    prompt = {
        'order': 'Columns of the CSV should contain \'id\', \'title_th\', \'title_en\', \'lat\', \'lng\', \'rent_price\', \'sell_price\', \'area_id\', \'post_type\', \'house_type\', \'landarea_total_sqw\', \'areasize_sqm\', \'room_type\', \'district_id\', \'amphur_id\', and \'province_id\'.'
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            prompt['order'] = 'This is not the CSV file.'
            return render(request, template, prompt)

        df_pages = pd.read_csv(csv_file)
        df_pages_columns = df_pages.columns.tolist()
        df_pages_columns_amust = ['id','title_th','title_en','lat','lng','rent_price','sell_price','area_id'\
            ,'post_type','house_type','landarea_total_sqw','areasize_sqm','room_type','district_id','amphur_id','province_id']
        check = all(column in df_pages_columns for column in df_pages_columns_amust)

        if not check:
            prompt['order'] = 'FAIL!! Columns of the CSV should contain \'id\', \'title_th\', \'title_en\', \'lat\', \'lng\', \'rent_price\', \'sell_price\', \'area_id\', \'post_type\', \'house_type\', \'landarea_total_sqw\', \'areasize_sqm\', \'room_type\', \'district_id\', \'amphur_id\', and \'province_id\'.'
            return render(request, template, prompt)

        # ['Supermarket/ Convenience Store', 'school, university, education places', 'Department Store']
        distances_list = ['distances_supermarket','distances_department_store','distances_education','distances_transit']
        check = all(column in df_pages_columns for column in distances_list)

        if not check:
            flag_distances = 0
            flag_supermarket = False    
            flag_department_store = False
            flag_education = False
            flag_transit = False

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
        
        prompt['order'] = 'SUCCESS!!'
        return render(request, template, prompt)
    else:
        return render(request, template, prompt)

def uploadTxns(request):
    template = 'upload_data/upload_txns.html'
    prompt = {
        'order': 'Columns of the CSV should contain [\'userID\', \'page\', \'event_strength\'] or [\'ID\', \'page\', \'look_tel\', and \'look_information\'].'
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            prompt['order'] = 'This is not the CSV file.'
            return render(request, template, prompt)

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
                return render(request, template, prompt)

        for index, row in df_txns.iterrows():
            try:
                page = Page.objects.get(page_id = row['page'])
            except Page.DoesNotExist:
                continue

            _, created = Transaction.objects.update_or_create(userID = row['userID'], page = page, event_strength = row['event_strength'])

        prompt['order'] = 'SUCCESS!!'
        return render(request, template, prompt)
    else:
        return render(request, template, prompt)

def uploadAddress(request):
    template = 'upload_data/upload_address.html'
    prompt = {
        'order': 'Columns of the CSV should contain \'district_id\', \'district_th\', \'amphur_id\', \'amphur_th\' , \'province_id\', and \'province_th\'.'
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            prompt['order'] = 'This is not the CSV file.'
            return render(request, template, prompt)

        df_address = pd.read_csv(csv_file)
        df_address_columns = ['district_id','district_th','amphur_id','amphur_th','province_id','province_th']
        check = all(column in df_address.columns.tolist() for column in df_address_columns)

        if not check:
            prompt['order'] = 'FAIL!! Columns of the CSV should contain \'district_id\', \'district_th\', \'amphur_id\', \'amphur_th\' , \'province_id\', and \'province_th\'.'
            return render(request, template, prompt)

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

        prompt['order'] = 'SUCCESS!!'
        return render(request, template, prompt)
    else:
        return render(request, template, prompt)

def uploadPlaces(request):
    template = 'upload_data/upload_places.html'
    prompt = {
        'order': 'Columns of the CSV should contain \'name_th\', \'latitude\', \'longtitude\', \'district_id\', \'amphur_id\', , and \'province_id\'.'
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            prompt['order'] = 'This is not the CSV file.'
            return render(request, template, prompt)

        df_places = pd.read_csv(csv_file)
        df_places_columns = ['name_th', 'latitude', 'longtitude', 'district_id', 'amphur_id', 'province_id']
        check = all(column in df_places.columns.tolist() for column in df_places_columns)

        if not check:
            prompt['order'] = 'FAIL!! Columns of the CSV should contain \'name_th\', \'latitude\', \'longtitude\', \'district_id\', \'amphur_id\', , and \'province_id\'.'
            return render(request, template, prompt)
        
        for index, row in df_places.iterrows():
            district = District.objects.get(district_id = row['district_id'])
            amphur = Amphur.objects.get(amphur_id = row['amphur_id'])
            province = Province.objects.get(province_id = row['province_id'])

            _, created = Place.objects.update_or_create(name_th = row['name_th'] \
                , latitude = row['latitude'], longitude = row['longitude'], poi_type = row['poi_type'], district = district \
                , amphur = amphur, province = province)
        
        prompt['order'] = 'SUCCESS!!'
        return render(request, template, prompt)
    else:
        return render(request, template, prompt)

def uploadTransits(request):
    template = 'upload_data/upload_transits.html'
    prompt = {
        'order': 'Columns of the CSV should contain \'en\', \'th\', \'latitude\', and \'longitude\'.'
    }
    if request.method == 'POST':
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            prompt['order'] = 'This is not the CSV file.'
            return render(request, template, prompt)
        df_transits = pd.read_csv(csv_file)
        df_transits_columns = ['en', 'th', 'latitude', 'longitude']
        check = all(column in df_transits.columns.tolist() for column in df_transits_columns)

        if not check:
            prompt['order'] = 'FAIL!! Columns of the CSV should contain \'en\', \'th\', \'latitude\', and \'longitude\'.'
            return render(request, template, prompt)
        
        for index, row in df_transits.iterrows():
            _, created = Transit.objects.update_or_create(name_th = row['th'], name_en = row['en'], latitude = row['latitude'], longitude = row['longitude'])
        prompt['order'] = 'SUCCESS!!'
        return render(request, template, prompt)
    else:
        return render(request, template, prompt)

def getSettings(request):
    settings = Setting.objects.all()
    return render(request, 'setting/settings.html', {'settings': settings})

def addSetting(request):
    if request.method == 'POST':
        form = SettingForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                return redirect('/setting')
            except:
                pass
    else:
        form = SettingForm()
    return render(request, 'setting/add_setting.html', {'form': form})

def editSetting(request, id):
    setting = Setting.objects.get(pk = id)
    return render(request, 'setting/edit_setting.html', {'setting': setting})

def updateSetting(request, id):
    setting = Setting.objects.get(pk = id)
    form = SettingForm(request.POST, instance = setting)
    if form.is_valid():
        form.save()
        return redirect('/setting')
    return render(request, 'setting/edit_setting.html', {'setting': setting})

def deleteSetting(request, id):
    setting = Setting.objects.get(pk = id)
    setting.delete()
    return redirect('/setting')
