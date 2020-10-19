from django.shortcuts import render
# from django.contrib.auth.decorators import permission_required
from .models import Province, Amphur, District, Page, Transaction, Place, Setting

from .cb_model import CBRecommender
from .cf_model import CFRecommender
from .hybrid_model import HybridRecommender

import pandas as pd

def index(request):
    return render(request, 'index.html')

def detail(request, page_id):
    try:
        page = Page.objects.get(pk = page_id)
    except Page.DoesNotExist:
        return render(request, 'detail.html', {})
    return render(request, 'detail.html', {'page': page})

def upload_address(request):
    template = 'upload_address.html'

    prompt = {
        'order': 'Order of the CSV should be \'district_id\', \district_th\', \'amphur_id\', \'amphur_th\' \
            , \'province_id\', and \'province_th\'.'
    }

    if request.method == 'GET':
        return render(request, template, prompt)

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        prompt_2 = {
            'order': 'This is not the CSV file.'
        }
        return render(request, template, prompt_2)

    df_address = pd.read_csv(csv_file)

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

    context = {}

    return render(request, template, context)

def upload_pages(request):
    template = 'upload_pages.html'

    # prompt = {
    #     'order': 'Order of the CSV should be \'district_id\', \district_th\', \'amphur_id\', \'amphur_th\' \
    #         , \'province_id\', and \'province_th\'.'
    # }

    prompt = {
        'order': 'Damn it.'
    }

    if request.method == 'GET':
        return render(request, template, prompt)

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        prompt_2 = {
            'order': 'This is not the CSV file.'
        }
        return render(request, template, prompt_2)

    df_pages = pd.read_csv(csv_file)

    for index, row in df_pages.iterrows():
        district = District.objects.get(district_id = row['district_id'])
        amphur = Amphur.objects.get(amphur_id = row['amphur_id'])
        province = Province.objects.get(province_id = row['province_id'])

        _, created = Page.objects.update_or_create(page_id = row['id'], title_th = row['title_th'], title_en = row['title_en'] \
            , lat = row['lat'], lng = row['lng'], rent_price = row['rent_price'], sale_price = row['sell_price'], area_id = row['area_id']\
            , post_type = row['post_type'], house_type = row['house_type'], landarea_total_sqw = row['landarea_total_sqw'] \
            , area_size_sqm = row['areasize_sqm'], room_type = row['room_type'], province = province, amphur = amphur, district = district)

    context = {}

    return render(request, template, context)

def upload_txns(request):
    template = 'upload_txns.html'

    # prompt = {
    #     'order': 'Order of the CSV should be \'district_id\', \district_th\', \'amphur_id\', \'amphur_th\' \
    #         , \'province_id\', and \'province_th\'.'
    # }

    prompt = {
        'order': 'Goddamn it.'
    }

    if request.method == 'GET':
        return render(request, template, prompt)

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        prompt_2 = {
            'order': 'This is not the CSV file.'
        }
        return render(request, template, prompt_2)

    df_txns = pd.read_csv(csv_file)

    # txns dataset preparation codes here.

    df_txns_true_columns = ['userID','page','event_strength']
    df_txns_columns = df_txns.columns.tolist()

    if df_txns_columns != df_txns_true_columns:
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
            if row['look_info'] != 0:
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

    # codes end here.

    for index, row in df_txns.iterrows():
        try:
            page = Page.objects.get(page_id = row['page'])
        except Page.DoesNotExist:
            continue

        _, created = Transaction.objects.update_or_create(userID = row['userID'], page = page, event_strength = row['event_strength'])

    context = {}

    return render(request, template, context)

def upload_places(request):
    template = 'upload_places.html'

    # prompt = {
    #     'order': 'Order of the CSV should be \'district_id\', \district_th\', \'amphur_id\', \'amphur_th\' \
    #         , \'province_id\', and \'province_th\'.'
    # }

    prompt = {
        'order': 'Goddamn son of a bitch.'
    }

    if request.method == 'GET':
        return render(request, template, prompt)

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        prompt_2 = {
            'order': 'This is not the CSV file.'
        }
        return render(request, template, prompt_2)

    df_places = pd.read_csv(csv_file)

    for index, row in df_places.iterrows():
        district = District.objects.get(district_id = row['district_id'])
        amphur = Amphur.objects.get(amphur_id = row['amphur_id'])
        province = Province.objects.get(province_id = row['province_id'])

        _, created = Place.objects.update_or_create(name_th = row['name_th'] \
            , latitude = row['latitude'], longitude = row['longitude'], poi_type = row['poi_type'], district = district \
            , amphur = amphur, province = province)

    context = {}

    return render(request, template, context)

def recommend_default(request, page_id):
    template = 'result.html'

    try:
        page = Page.objects.get(pk = page_id)
    except Page.DoesNotExist:
        return render(request, template, {})

    df_pages = pd.DataFrame(list(Page.objects.all().values()))
    df_txns = pd.DataFrame(list(Transaction.objects.all().values()))

    cb_model = CBRecommender(df_pages)
    cf_model = CFRecommender(df_txns, df_pages)

    hybrid_model = HybridRecommender(cb_model, cf_model, df_pages)

    df_recs = hybrid_model.recommend(page_id)
    # df_recs = hybrid_model.recommend_with_top_3cb(page_id)
    # df_recs = hybrid_model.recommend_without_weights(page_id)

    df_recs_html = df_recs[['page_id','title_th']].to_html()

    # return render(request, template, {'page': page , 'df_pages_html': df_pages_html})
    return render(request, template, {'page': page , 'df_recs_html': df_recs_html})

def recommend(request, page_id, setting_name):
    template = 'result.html'

    try:
        page = Page.objects.get(pk = page_id)
    except Page.DoesNotExist:
        return render(request, template, {})

    try:
        setting = Setting.objects.get(setting_name = setting_name)
    except Setting.DoesNotExist:
        return render(request, template, {})

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

    df_recs_html = df_recs[['page_id','title_th']].to_html()

    # return render(request, template, {'page': page , 'df_pages_html': df_pages_html})
    return render(request, template, {'page': page , 'df_recs_html': df_recs_html})