from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from .models import *
from .serializers import *
from .utils import UmamusumeLog
from .breedingCount import getbreedingCountData
from .racePattern import get_race_pattern_data

@api_view(['POST'])
@permission_classes([AllowAny])
def race_list(request):
    """レースのリストをDBから取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.data.state レース場状態 (-1:全て, その他:指定状態)
    * @param request.data.distance 距離 (-1:全て, その他:指定距離)
    * @return Response レースリストデータ
    """
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
    """ウマ娘を登録する際のレース情報を加工してDBから取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @return Response レース登録用リストデータ
    """
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
    """ユーザーが登録したウマ娘の未出走データを取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @return Response ウマ娘別の残レース情報
    """
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
                breedingCount = getbreedingCountData(regist_umamusume,remaining_races)
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
                "breedingCount": breedingCount,
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
    """シーズン、出走月、前後半また対象ウマ娘が出走していないレースを取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @param request.data.umamusumeId ウマ娘ID
    * @param request.data.season シーズン (1:ジュニア, 2:クラシック, 3:シニア)
    * @param request.data.month 出走月 (1-12)
    * @param request.data.half 前後半 (0:前半, 1:後半)
    * @return Response レース情報とプロパティ
    """
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
    """全体残レース、シーズン、出走月、前後半を引数としてレースを取得する関数
    * @param regist_race_ids 出走済みレースIDリスト
    * @param season シーズン (1:ジュニア, 2:クラシック, 3:シニア)
    * @param month 出走月 (1-12)
    * @param half 前後半 (0:前半, 1:後半)
    * @return QuerySet レース情報のクエリセット
    """
    remaining_races = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])
    
    if season == 1:
        return remaining_races.filter(half_flag=half, race_months=month, junior_flag=1)
    elif season == 2:
        return remaining_races.filter(half_flag=half, race_months=month, classic_flag=1)
    elif season == 3:
        return remaining_races.filter(half_flag=half, race_months=month, senior_flag=1)
    
    return Race.objects.none()


def set_race_return(regist_race_ids, prop):
    """対象時期より前にレースが存在するか検証する関数
    * @param regist_race_ids 出走済みレースIDリスト
    * @param prop プロパティ辞書 (season, month, half)
    * @return bool 前にレースが存在するかどうか
    """
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
    """対象時期より後にレースが存在するか検証する関数
    * @param regist_race_ids 出走済みレースIDリスト
    * @param prop プロパティ辞書 (season, month, half)
    * @return bool 後にレースが存在するかどうか
    """
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
    """対象のレースに対して出走した結果を残すAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @param request.data.umamusumeId ウマ娘ID
    * @param request.data.raceId レースID
    * @return Response 出走完了メッセージ
    """
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


@api_view(['GET'])
@permission_classes([AllowAny])
def get_race_pattern(request):
    """残レースから計算したレース順序を出力するAPI
    * @param request HTTPリクエストオブジェクト
    * @return Response レースパターンデータ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'get_race_pattern')
    
    try:
        umamusume_id = 2    # 仮のウマ娘ID
        user_id = 1         # 仮のユーザーID
        
        # RegistUmamusumeを取得
        regist_umamusume = RegistUmamusume.objects.get(user_id=user_id, umamusume_id=umamusume_id)
        
        # 出走済みレースIDを取得
        regist_race_ids = RegistUmamusumeRace.objects.filter(
            user_id=user_id,
            umamusume_id=umamusume_id
        ).values_list('race_id', flat=True)
        
        # 残レースを取得
        remaining_races = Race.objects.exclude(race_id__in=regist_race_ids).filter(race_rank__in=[1, 2, 3])

        # シナリオレースを取得
        scenario_races = ScenarioRace.objects.filter(umamusume_id=regist_umamusume.umamusume_id)
        
        final_count = 6  # 仮の最終育成数
        race_pattern = get_race_pattern_data(final_count, user_id, umamusume_id)
        return Response({'data': race_pattern})
    except Exception as e:
        logger.logwrite('error', f'get_race_pattern:{e}')
        return Response({'error': '残レース計算エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)