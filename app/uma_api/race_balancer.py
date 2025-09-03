"""レース配置バランス調整モジュール"""

def balance_race_distribution(pattern):
    """レース配置を調整して連続出走を回避
    * @param pattern レースパターン辞書
    * @return dict 調整されたパターン
    """
    # 各級のレース配置状況をチェック
    for grade in ['junior', 'classic', 'senior']:
        pattern[grade] = redistribute_grade_races(pattern[grade])
    
    return pattern


def redistribute_grade_races(grade_races):
    """級内でのレース再配置
    * @param grade_races 級内レースリスト
    * @return list 調整されたレースリスト
    """
    # レースがあるスロットを特定
    race_slots = []
    empty_slots = []
    
    for idx, race_data in enumerate(grade_races):
        if race_data['race_name']:
            race_slots.append(idx)
        else:
            empty_slots.append(idx)
    
    # 連続出走をチェック
    consecutive_groups = find_consecutive_slots(race_slots)
    
    # 4回以上連続の場合のみ調整
    for group in consecutive_groups:
        if len(group) >= 4:
            # 後半の空きスロットに移動
            moved_count = move_races_to_later_slots(grade_races, group, empty_slots)
            if moved_count > 0:
                # 空きスロットリストを更新
                empty_slots = [idx for idx, race_data in enumerate(grade_races) if not race_data['race_name']]
    
    return grade_races


def find_consecutive_slots(race_slots):
    """連続するレーススロットを検出
    * @param race_slots レースがあるスロットのインデックスリスト
    * @return list 連続グループのリスト
    """
    if not race_slots:
        return []
    
    consecutive_groups = []
    current_group = [race_slots[0]]
    
    for i in range(1, len(race_slots)):
        if race_slots[i] == race_slots[i-1] + 1:  # 連続している
            current_group.append(race_slots[i])
        else:
            if len(current_group) >= 2:
                consecutive_groups.append(current_group)
            current_group = [race_slots[i]]
    
    if len(current_group) >= 2:
        consecutive_groups.append(current_group)
    
    return consecutive_groups


def move_races_to_later_slots(grade_races, consecutive_group, empty_slots):
    """連続レースを後半の空きスロットに移動
    * @param grade_races 級内レースリスト
    * @param consecutive_group 連続レースグループ
    * @param empty_slots 空きスロットリスト
    * @return int 移動したレース数
    """
    if len(consecutive_group) < 4:
        return 0
    
    # 移動対象は連続グループの後半部分
    races_to_move = consecutive_group[2:]  # 3番目以降を移動
    
    # 後半の空きスロットを優先（インデックスの大きい順）
    available_slots = sorted([slot for slot in empty_slots if slot > consecutive_group[-1]], reverse=True)
    
    moved_count = 0
    for race_idx in races_to_move:
        if available_slots:
            target_slot = available_slots.pop(0)
            
            # レースを移動
            race_name = grade_races[race_idx]['race_name']
            grade_races[race_idx]['race_name'] = ''  # 元の位置をクリア
            grade_races[target_slot]['race_name'] = race_name  # 新しい位置に配置
            
            moved_count += 1
    
    return moved_count