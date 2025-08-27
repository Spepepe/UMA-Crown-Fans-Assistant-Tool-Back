from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from .models import *
from .serializers import *
from .utils import UmamusumeLog


@api_view(['POST'])
@permission_classes([AllowAny])
def race_list(request):
    """レースのリストをDBから取得するAPI"""
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'raceList')
    
    try:
        races = Race.objects.extra(
            select={'custom_order': """
                CASE
                    WHEN junior_flag = 1 THEN 1
                    WHEN classic_flag = 1 THEN 2
                    WHEN senior_flag = 1 THEN 3
                    ELSE 4
                END
            """}
        ).order_by('custom_order', 'race_months', 'half_flag', 'race_rank')
        
        state = request.data.get('state')
        if state != -1:
            races = races.filter(race_state=state)
        
        distance = request.data.get('distance')
        if distance != -1:
            races = races.filter(distance=distance)
        
        serializer = RaceSerializer(races, many=True)
        logger.logwrite('end', f'raceList - 取得件数:{len(serializer.data)} (state:{state}, distance:{distance})')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'raceList:{e}')
        return Response({'error': 'レースリスト取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def race_regist_list(request):
    """ウマ娘を登録する際のレース情報を加工してDBから取得するAPI"""
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'raceRegistList')
    
    try:
        races = Race.objects.filter(race_rank__in=[1, 2, 3]).order_by('race_rank', 'race_months', 'half_flag')
        serializer = RaceSerializer(races, many=True)
        logger.logwrite('end', f'raceRegistList - 取得件数:{len(serializer.data)}')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'raceRegistList:{e}')
        return Response({'error': 'レース登録リスト取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def remaining(request):
    """ユーザーが登録したウマ娘の未出走データを取得するAPI"""
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'remaining')
    
    try:
        user_id = request.user.user_id
        regist_umamusumes = RegistUmamusume.objects.filter(user_id=user_id).select_related('umamusume')
        
        results = []
        for regist_umamusume in regist_umamusumes:
            regist_race_ids = RegistUmamusumeRace.objects.filter(
                user_id=user_id,
                umamusume_id=regist_umamusume.umamusume_id
            ).values_list('race_id', flat=True)
            
            remaining_races = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])
            
            is_all_crown = remaining_races.count() == 0
            
            if not is_all_crown:
                turf_sprint_race = remaining_races.filter(race_state=0, distance=1).count()
                turf_mile_race = remaining_races.filter(race_state=0, distance=2).count()
                turf_classic_race = remaining_races.filter(race_state=0, distance=3).count()
                turf_long_distance_race = remaining_races.filter(race_state=0, distance=4).count()
                dirt_sprint_distance_race = remaining_races.filter(race_state=1, distance=1).count()
                dirt_mile_race = remaining_races.filter(race_state=1, distance=2).count()
                dirt_classic_race = remaining_races.filter(race_state=1, distance=3).count()
            else:
                turf_sprint_race = turf_mile_race = turf_classic_race = turf_long_distance_race = 0
                dirt_sprint_distance_race = dirt_mile_race = dirt_classic_race = 0
            
            result = {
                "umamusume": UmamusumeSerializer(regist_umamusume.umamusume).data,
                "isAllCrown": is_all_crown,
                "allCrownRace": remaining_races.count(),
                "turfSprintRace": turf_sprint_race,
                "turfMileRace": turf_mile_race,
                "turfClassicRace": turf_classic_race,
                "turfLongDistanceRace": turf_long_distance_race,
                "dirtSprintDistanceRace": dirt_sprint_distance_race,
                "dirtMileRace": dirt_mile_race,
                "dirtClassicRace": dirt_classic_race,
            }
            results.append(result)
        
        logger.logwrite('end', f'remaining - 取得ウマ娘数:{len(results)} (user_id:{user_id})')
        return Response({'data': results})
    except Exception as e:
        logger.logwrite('error', f'remaining:{e}')
        return Response({'error': '残レース取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remaining_to_race(request):
    """シーズン、出走月、前後半また対象ウマ娘が出走していないレースを取得するAPI"""
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'remainingToRace')
    
    try:
        user_id = request.user.user_id
        umamusume_id = request.data.get('umamusumeId')
        season = request.data.get('season')
        month = request.data.get('month')
        half = request.data.get('half')
        
        props = {
            'season': season,
            'month': month,
            'half': half
        }
        
        regist_race_ids = RegistUmamusumeRace.objects.filter(
            user_id=user_id,
            umamusume_id=umamusume_id
        ).values_list('race_id', flat=True)
        
        race = set_remaining_race(regist_race_ids, season, month, half)
        
        loop_count = 0
        while not race and loop_count < 2:
            second_half = 0 if half == 1 else 1
            second_month = month
            second_season = season
            
            if half:
                second_month = month + 1
                if month == 12:
                    second_month = 1
                    if season < 3:
                        second_season = season + 1
            
            props['season'] = second_season
            props['month'] = second_month
            props['half'] = second_half
            
            race = set_remaining_race(regist_race_ids, second_season, second_month, second_half)
            loop_count += 1
        
        props['isRaceReturn'] = set_race_return(regist_race_ids, props)
        props['isRaceForward'] = set_race_forward(regist_race_ids, props)
        
        race_count = len(race) if race else 0
        logger.logwrite('end', f'remainingToRace - 取得レース数:{race_count} (umamusume_id:{umamusume_id}, season:{season}, month:{month}, half:{half})')
        return Response({'data': RaceSerializer(race, many=True).data if race else [], 'Props': props})
    except Exception as e:
        logger.logwrite('error', f'remainingToRace:{e}')
        return Response({'error': '残レース検索エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def set_remaining_race(regist_race_ids, season, month, half):
    """全体残レース、シーズン、出走月、前後半を引数としてレースを取得する関数"""
    remaining_races = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])
    
    if season == 1:
        return remaining_races.filter(half_flag=half, race_months=month, junior_flag=1)
    elif season == 2:
        return remaining_races.filter(half_flag=half, race_months=month, classic_flag=1)
    elif season == 3:
        return remaining_races.filter(half_flag=half, race_months=month, senior_flag=1)
    
    return Race.objects.none()


def set_race_return(regist_race_ids, prop):
    """対象時期より前にレースが存在するか検証する関数"""
    remaining_races = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])
    
    for s in range(prop['season'], 0, -1):
        month = prop['month']
        half = prop['half']
        
        if prop['season'] == s:
            if half == 1:
                if s == 1 and remaining_races.filter(half_flag=0, race_months=month, junior_flag=1).exists():
                    return True
                elif s == 2 and remaining_races.filter(half_flag=0, race_months=month, classic_flag=1).exists():
                    return True
                elif s == 3 and remaining_races.filter(half_flag=0, race_months=month, senior_flag=1).exists():
                    return True
            
            if s == 1 and remaining_races.filter(race_months__lt=month, junior_flag=1).exists():
                return True
            elif s == 2 and remaining_races.filter(race_months__lt=month, classic_flag=1).exists():
                return True
            elif s == 3 and remaining_races.filter(race_months__lt=month, senior_flag=1).exists():
                return True
        else:
            if s == 1 and remaining_races.filter(junior_flag=1).exists():
                return True
            elif s == 2 and remaining_races.filter(classic_flag=1).exists():
                return True
    
    return False


def set_race_forward(regist_race_ids, prop):
    """対象時期より後にレースが存在するか検証する関数"""
    remaining_races = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])
    
    for s in range(prop['season'], 4):
        month = prop['month']
        half = prop['half']
        
        if prop['season'] == s:
            if half == 0:
                if s == 1 and remaining_races.filter(half_flag=1, race_months=month, junior_flag=1).exists():
                    return True
                elif s == 2 and remaining_races.filter(half_flag=1, race_months=month, classic_flag=1).exists():
                    return True
                elif s == 3 and remaining_races.filter(half_flag=1, race_months=month, senior_flag=1).exists():
                    return True
            
            if s == 1 and remaining_races.filter(race_months__gt=month, junior_flag=1).exists():
                return True
            elif s == 2 and remaining_races.filter(race_months__gt=month, classic_flag=1).exists():
                return True
            elif s == 3 and remaining_races.filter(race_months__gt=month, senior_flag=1).exists():
                return True
        else:
            if s == 2 and remaining_races.filter(classic_flag=1).exists():
                return True
            elif s == 3 and remaining_races.filter(senior_flag=1).exists():
                return True
    
    return False


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def race_run(request):
    """対象のレースに対して出走した結果を残すAPI"""
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'raceRun')
    
    try:
        user_id = request.user.user_id
        umamusume_id = request.data.get('umamusumeId')
        race_id = request.data.get('raceId')
        
        RegistUmamusumeRace.objects.create(
            user_id=user_id,
            umamusume_id=umamusume_id,
            race_id=race_id,
            regist_date=timezone.now()
        )
        
        logger.logwrite('end', f'raceRun - 出走登録完了 (user_id:{user_id}, umamusume_id:{umamusume_id}, race_id:{race_id})')
        return Response({'message': '出走完了'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.logwrite('error', f'raceRun:{e}')
        return Response({'error': 'ウマ娘出走エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remaining_pattern(request):
    """対象ウマ娘の残レースと適性に合わせて推奨される因子とシナリオを取得するAPI"""
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'remainingPattern')
    
    try:
        user_id = request.user.user_id
        umamusume_id = request.data.get('umamusumeId')
        
        if not umamusume_id:
            logger.logwrite('error', 'remainingPattern:ウマ娘IDが必要です')
            return Response({'error': 'ウマ娘IDが必要です'}, status=status.HTTP_400_BAD_REQUEST)
        
        select_umamusume = Umamusume.objects.get(umamusume_id=umamusume_id)
        
        regist_race_ids = RegistUmamusumeRace.objects.filter(
            user_id=user_id,
            umamusume_id=umamusume_id
        ).values_list('race_id', flat=True)
        
        remaining_races = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])
        
        is_exist_scenario_flag = check_duplicate_scenario_race(umamusume_id, remaining_races)
        is_exist_larc_flag = check_larc_scenario(remaining_races)
        
        result = {}
        
        if is_exist_scenario_flag:
            result['selectScenario'] = 'メイクラ'
        else:
            if is_exist_larc_flag:
                result['selectScenario'] = 'なんでも'
            else:
                result['selectScenario'] = 'Larc'
        
        result['requiredsFactor'] = get_requires_factor(remaining_races, select_umamusume)
        
        logger.logwrite('end', f'remainingPattern - シナリオ:{result["selectScenario"]}, 因子数:{len(result["requiredsFactor"])} (user_id:{user_id}, umamusume_id:{umamusume_id})')
        return Response({'data': result})
    except Exception as e:
        logger.logwrite('error', f'remainingPattern:{e}')
        return Response({'error': '推奨パターン取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def check_duplicate_scenario_race(umamusume_id, remaining_races):
    """残レースに対象ウマ娘のシナリオと被るレースが存在するか検証する関数"""
    scenario_races = ScenarioRace.objects.filter(umamusume_id=umamusume_id)
    
    for scenario_race in scenario_races:
        check_race = scenario_race.race
        
        # 複雑な条件チェックロジックを簡略化
        for remaining_race in remaining_races:
            if (remaining_race.race_months == check_race.race_months and
                remaining_race.half_flag == check_race.half_flag and
                remaining_race.race_name != check_race.race_name):
                return True
    
    return False


def check_larc_scenario(remaining_races):
    """残レースでラークシナリオを走るべきレースがあるか検証する関数"""
    if not remaining_races.filter(scenario_flag=1).exists():
        # 日本ダービー条件
        if remaining_races.exclude(race_name="日本ダービー").filter(half_flag=1, race_months=5).exists():
            return True
        # 夏合宿条件
        if remaining_races.exclude(race_name__in=["ニエル賞", "フォワ賞"]).filter(
            race_months__in=[7, 8, 9], classic_flag=0).exists():
            return True
        # 凱旋門賞条件
        if remaining_races.exclude(race_name="凱旋門賞").filter(race_months=10, half_flag=0).exists():
            return True
        # 宝塚記念条件
        if remaining_races.exclude(race_name="宝塚記念").filter(
            race_months=10, half_flag=0, senior_flag=1, classic_flag=0, junior_flag=0).exists():
            return True
    
    return False


def get_requires_factor(remaining_races, select_umamusume):
    """残レースから必要な因子情報を格納する関数"""
    rank_race = get_ranked_race_counts(remaining_races)
    requires_factor = []
    
    for i in range(min(7, len(rank_race))):
        race_info = rank_race[i]
        
        if race_info['race_type'] == '芝':
            requires_factor = set_requires_factor(
                select_umamusume.turf_aptitude, race_info['race_type'], requires_factor)
        else:
            requires_factor = set_requires_factor(
                select_umamusume.dirt_aptitude, race_info['race_type'], requires_factor)
        
        if len(requires_factor) == 6:
            break
        
        distance_map = {
            '短距離': select_umamusume.sprint_aptitude,
            'マイル': select_umamusume.mile_aptitude,
            '中距離': select_umamusume.classic_aptitude,
            '長距離': select_umamusume.long_distance_aptitude,
        }
        
        if race_info['distance'] in distance_map:
            requires_factor = set_requires_factor(
                distance_map[race_info['distance']], race_info['distance'], requires_factor)
        
        if len(requires_factor) == 6:
            break
    
    return sorted(requires_factor)


def get_ranked_race_counts(remaining_races):
    """残レースのレースをバ場と距離に分割してランク付けする関数"""
    race_counts = {
        '芝_短距離': remaining_races.filter(race_state=0, distance=1).count(),
        '芝_マイル': remaining_races.filter(race_state=0, distance=2).count(),
        '芝_中距離': remaining_races.filter(race_state=0, distance=3).count(),
        '芝_長距離': remaining_races.filter(race_state=0, distance=4).count(),
        'ダート_短距離': remaining_races.filter(race_state=1, distance=1).count(),
        'ダート_マイル': remaining_races.filter(race_state=1, distance=2).count(),
        'ダート_中距離': remaining_races.filter(race_state=1, distance=3).count(),
    }
    
    sorted_counts = sorted(race_counts.items(), key=lambda x: x[1], reverse=True)
    
    ranked_race_counts = []
    for rank, (key, count) in enumerate(sorted_counts, 1):
        race_type, distance = key.split('_')
        ranked_race_counts.append({
            'race_type': race_type,
            'distance': distance,
            'count': count,
            'rank': rank,
        })
    
    return ranked_race_counts


def set_requires_factor(aptitude, aptitude_type, factor_array):
    """対象の適性を引き上げるために必要な因子を計算する関数"""
    factor_count = {'E': 1, 'F': 2, 'G': 3}.get(aptitude, 0)
    
    for _ in range(factor_count):
        if len(factor_array) == 6:
            break
        factor_array.append(aptitude_type)
    
    return factor_array