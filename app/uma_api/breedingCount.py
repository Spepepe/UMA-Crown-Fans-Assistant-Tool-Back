from .models import ScenarioRace
def getbreedingCountData( umamusume , remaining_races ):
    """全冠までの目安育成数を計算する関数
    * @param umamusume ウマ娘オブジェクト
    * @param remaining_races 残レースのクエリセット
    * @return int 必要な育成回数
    """
    
    # 1. ウマ娘に紐づくシナリオレースを取得
    scenario_races = ScenarioRace.objects.filter(umamusume_id=umamusume.umamusume_id)
    
    # 2. シナリオレースと被るタイミングの残レースを抽出
    conflicting_races = []
    added_race_ids = set()  # 重複チェック用
    for scenario_race in scenario_races:
        race = scenario_race.race
        # 同じ月・前後半の残レースを検索
        for remaining_race in remaining_races:
            if (remaining_race.race_months == race.race_months and 
                remaining_race.half_flag == race.half_flag and
                remaining_race.race_id not in added_race_ids):
                conflicting_races.append(remaining_race)
                added_race_ids.add(remaining_race.race_id)
    
    # remaining_races全体を級、月、前後半で集計
    remaining_summary = {}
    for race in remaining_races:
        if race.junior_flag:
            grade = 1
        elif race.classic_flag:
            grade = 2
        elif race.senior_flag:
            grade = 3
        else:
            grade = 0
        
        key = (grade, race.race_months, race.half_flag)
        if key not in remaining_summary:
            remaining_summary[key] = []
        remaining_summary[key].append(race.race_name)
    

    
    # conflicting_racesを級、月、前後半で集計
    conflicting_summary = {}
    for race in conflicting_races:
        if race.junior_flag:
            grade = 1
        elif race.classic_flag:
            grade = 2
        elif race.senior_flag:
            grade = 3
        else:
            grade = 0
        
        key = (grade, race.race_months, race.half_flag)
        if key not in conflicting_summary:
            conflicting_summary[key] = []
        conflicting_summary[key].append(race.race_name)
    


    # 各ターンの残レース数を計算
    turn_remaining = {}
    for race in remaining_races:
        grades = []
        if race.junior_flag:
            grades.append(1)
        if race.classic_flag:
            grades.append(2)
        if race.senior_flag:
            grades.append(3)
        
        for grade in grades:
            key = (grade, race.race_months, race.half_flag)
            if key not in turn_remaining:
                turn_remaining[key] = 0
            # 複数級の場合は各級で0.5、単一級の場合は1.0
            race_score = 0.5 if len(grades) > 1 else 1.0
            turn_remaining[key] += race_score
    
    # 各ターンのシナリオ競合数を計算
    turn_conflicts = {}
    for race in conflicting_races:
        grades = []
        if race.junior_flag:
            grades.append(1)
        if race.classic_flag:
            grades.append(2)
        if race.senior_flag:
            grades.append(3)
        
        for grade in grades:
            key = (grade, race.race_months, race.half_flag)
            if key not in turn_conflicts:
                turn_conflicts[key] = 0
            # 複数級の場合は各級で0.5、単一級の場合は1.0
            race_score = 0.5 if len(grades) > 1 else 1.0
            turn_conflicts[key] += race_score
    
    # 最大育成回数を決定
    max_breeding_count = 1
    for key in sorted(turn_remaining.keys()):
        remaining_count = turn_remaining.get(key, 0)
        conflict_count = turn_conflicts.get(key, 0)
        required_count = max(remaining_count, conflict_count)
        max_breeding_count = max(max_breeding_count, required_count)
    
    import math
    final_count = math.ceil(max_breeding_count)
    return final_count