def calculate_aptitude_factors(umamusume, target_surface, target_style):
    """
    ウマ娘の適性と目標因子に基づいて、継承させるべき因子を計算します。
    因子厳選のサポート（特にダート適性の補強）を最優先とし、
    その後、他の適性補強、最後に目標因子を返す、という優先順位で計算します。

    補強の優先順位:
    1. ダート適性 'G' or 'F' (因子厳選サポート)
    2. 距離・バ場適性 'E'
    3. 距離・バ場適性 'D'

    * @param umamusume ウマ娘オブジェクト
    * @param target_surface 目標の馬場因子 (例: "芝")
    * @param target_style 目標の脚質因子 (例: "差し")
    * @return tuple 因子ペア (factor_one, factor_two)
    """
    # ウマ娘情報がない場合は、目標因子をそのまま返す
    if not umamusume:
        return target_surface, target_style

    # --- 優先度1: ダート因子厳選のための補強 ---
    # ダート適性がGまたはFの場合、レースに勝利するために「ダート」因子を2つ提案する
    if umamusume.dirt_aptitude in ['G', 'F']:
        return "ダート", "ダート"

    # --- 優先度2: E適性の補強 ---
    # E適性がある場合、その因子を2つ返すことで最優先で補強する
    # 優先順位: マイル > 中距離 > 長距離 > 短距離 > ダート
    if umamusume.mile_aptitude == "E":
        return "マイル", "マイル"
    if umamusume.classic_aptitude == "E":
        return "中距離", "中距離"
    if umamusume.long_distance_aptitude == "E":
        return "長距離", "長距離"
    if umamusume.sprint_aptitude == "E":
        return "短距離", "短距離"
    if umamusume.dirt_aptitude == "E":
        return "ダート", "ダート"

    # --- 優先度3: D適性の補強 ---
    # 補強対象のD適性をリストアップ (優先度順)
    d_factors = []
    if umamusume.classic_aptitude == "D": d_factors.append("中距離")
    if umamusume.mile_aptitude == "D": d_factors.append("マイル")
    if umamusume.long_distance_aptitude == "D": d_factors.append("長距離")
    if umamusume.sprint_aptitude == "D": d_factors.append("短距離")
    if umamusume.dirt_aptitude == "D": d_factors.append("ダート")

    if len(d_factors) >= 2:
        # D適性が2つ以上ある場合、優先度の高い2つを返す
        return d_factors[0], d_factors[1]
    elif len(d_factors) == 1:
        # D適性が1つだけの場合、その因子と目標因子を組み合わせる
        factor_one = d_factors[0]
        # 補強因子と異なる方の目標因子をもう片方に設定する
        if factor_one != target_surface:
            factor_two = target_surface
        else:
            factor_two = target_style
        return factor_one, factor_two

    # --- デフォルト: 補強が不要な場合 ---
    # ユーザーが指定した目標の馬場と脚質を返す。
    return target_surface, target_style