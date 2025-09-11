def fill_empty_slots_with_any_races(pattern, remaining_races, used_races):
    """残レースが0になるまで、空いているタイミングに任意のレースを追加
    * @param pattern レースパターン辞書
    * @param remaining_races 残レースのクエリセット
    * @param used_races 使用済みレースIDセット
    * @return None
    """
    grade_mappings = {
        'junior': (pattern['junior'], 1),
        'classic': (pattern['classic'], 2), 
        'senior': (pattern['senior'], 3)
    }
    
    # ラークシナリオの場合は制限を適用
    is_larc = pattern.get('scenario') == 'ラーク'
    
    # 残レースが0になるまでループ
    while True:
        added_any_race = False
        
        for grade_name, (grade_races, grade_num) in grade_mappings.items():
            for idx, race_data in enumerate(grade_races):
                if not race_data['race_name']:  # 空いているタイミング
                    month = race_data['month']
                    half = race_data['half']
                    
                    # ラークシナリオの制限チェック
                    if is_larc:
                        # クラシック7月前半～10月後半は固定レース以外入れない
                        if grade_name == 'classic' and ((month == 7) or (month == 8) or (month == 9) or (month == 10)):
                            continue
                        # シニア6月後半以降は固定レース以外入れない
                        if grade_name == 'senior' and ((month == 6 and half == 1) or (month >= 7)):
                            continue
                    
                    # 残レースから適合するレースを検索
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
                        
                        # 条件マッチング（馬場・距離は問わない）
                        if (race.race_months == month and 
                            race.half_flag == half and 
                            race_grade_match and
                            race.race_id not in used_races):
                            matching_races.append(race)
                    
                    # 最初に見つかったレースを追加
                    if matching_races:
                        selected_race = matching_races[0]
                        pattern[grade_name][idx]['race_name'] = selected_race.race_name
                        used_races.add(selected_race.race_id)
                        added_any_race = True
        
        # このループで何も追加されなかったら終了
        if not added_any_race:
            break


def fill_empty_slots_with_matching_races(pattern, remaining_races, target_surface, target_distance, used_races):
    """パターンの空いているタイミングに、指定した馬場・距離に合う残レースを追加
    * @param pattern レースパターン辞書
    * @param remaining_races 残レースのクエリセット
    * @param target_surface ターゲット馬場 (0:芝, 1:ダート)
    * @param target_distance ターゲット距離 (1:短距離, 2:マイル, 3:中距離, 4:長距離)
    * @param used_races 使用済みレースIDセット
    * @return None
    """
    grade_mappings = {
        'junior': (pattern['junior'], 1),
        'classic': (pattern['classic'], 2), 
        'senior': (pattern['senior'], 3)
    }
    
    # ラークシナリオの場合は制限を適用
    is_larc = pattern.get('scenario') == 'ラーク'
    
    for grade_name, (grade_races, grade_num) in grade_mappings.items():
        for idx, race_data in enumerate(grade_races):
            if not race_data['race_name']:  # 空いているタイミング
                month = race_data['month']
                half = race_data['half']
                
                # ラークシナリオの制限チェック
                if is_larc:
                    # クラシック7月前半～10月後半は固定レース以外入れない
                    if grade_name == 'classic' and ((month == 7) or (month == 8) or (month == 9) or (month == 10)):
                        continue
                    # シニア6月後半以降は固定レース以外入れない
                    if grade_name == 'senior' and ((month == 6 and half == 1) or (month >= 7)):
                        continue
                
                # 残レースから適合するレースを検索
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
                    
                    # 条件マッチング
                    if (race.race_months == month and 
                        race.half_flag == half and 
                        race_grade_match and
                        race.race_state == target_surface and 
                        race.distance == target_distance and
                        race.race_id not in used_races):
                        matching_races.append(race)
                
                # 最初に見つかったレースを追加
                if matching_races:
                    selected_race = matching_races[0]
                    pattern[grade_name][idx]['race_name'] = selected_race.race_name
                    used_races.add(selected_race.race_id)


def calculate_factor_composition(umamusume_data, pattern_races):
    """ウマ娘の適性とパターン内レースを元に因子構成を計算
    * @param umamusume_data ウマ娘データオブジェクト
    * @param pattern_races パターン内レースリスト
    * @return list 因子構成リスト (6個)
    """
    # 適性を数値化 (S=4, A=3, B=2, C=1, D=0, E=-1, F=-2, G=-3)
    aptitude_map = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': -1, 'F': -2, 'G': -3}
    
    turf_aptitude = aptitude_map.get(umamusume_data.turf_aptitude, 0)
    dirt_aptitude = aptitude_map.get(umamusume_data.dirt_aptitude, 0)
    sprint_aptitude = aptitude_map.get(umamusume_data.sprint_aptitude, 0)
    mile_aptitude = aptitude_map.get(umamusume_data.mile_aptitude, 0)
    classic_aptitude = aptitude_map.get(umamusume_data.classic_aptitude, 0)
    long_aptitude = aptitude_map.get(umamusume_data.long_distance_aptitude, 0)
    
    # パターン内レースの馬場・距離を集計
    surface_usage = {0: False, 1: False}  # 0: 芝, 1: ダート
    distance_usage = {1: False, 2: False, 3: False, 4: False}  # 1: 短距離, 2: マイル, 3: 中距離, 4: 長距離
    distance_count = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for race in pattern_races:
        surface_usage[race.race_state] = True
        distance_usage[race.distance] = True
        distance_count[race.distance] += 1
    
    # デバッグ: 適性と使用状況を確認

    
    factors = []
    
    # 6個すべて埋めるまでループ
    while len(factors) < 6:
        added = False
        
        # 馬場適性を優先
        for surface_state, surface_name in [(1, 'ダート'), (0, '芝')]:
            if surface_usage[surface_state]:
                current_aptitude = dirt_aptitude if surface_state == 1 else turf_aptitude
                current_count = factors.count(surface_name)
                # 適性別に必要な因子数を計算
                needed_factors = 0
                if current_aptitude == -3:  # G
                    needed_factors = 4
                elif current_aptitude == -2:  # F
                    needed_factors = 4
                elif current_aptitude == -1:  # E
                    needed_factors = 4
                elif current_aptitude == 0:  # D
                    needed_factors = 3
                elif current_aptitude == 1:  # C
                    needed_factors = 2
                elif current_aptitude == 2:  # B
                    needed_factors = 1
                
                if current_count < needed_factors:
                    factors.append(surface_name)
                    added = True
                    break
        
        if added:
            continue
        
        # 距離適性を低い順に優先
        distance_priorities = []
        if distance_usage[1]:  # 短距離
            distance_priorities.append((sprint_aptitude, '短距離', distance_count[1]))
        if distance_usage[2]:  # マイル
            distance_priorities.append((mile_aptitude, 'マイル', distance_count[2]))
        if distance_usage[3]:  # 中距離
            distance_priorities.append((classic_aptitude, '中距離', distance_count[3]))
        if distance_usage[4]:  # 長距離
            distance_priorities.append((long_aptitude, '長距離', distance_count[4]))
        
        # 適性の低い順にソート、同じ場合は使用回数の多い順
        distance_priorities.sort(key=lambda x: (x[0], -x[2]))
        
        for aptitude, factor_name, count in distance_priorities:
            current_count = factors.count(factor_name)
            # 適性別に必要な因子数を計算
            needed_factors = 0
            if aptitude == -3:  # G
                needed_factors = 4
            elif aptitude == -2:  # F
                needed_factors = 4
            elif aptitude == -1:  # E
                needed_factors = 4
            elif aptitude == 0:  # D
                needed_factors = 3
            elif aptitude == 1:  # C
                needed_factors = 2
            elif aptitude == 2:  # B
                needed_factors = 1
            
            if current_count < needed_factors:
                factors.append(factor_name)
                added = True
                break
        
        if not added:
            factors.append('自由')  # これ以上追加できない場合

    

    return factors[:6]


def get_race_pattern_data(count, user_id, umamusume_id):
    """レースパターンデータを生成するメイン関数
    * @param count 生成するパターン数
    * @param user_id ユーザーID
    * @param umamusume_id ウマ娘ID
    * @return list レースパターンリスト
    """
    from .models import RegistUmamusume, RegistUmamusumeRace, Race, ScenarioRace
    
    # ウマ娘情報を取得
    regist_umamusume = RegistUmamusume.objects.get(user_id=user_id, umamusume_id=umamusume_id)
    
    # 出走済みレースIDを取得
    regist_race_ids = RegistUmamusumeRace.objects.filter(
        user_id=user_id,
        umamusume_id=umamusume_id
    ).values_list('race_id', flat=True)
    
    # 残レースを取得
    remaining_races = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])
    
    # シナリオレースを取得
    scenario_races = ScenarioRace.objects.filter(umamusume_id=umamusume_id)
    
    # シナリオレースと被るタイミングの残レースを抽出
    scenario_race_ids = {scenario_race.race.race_id for scenario_race in scenario_races}
    conflicting_races = []
    added_race_ids = set()
    

    for scenario_race in scenario_races:
        race = scenario_race.race
        # シナリオレースの級を判定
        if scenario_race.senior_flag == 1:
            grade_type = 'senior'
        elif scenario_race.senior_flag == 0:
            grade_type = 'classic'
        else:
            # senior_flagがNoneの場合はraceテーブルのフラグを使用
            if race.senior_flag == 1:
                grade_type = 'senior'
            elif race.classic_flag == 1:
                grade_type = 'classic'
            else:
                grade_type = 'junior'
            
        for remaining_race in remaining_races:
            # 同じ月・前後半・級のレースのみ抽出
            # レースの級を判定（シニア優先）
            if remaining_race.senior_flag == 1:
                remaining_grade = 'senior'
            elif remaining_race.classic_flag == 1:
                remaining_grade = 'classic'
            else:
                remaining_grade = 'junior'
            
            same_grade = (grade_type == remaining_grade)
            
            if (remaining_race.race_months == race.race_months and 
                remaining_race.half_flag == race.half_flag and
                same_grade and
                remaining_race.race_id not in added_race_ids and
                remaining_race.race_id not in scenario_race_ids):

                conflicting_races.append(remaining_race)
                added_race_ids.add(remaining_race.race_id)
    
    # countの数だけ配列を作成
    patterns = []
    used_races = set(scenario_race_ids)  # シナリオレースIDを最初から格納
    
    # ニエル賞、フォワ賞、凱旋門賞、宝塚記念のIDも追加
    larc_race_names = ['ニエル賞', 'フォワ賞', '凱旋門賞', '宝塚記念']
    for race in remaining_races:
        if race.race_name in larc_race_names:
            used_races.add(race.race_id)
    
    larc_created = False  # ラークシナリオが作成済みかチェック
    
    for i in range(count):
        # パターンにシナリオ競合レースがあるかチェック
        has_conflicting_races = False
        
        # 事前にこのパターンで使用可能なレースの馬場・距離を集計
        available_surface_count = {0: 0, 1: 0}
        available_distance_count = {1: 0, 2: 0, 3: 0, 4: 0}
        
        for race in conflicting_races:
            if race.race_id not in used_races:
                available_surface_count[race.race_state] += 1
                available_distance_count[race.distance] += 1
        
        # ウマ娘の適性を考慮した優先馬場と距離を決定
        umamusume_data = regist_umamusume.umamusume
        
        # 馬場適性を数値化 (S=4, A=3, B=2, C=1, D=0, E=-1, F=-2, G=-3)
        aptitude_map = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': -1, 'F': -2, 'G': -3}
        turf_aptitude = aptitude_map.get(umamusume_data.turf_aptitude, 0)
        dirt_aptitude = aptitude_map.get(umamusume_data.dirt_aptitude, 0)
        
        # 距離適性を数値化
        sprint_aptitude = aptitude_map.get(umamusume_data.sprint_aptitude, 0)
        mile_aptitude = aptitude_map.get(umamusume_data.mile_aptitude, 0)
        classic_aptitude = aptitude_map.get(umamusume_data.classic_aptitude, 0)
        long_aptitude = aptitude_map.get(umamusume_data.long_distance_aptitude, 0)
        
        # 適性と利用可能レース数を組み合わせて優先度を決定
        surface_score = {
            0: turf_aptitude * available_surface_count[0],  # 芝
            1: dirt_aptitude * available_surface_count[1]   # ダート
        }
        
        distance_score = {
            1: sprint_aptitude * available_distance_count[1],   # スプリント
            2: mile_aptitude * available_distance_count[2],     # マイル
            3: classic_aptitude * available_distance_count[3],  # クラシック
            4: long_aptitude * available_distance_count[4]      # 長距離
        }
        
        # 最もスコアの高い馬場と距離を選択
        preferred_surface = max(surface_score, key=surface_score.get) if any(surface_score.values()) else 0
        preferred_distance = max(distance_score, key=distance_score.get) if any(distance_score.values()) else 1
        
        pattern = {
            "scenario": "メイクラ",  # 仮設定、後で更新
            "junior": [],
            "classic": [],
            "senior": []
        }
        
        # ジュニア 7月前半~12月後半 (12項目)
        for month in range(7, 13):
            for half in [0, 1]:
                matching_race = None
                
                for race in conflicting_races:
                    if (race.race_months == month and race.half_flag == half and 
                        race.junior_flag and race.race_id not in used_races):
                        matching_race = race
                        used_races.add(race.race_id)
                        break
                
                pattern["junior"].append({
                    "race_name": matching_race.race_name if matching_race else "",
                    "month": month,
                    "half": half
                })
        
        # クラシック 1月前半~12月後半 (24項目)
        for month in range(1, 13):
            for half in [0, 1]:
                matching_race = None
                candidate_races = []
                for race in conflicting_races:
                    if race.senior_flag == 1:
                        race_grade = 'senior'
                    elif race.classic_flag == 1:
                        race_grade = 'classic'
                    else:
                        race_grade = 'junior'
                    
                    if (race.race_months == month and race.half_flag == half and 
                        race_grade == 'classic' and race.race_id not in used_races):
                        candidate_races.append(race)
                
                if candidate_races:
                    def race_priority(race):
                        surface_match = 1 if race.race_state == preferred_surface else 0
                        distance_match = 1 if race.distance == preferred_distance else 0
                        return (-surface_match, -distance_match, race.race_state, race.distance)
                    
                    candidate_races.sort(key=race_priority)
                    matching_race = candidate_races[0]
                    used_races.add(matching_race.race_id)
                    has_conflicting_races = True
                
                pattern["classic"].append({
                    "race_name": matching_race.race_name if matching_race else "",
                    "month": month,
                    "half": half
                })
        
        # シニア 1月前半~12月後半 (24項目)
        for month in range(1, 13):
            for half in [0, 1]:
                matching_race = None
                candidate_races = []
                for race in conflicting_races:
                    if race.senior_flag == 1:
                        race_grade = 'senior'
                    elif race.classic_flag == 1:
                        race_grade = 'classic'
                    else:
                        race_grade = 'junior'
                    
                    if (race.race_months == month and race.half_flag == half and 
                        race_grade == 'senior' and race.race_id not in used_races):
                        candidate_races.append(race)
                
                if candidate_races:
                    def race_priority(race):
                        surface_match = 1 if race.race_state == preferred_surface else 0
                        distance_match = 1 if race.distance == preferred_distance else 0
                        return (-surface_match, -distance_match, race.race_state, race.distance)
                    
                    candidate_races.sort(key=race_priority)
                    matching_race = candidate_races[0]
                    used_races.add(matching_race.race_id)
                    has_conflicting_races = True
                
                pattern["senior"].append({
                    "race_name": matching_race.race_name if matching_race else "",
                    "month": month,
                    "half": half
                })
        
        # ラークシナリオのチェック
        is_larc_scenario = False
        
        # クラシック7月前半～10月前半に残レースがあるかチェック
        classic_summer_autumn_races = any(
            r['race_name'] for r in pattern['classic']
            if (r['month'] == 7 and r['half'] == 0) or  # 7月前半
               (r['month'] == 7 and r['half'] == 1) or  # 7月後半
               (r['month'] == 8 and r['half'] == 0) or  # 8月前半
               (r['month'] == 8 and r['half'] == 1) or  # 8月後半
               (r['month'] == 9 and r['half'] == 0) or  # 9月前半
               (r['month'] == 9 and r['half'] == 1) or  # 9月後半
               (r['month'] == 10 and r['half'] == 0)    # 10月前半
        )
        
        # シニア6月前半以降に残レースがあるかチェック
        senior_late_races = any(
            r['race_name'] for r in pattern['senior']
            if (r['month'] >= 7 or (r['month'] == 6 and r['half'] == 1))
        )

        # ラークシナリオのレースと被るレースがすでに適用されているか検証
        larc_scenario_race_names = any(
            r['race_name'] for r in pattern['classic']
            if (r['month'] == 5 and r['half'] == 1 and r['race_name'] != '日本ダービー')
        )
        
        # ラークシナリオの条件: 残レースがなく、まだ作成していない
        if (not classic_summer_autumn_races and 
            not senior_late_races and
            not larc_scenario_race_names and 
            not larc_created):
            is_larc_scenario = True
            larc_created = True
            
            # ラークシナリオのレースを追加（conflicting_racesで使用されていないタイミングのみ）
            for idx, race_data in enumerate(pattern['classic']):
                if race_data['month'] == 5 and race_data['half'] == 1 and not race_data['race_name']:  # 5月後半
                    pattern['classic'][idx]['race_name'] = '日本ダービー'
                elif race_data['month'] == 9 and race_data['half'] == 0 and not race_data['race_name']:  # 9月前半
                    pattern['classic'][idx]['race_name'] = 'ニエル賞'
                elif race_data['month'] == 10 and race_data['half'] == 0 and not race_data['race_name']:  # 10月前半
                    pattern['classic'][idx]['race_name'] = '凱旋門賞'
            
            for idx, race_data in enumerate(pattern['senior']):
                if race_data['month'] == 6 and race_data['half'] == 1 and not race_data['race_name']:  # 6月後半
                    pattern['senior'][idx]['race_name'] = '宝塚記念'
                elif race_data['month'] == 9 and race_data['half'] == 0 and not race_data['race_name']:  # 9月前半
                    pattern['senior'][idx]['race_name'] = 'フォワ賞'
                elif race_data['month'] == 10 and race_data['half'] == 0 and not race_data['race_name']:  # 10月前半
                    pattern['senior'][idx]['race_name'] = '凱旋門賞'
        
        # シナリオ名を決定
        if is_larc_scenario:
            pattern["scenario"] = "ラーク"
        elif has_conflicting_races:
            pattern["scenario"] = "メイクラ"
        else:
            pattern["scenario"] = "最新"
            # 最新シナリオの場合はシナリオレースをすべて配置
            for scenario_race in scenario_races:
                race = scenario_race.race
                month = race.race_months
                half = race.half_flag
                
                # シナリオレースの級を判定
                if scenario_race.senior_flag == 1:
                    grade_type = 'senior'
                elif scenario_race.senior_flag == 0:
                    grade_type = 'classic'
                else:
                    if race.senior_flag == 1:
                        grade_type = 'senior'
                    elif race.classic_flag == 1:
                        grade_type = 'classic'
                    else:
                        grade_type = 'junior'
                
                # 該当タイミングにシナリオレースを配置
                for idx, race_data in enumerate(pattern[grade_type]):
                    if race_data['month'] == month and race_data['half'] == half:
                        pattern[grade_type][idx]['race_name'] = race.race_name
                        break
        
        # パターン内のレースから馬場と距離を集計
        surface_count = {0: 0, 1: 0}  # 0: turf, 1: dirt
        distance_count = {1: 0, 2: 0, 3: 0, 4: 0}  # 1: sprint, 2: mile, 3: classic, 4: long
        
        # パターン内の全レースをチェック
        all_races_in_pattern = []
        for grade_races in [pattern['junior'], pattern['classic'], pattern['senior']]:
            for race_data in grade_races:
                if race_data['race_name']:  # レース名がある場合
                    race_found = False
                    # conflicting_racesから該当レースを検索
                    for race in conflicting_races:
                        if (race.race_name == race_data['race_name'] and 
                            race.race_months == race_data['month'] and 
                            race.half_flag == race_data['half']):
                            all_races_in_pattern.append(race)
                            race_found = True
                            break
                    # remaining_racesからも検索
                    if not race_found:
                        for race in remaining_races:
                            if (race.race_name == race_data['race_name'] and 
                                race.race_months == race_data['month'] and 
                                race.half_flag == race_data['half']):
                                all_races_in_pattern.append(race)
                                race_found = True
                                break
                    # 見つからない場合は全レースから検索（因子計算のため）
                    if not race_found:
                        from .models import Race
                        try:
                            race = Race.objects.get(
                                race_name=race_data['race_name'],
                                race_months=race_data['month'],
                                half_flag=race_data['half']
                            )
                            all_races_in_pattern.append(race)
                        except Race.DoesNotExist:
                            pass
        
        # 馬場と距離を集計
        for race in all_races_in_pattern:
            surface_count[race.race_state] += 1
            distance_count[race.distance] += 1
        
        # 最も多い馬場と距離を決定
        most_common_surface = max(surface_count, key=surface_count.get) if any(surface_count.values()) else 0
        most_common_distance = max(distance_count, key=distance_count.get) if any(distance_count.values()) else 1
        
        # 馬場と距離を文字列化してパターンに追加
        surface_names = {0: '芝', 1: 'ダート'}
        distance_names = {1: '短距離', 2: 'マイル', 3: '中距離', 4: '長距離'}
        
        pattern['surface'] = surface_names[most_common_surface]
        pattern['distance'] = distance_names[most_common_distance]
        

        
        # ジュニア期の空いているタイミングにジュニア級レースのみ追加
        for idx, race_data in enumerate(pattern['junior']):
            if not race_data['race_name']:
                month = race_data['month']
                half = race_data['half']
                
                # ジュニア級の残レースのみ検索
                for race in remaining_races:
                    if (race.race_months == month and race.half_flag == half and 
                        race.junior_flag and race.race_id not in used_races):
                        pattern['junior'][idx]['race_name'] = race.race_name
                        used_races.add(race.race_id)
                        all_races_in_pattern.append(race)
                        break
        
        # パターンの馬場・距離に合う残レースを空いているタイミングに追加
        fill_empty_slots_with_matching_races(pattern, remaining_races, most_common_surface, most_common_distance, used_races)
        
        # 残レースが0になるまで任意のレースで埋める
        fill_empty_slots_with_any_races(pattern, remaining_races, used_races)
        
        # 追加されたレースをall_races_in_patternに反映
        for grade_races in [pattern['junior'], pattern['classic'], pattern['senior']]:
            for race_data in grade_races:
                if race_data['race_name'] and not any(r.race_name == race_data['race_name'] and r.race_months == race_data['month'] and r.half_flag == race_data['half'] for r in all_races_in_pattern):
                    for race in remaining_races:
                        if (race.race_name == race_data['race_name'] and 
                            race.race_months == race_data['month'] and 
                            race.half_flag == race_data['half']):
                            all_races_in_pattern.append(race)
                            break
        
        # 最終的な馬場と距離を再集計
        surface_count = {0: 0, 1: 0}
        distance_count = {1: 0, 2: 0, 3: 0, 4: 0}
        
        for race in all_races_in_pattern:
            surface_count[race.race_state] += 1
            distance_count[race.distance] += 1
        
        # 最も多い馬場と距離を決定
        most_common_surface = max(surface_count, key=surface_count.get) if any(surface_count.values()) else 0
        most_common_distance = max(distance_count, key=distance_count.get) if any(distance_count.values()) else 1
        
        # 馬場と距離を文字列化してパターンに追加
        surface_names = {0: '芝', 1: 'ダート'}
        distance_names = {1: '短距離', 2: 'マイル', 3: '中距離', 4: '長距離'}
        
        pattern['surface'] = surface_names[most_common_surface]
        pattern['distance'] = distance_names[most_common_distance]
        

        
        # 因子構成を計算（最終的なall_races_in_patternを使用）
        pattern['factors'] = calculate_factor_composition(umamusume_data, all_races_in_pattern)
        
        # レース数を計算
        total_races = 0
        for grade_races in [pattern['junior'], pattern['classic'], pattern['senior']]:
            for race_data in grade_races:
                if race_data['race_name']:
                    total_races += 1
        pattern['totalRaces'] = total_races
        
        patterns.append(pattern)
    

    


    
    return {
        'patterns': patterns
    }