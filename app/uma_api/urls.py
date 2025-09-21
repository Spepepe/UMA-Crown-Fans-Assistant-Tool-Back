from django.urls import path
from . import views, race_views

urlpatterns = [
    # 声優関連
    path('api/acter/list', views.acter_list, name='acter_list'),
    
    # ジュエル関連
    path('api/jewel/list', views.jewel_list, name='jewel_list'),
    path('api/jewel/regist', views.jewel_regist, name='jewel_regist'),
    
    # ライブ関連
    path('api/live/list', views.live_list, name='live_list'),
    path('api/live/umamusume', views.umamusume_list_by_live, name='umamusume_list_by_live'),
    
    # レース関連
    path('api/race/list', race_views.race_list, name='race_list'),
    path('api/race/regist-list', race_views.race_regist_list, name='race_regist_list'),
    path('api/race/remaining', race_views.remaining, name='remaining'),
    path('api/race/remaining-to-race', race_views.remaining_to_race, name='remaining_to_race'),
    path('api/race/run', race_views.race_run, name='race_run'),
    path('api/race/pattern', race_views.get_race_pattern, name='get_race_pattern'),
    path('api/race/register-pattern', views.register_race_pattern, name='register_race_pattern'),
    path('api/race/register-one', race_views.race_register_one, name='race_register_one'),
    
    # ウマ娘関連
    path('api/umamusume/regist-list', views.umamusume_regist_list, name='umamusume_regist_list'),
    path('api/umamusume/regist', views.umamusume_regist, name='umamusume_regist'),
    path('api/umamusume/user-regist', views.user_regist_umamusume, name='user_regist_umamusume'),
    path('api/umamusume/fan-up', views.fan_up, name='fan_up'),
    path('api/umamusume/list', views.umamusume_list, name='umamusume_list'),

    #　因子関連
    path('api/factor/calculate', views.calculate_parent_factors, name='calculate_parent_factors'),
    
    # ユーザー関連
    path('api/user/register', views.user_register, name='user_register'),
    path('api/user/login', views.user_login, name='user_login'),
    path('api/user/logout', views.user_logout, name='user_logout'),
    path('api/user/data', views.get_user_data, name='get_user_data'),
]