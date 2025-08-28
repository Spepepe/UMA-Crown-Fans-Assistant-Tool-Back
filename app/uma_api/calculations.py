def calculate_aptitude_factors(umamusume, base_factor_distance, base_factor_style):
    """
    ウマ娘の適性に基づいて因子を計算し、返します。
    優先順位: マイル > 中距離 > 長距離 > ダート
    """
    # ウマ娘情報がない場合はデフォルト値を返す
    if not umamusume:
        return base_factor_distance, base_factor_style

    # E適性の優先度を先に判定 (マイル > 中距離 > 長距離の順)
    if umamusume.mile_aptitude == "E":
        return "マイル", "マイル"
    
    if umamusume.classic_aptitude == "E":
        return "中距離", "中距離"
        
    if umamusume.long_distance_aptitude == "E":
        factor_one = "長距離"
        # ダート適性がFならダート因子、Gなら長距離因子、D以上ならベース因子
        if umamusume.dirt_aptitude == 'F':
            factor_two = "ダート"
        else:
            factor_two = "長距離"
        return factor_one, factor_two

    # D適性の判定
    # D適性の中での優先順位も考慮 (中距離 > マイル)
    factor_one = base_factor_distance
    if umamusume.classic_aptitude == "D":
        factor_one = "中距離"
    elif umamusume.mile_aptitude == "D":
        factor_one = "マイル"

    # `ABB`または`BBB`の因子の特別処理
    factor_two = base_factor_distance
    # マイルDと中距離Dが両方Dの場合、もう片方が中距離になる
    if umamusume.classic_aptitude == "D" and umamusume.mile_aptitude == "D":
        factor_two = "中距離"

    if umamusume.dirt_aptitude == 'G' and factor_one == base_factor_distance and factor_two == base_factor_distance:
        # ダート適性がGでかつ、E/D適性による因子が決定しなかった場合
        return "ダート","ダート"
    
    if umamusume.dirt_aptitude == 'F':
        # ここに到達した場合、ダート適性がFで、E/D適性による因子が決定しなかった場合
        if factor_one == base_factor_distance:
            factor_one = "ダート"
        if factor_two == base_factor_distance:
            factor_two = "ダート"
    
    # ダート適性がA, B, C, Dの場合の特殊処理
    if umamusume.dirt_aptitude in ['A', 'B', 'C', 'D']:
        return base_factor_distance, base_factor_distance
            
    # 片方のスロットが空いていれば脚質因子で埋める
    if factor_one == base_factor_distance and factor_two != base_factor_distance:
        factor_one = base_factor_style
    elif factor_one != base_factor_distance and factor_two == base_factor_distance:
        factor_two = base_factor_style
    
    return factor_one, factor_two