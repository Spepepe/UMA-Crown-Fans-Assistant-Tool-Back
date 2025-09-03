"""因子計算モジュール"""

def calculate_needed_factors(aptitude):
    """適性値から必要な因子数を計算
    * @param aptitude 適性値 (-3:G, -2:F, -1:E, 0:D, 1:C, 2:B, 3:A, 4:S)
    * @return int 必要な因子数
    """
    if aptitude == -3:  # G
        return 4
    elif aptitude == -2:  # F
        return 4
    elif aptitude == -1:  # E
        return 4
    elif aptitude == 0:  # D
        return 3
    elif aptitude == 1:  # C
        return 2
    elif aptitude == 2:  # B
        return 1
    else:  # A以上
        return 0


def calculate_factor_composition(umamusume_data, pattern_races):
    """ウマ娘の適性とパターン内レースを元に因子構成を計算
    * @param umamusume_data ウマ娘データオブジェクト
    * @param pattern_races パターン内レースリスト
    * @return list 因子構成リスト (6個)
    """
    aptitude_map = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': -1, 'F': -2, 'G': -3}
    
    turf_aptitude = aptitude_map.get(umamusume_data.turf_aptitude, 0)
    dirt_aptitude = aptitude_map.get(umamusume_data.dirt_aptitude, 0)
    sprint_aptitude = aptitude_map.get(umamusume_data.sprint_aptitude, 0)
    mile_aptitude = aptitude_map.get(umamusume_data.mile_aptitude, 0)
    classic_aptitude = aptitude_map.get(umamusume_data.classic_aptitude, 0)
    long_aptitude = aptitude_map.get(umamusume_data.long_distance_aptitude, 0)
    
    # パターン内レースの馬場・距離を集計
    surface_usage = {0: False, 1: False}
    distance_usage = {1: False, 2: False, 3: False, 4: False}
    distance_count = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for race in pattern_races:
        surface_usage[race.race_state] = True
        distance_usage[race.distance] = True
        distance_count[race.distance] += 1
    
    factors = []
    
    # 6個すべて埋めるまでループ
    while len(factors) < 6:
        added = False
        
        # 馬場適性を優先
        for surface_state, surface_name in [(1, 'ダート'), (0, '芝')]:
            if surface_usage[surface_state]:
                current_aptitude = dirt_aptitude if surface_state == 1 else turf_aptitude
                current_count = factors.count(surface_name)
                needed_factors = calculate_needed_factors(current_aptitude)
                
                if current_count < needed_factors:
                    factors.append(surface_name)
                    added = True
                    break
        
        if added:
            continue
        
        # 距離適性を低い順に優先
        distance_priorities = []
        if distance_usage[1]:
            distance_priorities.append((sprint_aptitude, '短距離', distance_count[1]))
        if distance_usage[2]:
            distance_priorities.append((mile_aptitude, 'マイル', distance_count[2]))
        if distance_usage[3]:
            distance_priorities.append((classic_aptitude, '中距離', distance_count[3]))
        if distance_usage[4]:
            distance_priorities.append((long_aptitude, '長距離', distance_count[4]))
        
        distance_priorities.sort(key=lambda x: (x[0], -x[2]))
        
        for aptitude, factor_name, count in distance_priorities:
            current_count = factors.count(factor_name)
            needed_factors = calculate_needed_factors(aptitude)
            
            if current_count < needed_factors:
                factors.append(factor_name)
                added = True
                break
        
        if not added:
            factors.append('自由')
    
    return factors[:6]