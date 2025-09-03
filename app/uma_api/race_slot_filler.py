"""レーススロット埋めモジュール"""

def is_larc_restricted(grade_name, month, half):
    """ラークシナリオの制限をチェック
    * @param grade_name レース級 ('junior', 'classic', 'senior')
    * @param month 月 (1-12)
    * @param half 前後半 (0:前半, 1:後半)
    * @return bool 制限されているかどうか
    """
    if grade_name == 'classic' and month in [7, 8, 9, 10]:
        return True
    if grade_name == 'senior' and ((month == 6 and half == 1) or (month >= 7)):
        return True
    return False


def find_matching_races(remaining_races, month, half, grade_num, used_races, target_surface=None, target_distance=None):
    """条件に合うレースを検索
    * @param remaining_races 残レースリスト
    * @param month 月 (1-12)
    * @param half 前後半 (0:前半, 1:後半)
    * @param grade_num レース級番号 (1:ジュニア, 2:クラシック, 3:シニア)
    * @param used_races 使用済みレースIDセット
    * @param target_surface ターゲット馬場 (オプション)
    * @param target_distance ターゲット距離 (オプション)
    * @return list マッチするレースリスト
    """
    matching_races = []
    for race in remaining_races:
        # レースの級を判定
        race_grade_match = False
        if grade_num == 1 and race.junior_flag:
            race_grade_match = True
        elif grade_num == 2 and race.classic_flag:
            race_grade_match = True
        elif grade_num == 3 and race.senior_flag:
            race_grade_match = True
        
        # 基本条件マッチング
        if (race.race_months == month and 
            race.half_flag == half and 
            race_grade_match and
            race.race_id not in used_races):
            
            # 馬場・距離の条件チェック
            if target_surface is not None and target_distance is not None:
                if race.race_state == target_surface and race.distance == target_distance:
                    matching_races.append(race)
            else:
                matching_races.append(race)
    
    return matching_races


def fill_empty_slots_with_matching_races(pattern, remaining_races, target_surface, target_distance, used_races):
    """パターンの空いているタイミングに、指定した馬場・距離に合う残レースを追加
    * @param pattern レースパターン辞書
    * @param remaining_races 残レースリスト
    * @param target_surface ターゲット馬場
    * @param target_distance ターゲット距離
    * @param used_races 使用済みレースIDセット
    * @return None
    """
    grade_mappings = {
        'junior': (pattern['junior'], 1),
        'classic': (pattern['classic'], 2), 
        'senior': (pattern['senior'], 3)
    }
    
    is_larc = pattern.get('scenario') == 'ラーク'
    
    for grade_name, (grade_races, grade_num) in grade_mappings.items():
        for idx, race_data in enumerate(grade_races):
            if not race_data['race_name']:
                month = race_data['month']
                half = race_data['half']
                
                if is_larc and is_larc_restricted(grade_name, month, half):
                    continue
                
                matching_races = find_matching_races(
                    remaining_races, month, half, grade_num, used_races, target_surface, target_distance
                )
                
                if matching_races:
                    selected_race = matching_races[0]
                    pattern[grade_name][idx]['race_name'] = selected_race.race_name
                    used_races.add(selected_race.race_id)


def fill_empty_slots_with_any_races(pattern, remaining_races, used_races):
    """残レースが0になるまで、空いているタイミングに任意のレースを追加
    * @param pattern レースパターン辞書
    * @param remaining_races 残レースリスト
    * @param used_races 使用済みレースIDセット
    * @return None
    """
    grade_mappings = {
        'junior': (pattern['junior'], 1),
        'classic': (pattern['classic'], 2), 
        'senior': (pattern['senior'], 3)
    }
    
    is_larc = pattern.get('scenario') == 'ラーク'
    
    while True:
        added_any_race = False
        
        for grade_name, (grade_races, grade_num) in grade_mappings.items():
            for idx, race_data in enumerate(grade_races):
                if not race_data['race_name']:
                    month = race_data['month']
                    half = race_data['half']
                    
                    if is_larc and is_larc_restricted(grade_name, month, half):
                        continue
                    
                    matching_races = find_matching_races(
                        remaining_races, month, half, grade_num, used_races
                    )
                    
                    if matching_races:
                        selected_race = matching_races[0]
                        pattern[grade_name][idx]['race_name'] = selected_race.race_name
                        used_races.add(selected_race.race_id)
                        added_any_race = True
        
        if not added_any_race:
            break