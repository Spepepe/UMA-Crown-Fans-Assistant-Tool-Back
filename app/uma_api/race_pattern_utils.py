"""レースパターン生成のユーティリティ関数"""

def get_race_grade(race, scenario_race=None):
    """レースの級を判定
    * @param race レースオブジェクト
    * @param scenario_race シナリオレースオブジェクト (オプション)
    * @return str レース級 ('junior', 'classic', 'senior')
    """
    if scenario_race:
        if scenario_race.senior_flag == 1:
            return 'senior'
        elif scenario_race.senior_flag == 0:
            return 'classic'
    
    if race.senior_flag == 1:
        return 'senior'
    elif race.classic_flag == 1:
        return 'classic'
    else:
        return 'junior'


def calculate_aptitude_scores(umamusume_data, available_surface_count, available_distance_count):
    """適性スコアを計算
    * @param umamusume_data ウマ娘データオブジェクト
    * @param available_surface_count 利用可能馬場数辞書
    * @param available_distance_count 利用可能距離数辞書
    * @return tuple 優先馬場と優先距離
    """
    aptitude_map = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': -1, 'F': -2, 'G': -3}
    
    turf_aptitude = aptitude_map.get(umamusume_data.turf_aptitude, 0)
    dirt_aptitude = aptitude_map.get(umamusume_data.dirt_aptitude, 0)
    sprint_aptitude = aptitude_map.get(umamusume_data.sprint_aptitude, 0)
    mile_aptitude = aptitude_map.get(umamusume_data.mile_aptitude, 0)
    classic_aptitude = aptitude_map.get(umamusume_data.classic_aptitude, 0)
    long_aptitude = aptitude_map.get(umamusume_data.long_distance_aptitude, 0)
    
    surface_score = {
        0: turf_aptitude * available_surface_count[0],
        1: dirt_aptitude * available_surface_count[1]
    }
    
    distance_score = {
        1: sprint_aptitude * available_distance_count[1],
        2: mile_aptitude * available_distance_count[2],
        3: classic_aptitude * available_distance_count[3],
        4: long_aptitude * available_distance_count[4]
    }
    
    preferred_surface = max(surface_score, key=surface_score.get) if any(surface_score.values()) else 0
    preferred_distance = max(distance_score, key=distance_score.get) if any(distance_score.values()) else 1
    
    return preferred_surface, preferred_distance


def is_larc_scenario_eligible(pattern):
    """ラークシナリオの条件をチェック
    * @param pattern レースパターン辞書
    * @return bool ラークシナリオに適格かどうか
    """
    classic_summer_autumn_races = any(
        r['race_name'] for r in pattern['classic']
        if (r['month'] == 7 and r['half'] == 0) or
           (r['month'] == 7 and r['half'] == 1) or
           (r['month'] == 8 and r['half'] == 0) or
           (r['month'] == 8 and r['half'] == 1) or
           (r['month'] == 9 and r['half'] == 0) or
           (r['month'] == 9 and r['half'] == 1) or
           (r['month'] == 10 and r['half'] == 0)
    )
    
    senior_late_races = any(
        r['race_name'] for r in pattern['senior']
        if (r['month'] >= 7) and not (r['month'] == 9 and r['half'] == 0)
    )
    
    return not classic_summer_autumn_races and not senior_late_races


def add_larc_scenario_races(pattern):
    """ラークシナリオのレースを追加
    * @param pattern レースパターン辞書
    * @return None
    """
    for idx, race_data in enumerate(pattern['classic']):
        if race_data['month'] == 5 and race_data['half'] == 1 and not race_data['race_name']:
            pattern['classic'][idx]['race_name'] = '日本ダービー'
        elif race_data['month'] == 9 and race_data['half'] == 0 and not race_data['race_name']:
            pattern['classic'][idx]['race_name'] = 'ニエル賞'
        elif race_data['month'] == 10 and race_data['half'] == 0 and not race_data['race_name']:
            pattern['classic'][idx]['race_name'] = '凱旋門賞'
    
    for idx, race_data in enumerate(pattern['senior']):
        if race_data['month'] == 6 and race_data['half'] == 1 and not race_data['race_name']:
            pattern['senior'][idx]['race_name'] = '宝塚記念'
        elif race_data['month'] == 9 and race_data['half'] == 0 and not race_data['race_name']:
            pattern['senior'][idx]['race_name'] = 'フォワ賞'


def add_scenario_races_to_pattern(pattern, scenario_races):
    """最新シナリオのレースを追加
    * @param pattern レースパターン辞書
    * @param scenario_races シナリオレースリスト
    * @return None
    """
    for scenario_race in scenario_races:
        race = scenario_race.race
        month = race.race_months
        half = race.half_flag
        grade_type = get_race_grade(race, scenario_race)
        
        for idx, race_data in enumerate(pattern[grade_type]):
            if race_data['month'] == month and race_data['half'] == half:
                pattern[grade_type][idx]['race_name'] = race.race_name
                break


def find_race_in_collections(race_data, conflicting_races, remaining_races):
    """複数のレースコレクションからレースを検索
    * @param race_data レースデータ辞書
    * @param conflicting_races 競合レースリスト
    * @param remaining_races 残レースリスト
    * @return Race|None 見つかったレースまたはNone
    """
    # conflicting_racesから検索
    for race in conflicting_races:
        if (race.race_name == race_data['race_name'] and 
            race.race_months == race_data['month'] and 
            race.half_flag == race_data['half']):
            return race
    
    # remaining_racesから検索
    for race in remaining_races:
        if (race.race_name == race_data['race_name'] and 
            race.race_months == race_data['month'] and 
            race.half_flag == race_data['half']):
            return race
    
    # 全レースから検索
    from .models import Race
    try:
        return Race.objects.get(
            race_name=race_data['race_name'],
            race_months=race_data['month'],
            half_flag=race_data['half']
        )
    except Race.DoesNotExist:
        return None


def collect_pattern_races(pattern, conflicting_races, remaining_races):
    """パターン内の全レースを収集
    * @param pattern レースパターン辞書
    * @param conflicting_races 競合レースリスト
    * @param remaining_races 残レースリスト
    * @return list パターン内の全レースリスト
    """
    all_races = []
    for grade_races in [pattern['junior'], pattern['classic'], pattern['senior']]:
        for race_data in grade_races:
            if race_data['race_name']:
                race = find_race_in_collections(race_data, conflicting_races, remaining_races)
                if race:
                    all_races.append(race)
    return all_races


def calculate_surface_and_distance(all_races):
    """馬場と距離を集計して最頻値を返す
    * @param all_races 全レースリスト
    * @return tuple (最頻馬場ID, 最頻距離ID, 馬場名, 距離名)
    """
    surface_count = {0: 0, 1: 0}
    distance_count = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for race in all_races:
        surface_count[race.race_state] += 1
        distance_count[race.distance] += 1
    
    most_common_surface = max(surface_count, key=surface_count.get) if any(surface_count.values()) else 0
    most_common_distance = max(distance_count, key=distance_count.get) if any(distance_count.values()) else 1
    
    surface_names = {0: '芝', 1: 'ダート'}
    distance_names = {1: '短距離', 2: 'マイル', 3: '中距離', 4: '長距離'}
    
    return (most_common_surface, most_common_distance, 
            surface_names[most_common_surface], distance_names[most_common_distance])


def add_junior_races(pattern, remaining_races, used_races, all_races):
    """ジュニア期の空きスロットにレースを追加
    * @param pattern レースパターン辞書
    * @param remaining_races 残レースリスト
    * @param used_races 使用済みレースIDセット
    * @param all_races 全レースリスト
    * @return None
    """
    for idx, race_data in enumerate(pattern['junior']):
        if not race_data['race_name']:
            month = race_data['month']
            half = race_data['half']
            
            for race in remaining_races:
                if (race.race_months == month and race.half_flag == half and 
                    race.junior_flag and race.race_id not in used_races):
                    pattern['junior'][idx]['race_name'] = race.race_name
                    used_races.add(race.race_id)
                    all_races.append(race)
                    break


def update_races_in_pattern(pattern, remaining_races, all_races):
    """パターンに追加されたレースをall_racesに反映
    * @param pattern レースパターン辞書
    * @param remaining_races 残レースリスト
    * @param all_races 全レースリスト
    * @return None
    """
    for grade_races in [pattern['junior'], pattern['classic'], pattern['senior']]:
        for race_data in grade_races:
            if race_data['race_name'] and not any(
                r.race_name == race_data['race_name'] and 
                r.race_months == race_data['month'] and 
                r.half_flag == race_data['half'] for r in all_races
            ):
                for race in remaining_races:
                    if (race.race_name == race_data['race_name'] and 
                        race.race_months == race_data['month'] and 
                        race.half_flag == race_data['half']):
                        all_races.append(race)
                        break