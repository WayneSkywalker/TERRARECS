import numpy as np
import pandas as pd

from .cb_model import CBRecommender
from .cf_model import CFRecommender

class HybridRecommender:
    
    MODEL_NAME = 'Hybrid'
    
    def __init__(self, cb_recs_model, cf_recs_model, df_pages, cb_ensemble_weight = 1.0, cf_ensemble_weight = 1.0):
        self.cb_recs_model = cb_recs_model
        self.cf_recs_model = cf_recs_model
        self.df_pages = df_pages
        self.cb_ensemble_weight = cb_ensemble_weight
        self.cf_ensemble_weight = cf_ensemble_weight
        
    def get_model_name(self):
        return self.MODEL_NAME
    
    def recommend(self, page_id, k = 10):
        df_cb_recs = self.cb_recs_model.recommend(page_id, k)
        df_cf_recs = self.cf_recs_model.recommend(page_id)
        
        df_hybrid_recs = df_cb_recs.merge(df_cf_recs, how = 'outer', left_on = 'id', right_on = 'id').fillna(0)
        
        # df_hybrid_recs['score'] = ((df_hybrid_recs['distance'] / df_cb_recs['distance'].mean()) * self.cb_ensemble_weight) + ((df_hybrid_recs['corr'] / df_cf_recs['corr'].mean()) * self.cf_ensemble_weight)
        df_hybrid_recs['score'] = (df_hybrid_recs['distance'] * self.cb_ensemble_weight) + (df_hybrid_recs['corr'] * self.cf_ensemble_weight)
        
        # df_hybrid_recs = df_hybrid_recs.sort_values('score', ascending = False).head(k)
        
        df_hybrid_recs = df_hybrid_recs.sort_values('id')
        df_hybrid_recs_list = df_hybrid_recs.id.tolist()
        df_hybrid_recs_score_list = df_hybrid_recs.score.tolist()
        del df_hybrid_recs
        
        df_recommendation = self.df_pages[self.df_pages.id.isin(df_hybrid_recs_list)]
        df_recommendation['score'] = df_hybrid_recs_score_list
        del df_hybrid_recs_list, df_hybrid_recs_score_list
        df_recommendation = df_recommendation.sort_values('score', ascending = False).reset_index(drop = True).head(k)
        
        # return df_hybrid_recs
        return df_recommendation
    
    def recommend_with_top_3cb(self, page_id, k = 10):
        df_cb_recs = self.cb_recs_model.recommend(page_id, k)
        df_cf_recs = self.cf_recs_model.recommend(page_id)
        
        df_recommendation = df_cb_recs.head(3)
        df_recommendation = df_recommendation.rename(columns = {"distance":"score"})
        
        df_cb_recs = df_cb_recs[~df_cb_recs['id'].isin(df_recommendation['id'].tolist())]
        
        df_hybrid_recs = df_cb_recs.merge(df_cf_recs, how = 'outer', left_on = 'id', right_on = 'id').fillna(0)
        
        # df_hybrid_recs['score'] = ((df_hybrid_recs['distance'] / df_cb_recs['distance'].mean()) * self.cb_ensemble_weight) + ((df_hybrid_recs['corr'] / df_cf_recs['corr'].mean()) * self.cf_ensemble_weight)
        df_hybrid_recs['score'] = (df_hybrid_recs['distance'] * self.cb_ensemble_weight) + (df_hybrid_recs['corr'] * self.cf_ensemble_weight)
        
        # df_hybrid_recs = df_hybrid_recs.sort_values('score', ascending = False).head(k)
        
        df_hybrid_recs = df_hybrid_recs.sort_values('id')
        df_hybrid_recs_list = df_hybrid_recs.id.tolist()
        df_hybrid_recs_score_list = df_hybrid_recs.score.tolist()
        del df_hybrid_recs
        
        temp = self.df_pages[self.df_pages.id.isin(df_hybrid_recs_list)]
        temp['score'] = df_hybrid_recs_score_list
        temp = temp.sort_values('score', ascending = False).reset_index(drop = True)
        del df_hybrid_recs_list, df_hybrid_recs_score_list
        
        df_recommendation = df_recommendation.append(temp, ignore_index = True).head(k)
        del temp
        
        return df_recommendation
    
    def recommend_without_weights(self, page_id, k = 10, n_cb = None, n_cf = None):
        
        if (n_cb is None) or (n_cf is None):
            n_cb = int(round(k / 2))
            n_cf = int(round(k / 2))
        
        df_cb_recs = self.cb_recs_model.recommend(page_id, k)
        df_cf_recs = self.cf_recs_model.recommend(page_id)
        
        df_cb_recs = df_cb_recs.drop(columns = ['distance']).head(n_cb)
        df_cf_recs = df_cf_recs.drop(columns = ['corr']).head(n_cf)
        
        df_recommendation = df_cb_recs.append(df_cf_recs, ignore_index = True)
        
        return df_recommendation

