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
                    
                    # 見つかったレースを優先順位付けして追加
                    if matching_races:
                        strategy = pattern.get('strategy')

                        def get_race_priority(race):
                            """レースの優先度を計算する。タプルの先頭が優先される。"""
                            match_score = 0
                            if strategy:
                                strategy_keys = strategy.keys()
                                distance_map = {1: '短距離', 2: 'マイル', 3: '中距離', 4: '長距離'}
                                race_distance_name = distance_map.get(race.distance)

                                is_dirt_strategy = 'ダート' in strategy_keys
                                is_distance_strategy = race_distance_name in strategy_keys

                                if is_dirt_strategy and race.race_state == 1 and is_distance_strategy:
                                    match_score = 2 # 両方一致
                                elif (is_dirt_strategy and race.race_state == 1) or is_distance_strategy:
                                    match_score = 1 # 片方一致

                            # 優先度: 戦略との一致度 > G1 > G2 > G3
                            return (-match_score, race.race_rank)

                        matching_races.sort(key=get_race_priority)

                        selected_race = matching_races[0]
                        pattern[grade_name][idx]['race_name'] = selected_race.race_name
                        pattern[grade_name][idx]['race_id'] = selected_race.race_id
                        used_races.add(selected_race.race_id)
                        added_any_race = True
        
        # このループで何も追加されなかったら終了
        if not added_any_race:
            break

def calculate_factor_composition(umamusume_data, pattern_races, reinforcement_strategy=None, is_larc=False):
    """ウマ娘の適性とパターン内レースを元に因子構成を計算
    * @param umamusume_data ウマ娘データオブジェクト
    * @param pattern_races パターン内レースリスト
    * @param reinforcement_strategy 補強戦略辞書 (例: {'ダート': 3, 'マイル': 3})
    * @param is_larc ラークシナリオかどうか
    * @return list 因子構成リスト (6個)
    """
    factors = []
    aptitude_map = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': -1, 'F': -2, 'G': -3}
    
    current_strategy = reinforcement_strategy
    # ラークシナリオの場合、戦略から「芝」と「中距離」を除外
    if is_larc and current_strategy:
        current_strategy = {k: v for k, v in current_strategy.items() if k not in ['芝', '中距離']}

        # G適性の因子が残っている場合、個数を4に増やす
        aptitudes_data = {
            '芝': umamusume_data.turf_aptitude, 'ダート': umamusume_data.dirt_aptitude,
            '短距離': umamusume_data.sprint_aptitude, 'マイル': umamusume_data.mile_aptitude,
            '中距離': umamusume_data.classic_aptitude, '長距離': umamusume_data.long_distance_aptitude,
        }
        
        temp_strategy = {}
        total_factors = 0
        for factor, num in current_strategy.items():
            aptitude_char = aptitudes_data.get(factor, 'A')
            new_num = num
            if aptitude_map.get(aptitude_char, 0) <= -3:
                new_num = 3
            
            # 合計が6を超えないように調整
            if total_factors + new_num <= 6:
                temp_strategy[factor] = new_num
                total_factors += new_num
            elif total_factors + num <= 6:
                temp_strategy[factor] = num
                total_factors += num
        current_strategy = temp_strategy

        if not current_strategy:
            current_strategy = None # 戦略が空になったら通常計算

    # 戦略が指定されている場合は、それを最優先で適用
    if current_strategy:
        for factor, num in current_strategy.items():
            factors.extend([factor] * num)
        # 残りを「自由」で埋める
        while len(factors) < 6:
            factors.append('自由')
        return factors[:6]

    # --- 以下は戦略が指定されていない場合の既存ロジック ---
    # 適性を数値化 (S=4, A=3, B=2, C=1, D=0, E=-1, F=-2, G=-3)
    
    turf_aptitude = aptitude_map.get(umamusume_data.turf_aptitude, 0)
    dirt_aptitude = aptitude_map.get(umamusume_data.dirt_aptitude, 0)
    sprint_aptitude = aptitude_map.get(umamusume_data.sprint_aptitude, 0)
    mile_aptitude = aptitude_map.get(umamusume_data.mile_aptitude, 0)
    classic_aptitude = aptitude_map.get(umamusume_data.classic_aptitude, 0)
    long_aptitude = aptitude_map.get(umamusume_data.long_distance_aptitude, 0)
    
    # ラークシナリオの場合、芝と中距離適性をAとして扱う
    if is_larc:
        turf_aptitude = 3  # 'A'
        classic_aptitude = 3  # 'A'
    
    # パターン内レースの馬場・距離を集計
    surface_usage = {0: False, 1: False}  # 0: 芝, 1: ダート
    distance_usage = {1: False, 2: False, 3: False, 4: False}  # 1: 短距離, 2: マイル, 3: 中距離, 4: 長距離
    distance_count = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for race in pattern_races:
        surface_usage[race.race_state] = True
        distance_usage[race.distance] = True
        distance_count[race.distance] += 1
    
    # 補強対象の適性をリストアップ (優先度順)
    aptitudes_to_fix = []
    # 距離
    if distance_usage[4] and long_aptitude <= 1: aptitudes_to_fix.append((long_aptitude, '長距離'))
    if distance_usage[3] and classic_aptitude <= 1: aptitudes_to_fix.append((classic_aptitude, '中距離'))
    if distance_usage[2] and mile_aptitude <= 1: aptitudes_to_fix.append((mile_aptitude, 'マイル'))
    if distance_usage[1] and sprint_aptitude <= 1: aptitudes_to_fix.append((sprint_aptitude, '短距離'))
    # 馬場
    if surface_usage[1] and dirt_aptitude <= 1: aptitudes_to_fix.append((dirt_aptitude, 'ダート'))
    if surface_usage[0] and turf_aptitude <= 1: aptitudes_to_fix.append((turf_aptitude, '芝'))

    # 適性が低い順でソート (同じ適性値なら上記の優先度順が維持される)
    aptitudes_to_fix.sort(key=lambda x: x[0])

    # G,F,E適性の数を数える
    low_apt_to_fix = [name for apt, name in aptitudes_to_fix if apt <= -1]

    for aptitude, factor_name in aptitudes_to_fix:
        if len(factors) >= 6: 
            break

        # 既に因子が追加されている場合は、次の候補へ
        if any(f == factor_name for f in factors):
            continue

        needed_factors = 0
        if aptitude <= -1:  # G, F, E
            # 補強対象の低適性が複数ある場合は3、1つだけなら4を割り当てる
            if len(low_apt_to_fix) >= 2:
                needed_factors = 3
            else: # 1つだけ
                needed_factors = 4
        elif aptitude == 0:  # D
            needed_factors = 3
        elif aptitude == 1:  # C
            needed_factors = 2
        
        # 残りの因子スロットが足りる場合のみ、まとめて追加
        if len(factors) + needed_factors <= 6:
            factors.extend([factor_name] * needed_factors)

    # 残りを「自由」で埋める
    while len(factors) < 6:
        factors.append('自由')

    return factors[:6]


from itertools import combinations

def _get_reinforcement_strategies(umamusume_data):
    """ウマ娘の低い適性から、因子補強の戦略パターンを複数生成する"""
    aptitude_map = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': -1, 'F': -2, 'G': -3}
    
    aptitudes = {
        '芝': aptitude_map.get(umamusume_data.turf_aptitude, 0),
        'ダート': aptitude_map.get(umamusume_data.dirt_aptitude, 0),
        '短距離': aptitude_map.get(umamusume_data.sprint_aptitude, 0),
        'マイル': aptitude_map.get(umamusume_data.mile_aptitude, 0),
        '中距離': aptitude_map.get(umamusume_data.classic_aptitude, 0),
        '長距離': aptitude_map.get(umamusume_data.long_distance_aptitude, 0),
    }

    # C以下の適性を補強対象候補とする
    low_aptitudes = [name for name, value in aptitudes.items() if value <= 1]
    
    strategies = []
    # 候補から2つ選ぶ組み合わせ（因子3個ずつ）
    if len(low_aptitudes) >= 2:
        for combo in combinations(low_aptitudes, 2):
            strategies.append({combo[0]: 3, combo[1]: 3})

    # If specific strategies were generated, use them.
    # Otherwise, fall back to a single 'no strategy' run.
    if not strategies:
        return [None]
    return strategies

def _filter_races_by_strategy(races, strategy, umamusume_data):
    """戦略に基づき、適性が低く、かつ補強対象外のレースを除外する"""
    if not strategy:
        return races

    aptitude_map = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': -1, 'F': -2, 'G': -3}
    aptitudes = {
        '芝': aptitude_map.get(umamusume_data.turf_aptitude, 0),
        'ダート': aptitude_map.get(umamusume_data.dirt_aptitude, 0),
        '短距離': aptitude_map.get(umamusume_data.sprint_aptitude, 0),
        'マイル': aptitude_map.get(umamusume_data.mile_aptitude, 0),
        '中距離': aptitude_map.get(umamusume_data.classic_aptitude, 0),
        '長距離': aptitude_map.get(umamusume_data.long_distance_aptitude, 0),
    }

    # D以下の適性のうち、今回の戦略でサポートしないものを特定
    unsupported_low_aptitudes = {
        name for name, value in aptitudes.items() 
        if value <= 0 and name not in strategy
    }

    if not unsupported_low_aptitudes:
        return races

    distance_map = {1: '短距離', 2: 'マイル', 3: '中距離', 4: '長距離'}
    
    def is_race_supported(race):
        """このレースが現在の戦略でサポートされているかを判定する"""
        # 戦略でサポート外の芝レースは除外
        if '芝' in unsupported_low_aptitudes and race.race_state == 0:
            return False
        # 戦略でサポート外のダートレースは除外
        if 'ダート' in unsupported_low_aptitudes and race.race_state == 1:
            return False
        
        # 戦略でサポート外の距離のレースは除外
        race_distance_name = distance_map.get(race.distance)
        if race_distance_name in unsupported_low_aptitudes:
            return False
            
        return True

    return [race for race in races if is_race_supported(race)]

def _get_race_grade(race, scenario_info=None):
    """レースの級（'junior', 'classic', 'senior'）を判定する"""
    # ScenarioRaceの情報があれば、それを最優先する
    if scenario_info:
        # シニア級の目標レースとして指定されているか
        if scenario_info.senior_flag == 1:
            return 'senior'
        # シニア級でない場合、クラシック級かジュニア級かを判定する
        # ジュニア級でしか開催されないレースか？
        if race.junior_flag == 1 and not race.classic_flag:
            return 'junior'

        if race.senior_flag == 1:
            return 'senior'
        
        # 上記以外はクラシック級の目標とみなす
        return 'classic'

    # ScenarioRaceの情報がない場合（通常の残レースなど）、Raceオブジェクトのフラグで判定
    # シニア級でも開催されるならシニアを優先
    if race.senior_flag == 1:
        return 'senior'
    if race.classic_flag == 1:
        return 'classic'
    return 'junior'


def _extract_conflicting_races(scenario_races, remaining_races):
    """シナリオレースとタイミングが被るG1/G2/G3レースを抽出する"""
    scenario_race_ids = {sr.race.race_id for sr in scenario_races}
    conflicting_races = []
    added_race_ids = set()

    for scenario_race in scenario_races:
        race = scenario_race.race
        grade_type = _get_race_grade(race, scenario_race)
            
        for rem_race in remaining_races:
            rem_grade = _get_race_grade(rem_race)
            
            if (rem_race.race_months == race.race_months and 
                rem_race.half_flag == race.half_flag and
                grade_type == rem_grade and
                rem_race.race_id not in added_race_ids and
                rem_race.race_id not in scenario_race_ids):

                conflicting_races.append(rem_race)
                added_race_ids.add(rem_race.race_id)
    return conflicting_races, scenario_race_ids


def _initialize_used_races(scenario_race_ids, remaining_races):
    """使用済みレースIDセットを初期化する"""
    used_races = set(scenario_race_ids)
    
    larc_race_names = {'ニエル賞', 'フォワ賞', '凱旋門賞', '宝塚記念'}
    for race in remaining_races:
        if race.race_name in larc_race_names:
            used_races.add(race.race_id)
    return used_races


def _determine_preferred_conditions(umamusume_data, available_races):
    """ウマ娘の適性と利用可能レースから優先馬場・距離を決定する"""
    available_surface_count = {0: 0, 1: 0}
    available_distance_count = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for race in available_races:
        available_surface_count[race.race_state] += 1
        available_distance_count[race.distance] += 1
        
    aptitude_map = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': -1, 'F': -2, 'G': -3}
    def get_aptitude(apt_str):
        return aptitude_map.get(apt_str, 0)

    surface_score = {
        0: get_aptitude(umamusume_data.turf_aptitude) * available_surface_count[0],
        1: get_aptitude(umamusume_data.dirt_aptitude) * available_surface_count[1]
    }
    distance_score = {
        1: get_aptitude(umamusume_data.sprint_aptitude) * available_distance_count[1],
        2: get_aptitude(umamusume_data.mile_aptitude) * available_distance_count[2],
        3: get_aptitude(umamusume_data.classic_aptitude) * available_distance_count[3],
        4: get_aptitude(umamusume_data.long_distance_aptitude) * available_distance_count[4]
    }
    
    preferred_surface = max(surface_score, key=surface_score.get) if any(surface_score.values()) else 0
    preferred_distance = max(distance_score, key=distance_score.get) if any(distance_score.values()) else 1
    
    return preferred_surface, preferred_distance


def _create_base_pattern(conflicting_races, used_races, preferred_surface, preferred_distance):
    """競合レースを元に基本となるレースパターンを作成する"""
    pattern = {"junior": [], "classic": [], "senior": []}
    has_conflicting_races = False

    def race_priority(race):
        surface_match = 1 if race.race_state == preferred_surface else 0
        distance_match = 1 if race.distance == preferred_distance else 0
        return (-surface_match, -distance_match, race.race_state, race.distance)

    for grade_name, month_range in [('junior', range(7, 13)), ('classic', range(1, 13)), ('senior', range(1, 13))]:
        for month in month_range:
            for half in [0, 1]:
                candidate_races = [
                    race for race in conflicting_races
                    if (race.race_months == month and race.half_flag == half and
                        _get_race_grade(race) == grade_name and race.race_id not in used_races)
                ]
                
                matching_race = None
                if candidate_races:
                    if grade_name in ['classic', 'senior']:
                        candidate_races.sort(key=race_priority)
                    
                    matching_race = candidate_races[0]
                    used_races.add(matching_race.race_id)
                    has_conflicting_races = True

                pattern[grade_name].append({
                    "race_name": matching_race.race_name if matching_race else "",
                    "race_id": matching_race.race_id if matching_race else None,
                    "month": month, "half": half
                })
    return pattern, has_conflicting_races


def _apply_larc_scenario_if_applicable(pattern, larc_created, race_map, used_races , scenario_races):
    """ラークシナリオの条件をチェックし、適用可能であればパターンを更新する"""
    if larc_created:
        return False, True, used_races


    classic_summer_autumn_races = any(
        r['race_name'] for r in pattern['classic']
        if (r['month'] in [7, 8, 9]) or (r['month'] == 10 and r['half'] == 0)
    )
    senior_late_races = any(
        r['race_name'] for r in pattern['senior']
        if r['month'] >= 7 or (r['month'] == 6 and r['half'] == 1)
    )
    larc_conflict = any(
        r['race_name'] and r['race_name'] != '日本ダービー' for r in pattern['classic']
        if r['month'] == 5 and r['half'] == 1
    )
    
    is_larc_scenario = not (classic_summer_autumn_races or senior_late_races or larc_conflict)

    if is_larc_scenario:
        larc_races = {
            'classic': [(5, 1, '日本ダービー'), (9, 0, 'ニエル賞'), (10, 0, '凱旋門賞')],
            'senior': [(6, 1, '宝塚記念'), (9, 0, 'フォワ賞'), (10, 0, '凱旋門賞')]
        }
        for grade, races in larc_races.items():
            for idx, race_data in enumerate(pattern[grade]):
                for month, half, name in races:
                    if race_data['month'] == month and race_data['half'] == half and not race_data['race_name']:
                        race_id = race_map.get((name, month, half))
                        # race_idが見つかった場合のみパターンとused_racesを更新
                        if race_id:
                            pattern[grade][idx]['race_name'] = name
                            pattern[grade][idx]['race_id'] = race_id
                            used_races.add(race_id)
                        break
        return True, True, used_races
    return False, False, used_races


def _determine_and_apply_scenario(pattern, is_larc, has_conflicts, is_scenario_pattern=False):
    """シナリオ名を決定する"""
    if is_scenario_pattern:
        pattern["scenario"] = "伝説"
    elif is_larc:
        pattern["scenario"] = "ラーク"
    elif has_conflicts:
        pattern["scenario"] = "メイクラ"
    else:
        pattern["scenario"] = "メイクラ"


def _get_all_races_in_pattern(pattern, all_g_races):
    """パターン内のレース名からRaceオブジェクトのリストを取得する"""
    races_in_pattern = []
    race_id_map = {r.race_id: r for r in all_g_races}

    for grade_races in [pattern['junior'], pattern['classic'], pattern['senior']]:
        for race_data in grade_races:
            race_id = race_data.get('race_id')
            if race_id:
                race_obj = race_id_map.get(race_id)
                if race_obj:
                    races_in_pattern.append(race_obj)
    return races_in_pattern


def _calculate_and_set_main_conditions(pattern, races_in_pattern):
    """パターン内のレースを集計し、主要な馬場・距離を決定して設定する"""
    surface_count = {0: 0, 1: 0}
    distance_count = {1: 0, 2: 0, 3: 0, 4: 0}
    for race in races_in_pattern:
        surface_count[race.race_state] += 1
        distance_count[race.distance] += 1
    
    most_common_surface = max(surface_count, key=surface_count.get) if any(surface_count.values()) else 0
    most_common_distance = max(distance_count, key=distance_count.get) if any(distance_count.values()) else 1
    
    surface_names = {0: '芝', 1: 'ダート'}
    distance_names = {1: '短距離', 2: 'マイル', 3: '中距離', 4: '長距離'}
    pattern['surface'] = surface_names[most_common_surface]
    pattern['distance'] = distance_names[most_common_distance]
    return most_common_surface, most_common_distance


def _fill_junior_slots(pattern, remaining_races, used_races):
    """ジュニア期の空きスロットにジュニア級レースを追加する"""
    for idx, race_data in enumerate(pattern['junior']):
        if not race_data['race_name']:
            for race in remaining_races:
                if (race.race_months == race_data['month'] and race.half_flag == race_data['half'] and
                    race.junior_flag and race.race_id not in used_races):
                    pattern['junior'][idx]['race_name'] = race.race_name
                    pattern['junior'][idx]['race_id'] = race.race_id
                    used_races.add(race.race_id)
                    break

def get_race_pattern_data(count, user_id, umamusume_id):
    """レースパターンデータを生成するメイン関数
    * @param count 生成するパターン数
    * @param user_id ユーザーID
    * @param umamusume_id ウマ娘ID
    * @return list レースパターンリスト
    """
    from .models import RegistUmamusume, RegistUmamusumeRace, Race, ScenarioRace

    # --- 1. データ取得 ---
    regist_umamusume = RegistUmamusume.objects.get(user_id=user_id, umamusume_id=umamusume_id)
    umamusume_data = regist_umamusume.umamusume
    regist_race_ids = RegistUmamusumeRace.objects.filter(
        user_id=user_id, umamusume_id=umamusume_id
    ).values_list('race_id', flat=True)
    remaining_races_qs = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])
    scenario_races = ScenarioRace.objects.filter(umamusume_id=umamusume_id)
    all_g_races = list(Race.objects.filter(race_rank__in=[1, 2, 3]))

    # --- 2. 事前準備 ---
    # 2.1 補強戦略リストを作成
    strategies = _get_reinforcement_strategies(umamusume_data)
    
    # 2.2 シナリオレースIDを取得
    _, scenario_race_ids = _extract_conflicting_races(scenario_races, remaining_races_qs)
    
    # 2.3 レース名からIDを引くためのマップを作成
    race_map = {(r.race_name, r.race_months, r.half_flag): r.race_id for r in all_g_races}
    
    # --- 3. パターン生成ループ ---
    patterns = []
    
    # ラーク主要レース（凱旋門賞、ニエル賞、フォワ賞）が一つも残っていない場合、
    # ラークパターンは作成済みか作成不可能とみなし、フラグをTrueに設定する
    larc_key_race_names = {'凱旋門賞', 'ニエル賞', 'フォワ賞'}
    has_remaining_larc_races = remaining_races_qs.filter(race_name__in=larc_key_race_names).exists()
    larc_created = not has_remaining_larc_races
    
    # 全パターンで共有する使用済みレースIDセット
    # ループの外で一度だけ初期化し、パターン間で重複が起きないようにする
    used_races = _initialize_used_races(scenario_race_ids, remaining_races_qs)

    pattern_index = 0
    # 残りレースがなくなるか、新しいレースを配置できなくなるまでパターンを生成し続ける
    while True:
        # ループ開始前の使用済みレース数を記録
        races_used_before_iteration = len(used_races)

        # 3.0. このパターン用の準備
        strategy = strategies[pattern_index % len(strategies)]

        # 戦略に基づいて、このパターンで使用するレースをフィルタリング
        remaining_races = _filter_races_by_strategy(list(remaining_races_qs), strategy, umamusume_data)
        
        # フィルタリング後のレースリストから競合レースを再抽出
        conflicting_races, _ = _extract_conflicting_races(scenario_races, remaining_races)

        # 3.1. 優先馬場・距離の決定
        available_conflicts = [r for r in conflicting_races if r.race_id not in used_races]
        preferred_surface, preferred_distance = _determine_preferred_conditions(umamusume_data, available_conflicts)

        # 3.2. 基本パターンの作成
        pattern, has_conflicts = _create_base_pattern(conflicting_races, used_races, preferred_surface, preferred_distance)
        pattern['strategy'] = strategy # 表示やデバッグ用に戦略を記録

        # 3.3. ラークシナリオ判定 & 適用
        is_larc, larc_created, used_races = _apply_larc_scenario_if_applicable(pattern, larc_created, race_map, used_races , scenario_races)
        # 3.4. シナリオ名決定 & 適用
        _determine_and_apply_scenario(pattern, is_larc, has_conflicts)

        # 3.5. 空きスロットの充填 (1/3): 主要な馬場・距離の計算
        races_in_pattern = _get_all_races_in_pattern(pattern, all_g_races)
        most_common_surface, most_common_distance = _calculate_and_set_main_conditions(pattern, races_in_pattern)

        # 3.6. 空きスロットの充填 (2/3): 各種ルールに基づいて埋める
        _fill_junior_slots(pattern, remaining_races, used_races)
        fill_empty_slots_with_any_races(pattern, remaining_races, used_races)
        
        # 3.7. 空きスロットの充填 (3/3): 最終的なレースリストと主要な馬場・距離の再計算
        final_races_in_pattern = _get_all_races_in_pattern(pattern, all_g_races)
        _calculate_and_set_main_conditions(pattern, final_races_in_pattern)
        
    
        # 3.8. 因子構成と合計レース数を計算
        pattern['factors'] = calculate_factor_composition(umamusume_data, final_races_in_pattern, reinforcement_strategy=strategy, is_larc=is_larc)
        pattern['totalRaces'] = len(final_races_in_pattern)

        # このイテレーションで新しいレースが追加されたかチェック
        if len(used_races) > races_used_before_iteration or is_larc:
            patterns.append(pattern)
        else:
            # 新しいレースが一つも追加されなかった場合、これ以上パターンは作れないのでループを抜ける
            break

        pattern_index += 1
        # 安全装置として、生成されるパターン数に上限を設ける
        if pattern_index >= 20:
            break
    
    # --- 4. シナリオレースの取り扱い ---
    found_non_conflicting_pattern = False

    if scenario_races:
        # 4.1 シナリオレースとタイミングが被らないパターン(A)を探す
        for i, pattern in enumerate(patterns):
            is_conflicting = any(
                race_data['race_name']
                for sr in scenario_races
                for race_data in pattern[_get_race_grade(sr.race, sr)]
                if race_data['month'] == sr.race.race_months and race_data['half'] == sr.race.half_flag
            )

            if not is_conflicting:
                # 4.2 (A)にシナリオレースをマージし、シナリオを「伝説」として扱う
                for sr in scenario_races:
                    race = sr.race
                    grade = _get_race_grade(race, sr)
                    for race_data in patterns[i][grade]:
                        if race_data['month'] == race.race_months and race_data['half'] == race.half_flag and not race_data['race_name']:
                            race_data['race_name'] = race.race_name
                            race_data['race_id'] = race.race_id
                            break
                
                patterns[i]['scenario'] = "伝説"
                patterns[i]['strategy'] = None
                
                final_races_in_pattern = _get_all_races_in_pattern(patterns[i], all_g_races)
                _calculate_and_set_main_conditions(patterns[i], final_races_in_pattern)
                patterns[i]['factors'] = calculate_factor_composition(umamusume_data, final_races_in_pattern)
                patterns[i]['totalRaces'] = len(final_races_in_pattern)
                
                found_non_conflicting_pattern = True

    # 4.3 (A)がなければ、従来通り最後にシナリオレース用のパターンを追加
    if scenario_races and not found_non_conflicting_pattern:
        scenario_pattern = {"scenario": "伝説", "strategy": None, "junior": [], "classic": [], "senior": []}
        for grade_name, month_range in [('junior', range(7, 13)), ('classic', range(1, 13)), ('senior', range(1, 13))]:
            for month in month_range:
                for half in [0, 1]:
                    scenario_pattern[grade_name].append({"race_name": "", "race_id": None, "month": month, "half": half})

        for sr in scenario_races:
            race = sr.race
            grade = _get_race_grade(race, sr)
            for race_data in scenario_pattern[grade]:
                if race_data['month'] == race.race_months and race_data['half'] == race.half_flag:
                    race_data['race_name'] = race.race_name
                    race_data['race_id'] = race.race_id
                    break
        
        fill_empty_slots_with_any_races(scenario_pattern, list(remaining_races_qs), used_races)

        final_races_in_pattern = _get_all_races_in_pattern(scenario_pattern, all_g_races)
        _calculate_and_set_main_conditions(scenario_pattern, final_races_in_pattern)
        scenario_pattern['factors'] = calculate_factor_composition(umamusume_data, final_races_in_pattern)
        scenario_pattern['totalRaces'] = len(final_races_in_pattern)
        patterns.append(scenario_pattern)

    return {
        'patterns': patterns
    }
