from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Q, Count
from user_agents import parse
from .models import *
from .serializers import *
from .utils import UmamusumeLog
from itertools import permutations
import json
from .calculations import calculate_aptitude_factors


@api_view(['GET'])
@permission_classes([AllowAny])
def acter_list(request):
    """声優のリストをデータベースから取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @return Response 声優リストデータ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'acterList')
    
    try:
        acters = UmamusumeActer.objects.select_related('umamusume').order_by('-birthday')
        serializer = UmamusumeActerSerializer(acters, many=True)
        logger.logwrite('end', f'acterList - 取得件数:{len(serializer.data)}')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'acterList:{e}')
        return Response({'error': '声優リスト取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def jewel_list(request):
    """ジュエルのリストをデータベースから取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @param request.data.year 年
    * @param request.data.month 月
    * @return Response ジュエルリストデータ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'jewelList')
    
    try:
        user_id = request.user.user_id
        year = request.data.get('year')
        month = request.data.get('month')
        
        jewels = Jewel.objects.filter(
            user_id=user_id,
            year=year,
            month=month
        ).order_by('day')
        
        serializer = JewelSerializer(jewels, many=True)
        logger.logwrite('end', f'jewelList - 取得件数:{len(serializer.data)} ({year}/{month})')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'jewelList:{e}')
        return Response({'error': 'ジュエルリスト取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def jewel_regist(request):
    """当日のジュエルを登録するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @param request.data.jewel ジュエル金額
    * @return Response 登録完了メッセージ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'jewelRegist')
    
    try:
        user_id = request.user.user_id
        now = timezone.now()
        jewel_amount = request.data.get('jewel')
        
        jewel = Jewel.objects.create(
            user_id=user_id,
            year=now.year,
            month=now.month,
            day=now.day,
            jewel_amount=jewel_amount
        )
        
        logger.logwrite('end', f'jewelRegist - 登録金額:{jewel_amount}')
        return Response({'message': 'ジュエルが登録されました。'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.logwrite('error', f'jewelRegist:{e}')
        return Response({'error': 'ジュエル登録エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def live_list(request):
    """ライブのリストをデータベースから取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @return Response ライブリストデータ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'liveList')
    
    try:
        lives = Live.objects.all()
        serializer = LiveSerializer(lives, many=True)
        logger.logwrite('end', f'liveList - 取得件数:{len(serializer.data)}')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'liveList:{e}')
        return Response({'error': 'ライブリスト取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def umamusume_list_by_live(request):
    """ライブのIDを引数として、紐づくウマ娘の情報をDBから取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.data.liveId ライブID
    * @return Response ウマ娘リストデータ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'umamusumeListByLive')
    
    try:
        live_id = request.data.get('liveId')
        vocal_umamusumes = VocalUmamusume.objects.filter(live_id=live_id).select_related('umamusume')
        umamusumes = [vu.umamusume for vu in vocal_umamusumes]
        serializer = UmamusumeSerializer(umamusumes, many=True)
        logger.logwrite('end', f'umamusumeListByLive - 取得件数:{len(serializer.data)} (liveId:{live_id})')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'umamusumeListByLive:{e}')
        return Response({'error': 'ウマ娘リスト取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def umamusume_regist_list(request):
    """ユーザーが登録していない、ウマ娘情報を取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @return Response 未登録ウマ娘リストデータ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'umamusumeRegistList')
    
    try:
        user_id = request.user.user_id
        regist_umamusume_ids = RegistUmamusume.objects.filter(user_id=user_id).values_list('umamusume_id', flat=True)
        umamusumes = Umamusume.objects.exclude(umamusume_id__in=regist_umamusume_ids).order_by('umamusume_name')
        serializer = UmamusumeSerializer(umamusumes, many=True)
        logger.logwrite('end', f'umamusumeRegistList - 未登録件数:{len(serializer.data)}')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'umamusumeRegistList:{e}')
        return Response({'error': 'ウマ娘登録リスト取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def umamusume_regist(request):
    """ユーザーが選択した、ウマ娘のデータを登録するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @param request.data.umamusumeId ウマ娘ID
    * @param request.data.raceIdArray レースID配列
    * @param request.data.fans ファン数
    * @return Response 登録完了メッセージ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'umamusumeRegist')
    
    try:
        user_id = request.user.user_id
        umamusume_id = request.data.get('umamusumeId')
        race_id_array = request.data.get('raceIdArray', [])
        fans = request.data.get('fans')
        
        regist_umamusume = RegistUmamusume.objects.create(
            user_id=user_id,
            umamusume_id=umamusume_id,
            regist_date=timezone.now(),
            fans=fans
        )
        
        for race_id in race_id_array:
            RegistUmamusumeRace.objects.create(
                user_id=user_id,
                umamusume_id=umamusume_id,
                race_id=race_id,
                regist_date=timezone.now()
            )
        
        logger.logwrite('end', f'umamusumeRegist - 登録完了 umamusume_id:{umamusume_id}, レース数:{len(race_id_array)}')
        return Response({'message': 'ユーザーが登録されました。'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.logwrite('error', f'umamusumeRegist:{e}')
        return Response({'error': 'ウマ娘登録エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_regist_umamusume(request):
    """ユーザーが登録したウマ娘の情報を取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @return Response 登録済みウマ娘リストデータ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'userRegistUmamusume')
    
    try:
        user_id = request.user.user_id
        regist_umamusumes = RegistUmamusume.objects.filter(user_id=user_id).select_related('umamusume')
        serializer = RegistUmamusumeSerializer(regist_umamusumes, many=True)
        logger.logwrite('end', f'userRegistUmamusume - 登録済み件数:{len(serializer.data)}')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'userRegistUmamusume:{e}')
        return Response({'error': 'ユーザー登録ウマ娘取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fan_up(request):
    """ユーザーが入力したファン数をユーザーが登録したウマ娘データに反映させるAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @param request.data.umamusumeId ウマ娘ID
    * @param request.data.fans ファン数
    * @return Response 更新完了メッセージ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'fanUp')
    
    try:
        user_id = request.user.user_id
        umamusume_id = request.data.get('umamusumeId')
        fans = request.data.get('fans')
        
        updated_count = RegistUmamusume.objects.filter(user_id=user_id, umamusume_id=umamusume_id).update(fans=fans)
        
        logger.logwrite('end', f'fanUp - 更新完了 umamusume_id:{umamusume_id}, ファン数:{fans}, 更新件数:{updated_count}')
        return Response({'message': 'ファン数が変更されました'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.logwrite('error', f'fanUp:{e}')
        return Response({'error': 'ファン数更新エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_race_pattern(request):
    """選択されたレースパターンをまとめて登録するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user.user_id ユーザーID
    * @param request.data.umamusumeId ウマ娘ID
    * @param request.data.races レースオブジェクトの配列
    * @return Response 登録完了メッセージ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'register_race_pattern')
    
    try:
        user_id = request.user.user_id
        umamusume_id = request.data.get('umamusumeId')
        races = request.data.get('races', [])

        if not umamusume_id or not races:
            logger.logwrite('error', 'register_race_pattern - 不正なリクエスト: ウマ娘IDまたはレースデータがありません。')
            return Response({'error': 'ウマ娘IDとレースデータは必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        # 対象のウマ娘がユーザーによって登録されているか確認
        if not RegistUmamusume.objects.filter(user_id=user_id, umamusume_id=umamusume_id).exists():
            logger.logwrite('error', f'register_race_pattern - 対象のウマ娘が登録されていません: user_id={user_id}, umamusume_id={umamusume_id}')
            return Response({'error': '対象のウマ娘が登録されていません。'}, status=status.HTTP_400_BAD_REQUEST)

        race_records_to_create = []
        now = timezone.now()
        
        # 登録済みのレースIDを取得し、重複を避ける
        existing_race_ids = set(RegistUmamusumeRace.objects.filter(
            user_id=user_id, 
            umamusume_id=umamusume_id
        ).values_list('race_id', flat=True))

        for race in races:
            # フロントエンドからのキャメルケース(raceId)とスネークケース(race_id)の両方に対応
            race_id = race.get('race_id') or race.get('raceId')
            if race_id and race_id not in existing_race_ids:
                race_records_to_create.append(
                    RegistUmamusumeRace(user_id=user_id, umamusume_id=umamusume_id, race_id=race_id, regist_date=now)
                )
                # 同じリクエスト内での重複も防ぐ
                existing_race_ids.add(race_id)

        if race_records_to_create:
            RegistUmamusumeRace.objects.bulk_create(race_records_to_create)
        
        count = len(race_records_to_create)
        logger.logwrite('end', f'register_race_pattern - 登録完了 umamusume_id:{umamusume_id}, 新規レース数:{count}')
        return Response({'message': f'{count}件のレースが新たに出走登録されました。'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.logwrite('error', f'register_race_pattern:{e}')
        return Response({'error': 'レースパターン登録エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def umamusume_list(request):
    """ウマ娘情報を取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @return Response ウマ娘リストデータ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'umamusumLList')
    
    try:
        # umamusume_nameの五十音順でソートして取得
        umamusumes = Umamusume.objects.all().order_by('umamusume_name')
        
        serializer = UmamusumeSerializer(umamusumes, many=True)
        
        logger.logwrite('end', f'umamusumeList - 件数:{len(serializer.data)}')
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.logwrite('error', f'umamusumeList:{e}')
        return Response({'error': 'ウマ娘リスト取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def calculate_parent_factors(request):
    """因子情報を取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.GET.distance_id 距離ID
    * @param request.GET.surface_id コースID
    * @param request.GET.style_id 脚質ID
    * @param request.GET.parent_umamusume_id 親ウマ娘ID
    * @param request.GET.grandparent_umamusume_id 祖父ウマ娘ID
    * @param request.GET.grandmother_umamusume_id 祖母ウマ娘ID
    * @return Response 因子情報データ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'calculate_parent_factors')
    
    try:
        # リクエストから取得
        distance_id = int(request.GET.get('distance_id', 1))
        surface_id = int(request.GET.get('surface_id', 1))
        style_id = int(request.GET.get('style_id', 1))
        parent_umamusume_id = int(request.GET.get('parent_umamusume_id', 1))
        grandparent_umamusume_id = int(request.GET.get('grandparent_umamusume_id', 2))
        grandmother_umamusume_id = int(request.GET.get('grandmother_umamusume_id', 3))

        # IDを文字列に変換するマップ
        DISTANCE_MAP = {1: "短距離", 2: "マイル", 3: "中距離", 4: "長距離"}
        SURFACE_MAP = {1: "芝", 2: "ダート"}
        STYLE_MAP = {1: "逃げ", 2: "先行", 3: "差し", 4: "追込"}

        distance = DISTANCE_MAP.get(distance_id, "不明")
        surface = SURFACE_MAP.get(surface_id, "不明")
        style = STYLE_MAP.get(style_id, "不明")

        # ウマ娘情報をDBから取得
        parent_umamusume = Umamusume.objects.filter(umamusume_id=parent_umamusume_id).first()
        grandparent_umamusume = Umamusume.objects.filter(umamusume_id=grandparent_umamusume_id).first()
        grandmother_umamusume = Umamusume.objects.filter(umamusume_id=grandmother_umamusume_id).first()

        # 祖父母Aの適性因子を計算
        factor_a_1, factor_a_2 = calculate_aptitude_factors(grandparent_umamusume, surface, style)

        # 祖父母Bの適性因子を計算
        factor_b_1, factor_b_2 = calculate_aptitude_factors(grandmother_umamusume, surface, style)

        # --- パターン生成ロジック ---
        all_patterns = []

        # 1. 各祖父母のメイン因子プールを決定
        # 祖父母Aのメイン因子: サブ因子が「差し」x2なら「芝」x2、サブ因子が「芝」x2なら「差し」x2
        main_a_pool = (surface, style)
        if factor_a_1 == "差し" and factor_a_2 == "差し":
            main_a_pool = ("芝", "芝")
        elif factor_a_1 == "芝" and factor_a_2 == "芝":
            main_a_pool = ("差し", "差し")

        # 祖父母Bのメイン因子: 同様のロジック
        main_b_pool = (surface, style)
        if factor_b_1 == "差し" and factor_b_2 == "差し":
            main_b_pool = ("芝", "芝")
        elif factor_b_1 == "芝" and factor_b_2 == "芝":
            main_b_pool = ("差し", "差し")

        # 2. 各因子の組み合わせ(順列)を生成
        main_a_perms = sorted(list(set(permutations(main_a_pool))))
        sub_a_perms = sorted(list(set(permutations((factor_a_1, factor_a_2)))))
        main_b_perms = sorted(list(set(permutations(main_b_pool))))
        sub_b_perms = sorted(list(set(permutations((factor_b_1, factor_b_2)))))

        # 3. MainとSubの全組み合わせを生成
        for p_main_a in main_a_perms:
            for p_sub_a in sub_a_perms:
                for p_main_b in main_b_perms:
                    for p_sub_b in sub_b_perms:
                        # パターン1: 基本の組み合わせ
                        grandparent_a_factors = {
                            "aaa": p_main_a[0], "aba": p_main_a[1],
                            "aab": p_sub_a[0], "abb": p_sub_a[1],
                            "aa": factor_a_1, "ab": factor_a_2,
                        }
                        grandparent_b_factors = {
                            "baa": p_main_b[0], "bba": p_main_b[1],
                            "bab": p_sub_b[0], "bbb": p_sub_b[1],
                            "ba": factor_b_1, "bb": factor_b_2,
                        }
                        all_patterns.append({"factors": {"grandparent_a": grandparent_a_factors, "grandparent_b": grandparent_b_factors}})

                        # パターン2: 祖父母AとBのメイン因子を入れ替えた組み合わせ
                        grandparent_a_factors_swapped = {
                            "aaa": p_main_b[0], "aba": p_main_b[1], # Bのメイン因子を使用
                            "aab": p_sub_a[0], "abb": p_sub_a[1],
                            "aa": factor_a_1, "ab": factor_a_2,
                        }
                        grandparent_b_factors_swapped = {
                            "baa": p_main_a[0], "bba": p_main_a[1], # Aのメイン因子を使用
                            "bab": p_sub_b[0], "bbb": p_sub_b[1],
                            "ba": factor_b_1, "bb": factor_b_2,
                        }
                        all_patterns.append({"factors": {"grandparent_a": grandparent_a_factors_swapped, "grandparent_b": grandparent_b_factors_swapped}})

        # 最終的に生成されたパターンの中から重複を削除する
        unique_patterns = []
        seen_factors_str = set()
        for p in all_patterns:
            # factorsオブジェクトをJSON文字列に変換して比較
            factors_str = json.dumps(p['factors'], sort_keys=True)
            if factors_str not in seen_factors_str:
                # パターン名を追加してユニークリストに追加
                p["name"] = f"{len(unique_patterns) + 1}"
                unique_patterns.append(p)
                seen_factors_str.add(factors_str)

        return Response({'data': {'patterns': unique_patterns}})

    except Exception as e:
        logger.logwrite('error', f'calculate_parent_factors:{e}')
        return Response({'error': '因子情報取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



"""ユーザー関連API群"""
@api_view(['POST'])
@permission_classes([AllowAny])
def user_register(request):
    """ユーザーを登録するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.data ユーザー登録データ
    * @return Response 登録結果メッセージ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'userRegister')
    
    try:
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.logwrite('end', f'userRegister - 登録完了 user_name:{user.user_name}')
            return Response({
                'message': 'ユーザーが登録されました。',
                'user': UserPersonalSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        else:
            logger.logwrite('error', f'userRegister - バリデーションエラー:{serializer.errors}')
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.logwrite('error', f'userRegister:{e}')
        return Response({'error': 'ユーザー登録エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    """ユーザーログインAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.data.userName ユーザー名
    * @param request.data.password パスワード
    * @return Response ログイン結果とトークン
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'userLogin')
    
    try:
        user_name = request.data.get('userName')
        password = request.data.get('password')
        
        try:
            user = UserPersonal.objects.get(user_name=user_name)
        except UserPersonal.DoesNotExist:
            logger.logwrite('error', f'userLogin - ユーザーが見つかりません user_name:{user_name}')
            return Response({'message': 'ユーザーが見つかりません。'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            logger.logwrite('end', f'userLogin - ログイン成功 user_name:{user_name}')
            return Response({
                'message': 'ログイン成功',
                'token': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
        else:
            logger.logwrite('error', f'userLogin - パスワード認証失敗 user_name:{user_name}')
            return Response({'message': 'パスワードが違います。'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        logger.logwrite('error', f'userLogin:{e}')
        return Response({'error': 'ログインエラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    """ログアウトのためのAPI
    * @param request HTTPリクエストオブジェクト
    * @return Response ログアウト完了メッセージ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'userLogout')
    
    try:
        # JWTトークンはステートレスなので、クライアント側で削除
        logger.logwrite('end', 'userLogout - ログアウト完了')
        return Response({'message': 'ログアウトしました'})
    except Exception as e:
        logger.logwrite('error', f'userLogout:{e}')
        return Response({'error': 'ログアウトエラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    """ログイン中のユーザー情報を取得するAPI
    * @param request HTTPリクエストオブジェクト
    * @param request.user ログインユーザー
    * @return Response ユーザー情報データ
    """
    logger = UmamusumeLog(request)
    logger.logwrite('start', 'getUserData')
    
    try:
        serializer = UserPersonalSerializer(request.user)
        logger.logwrite('end', f'getUserData - 取得完了 user_name:{request.user.user_name}')
        return Response({'data': serializer.data})
    except Exception as e:
        logger.logwrite('error', f'getUserData:{e}')
        return Response({'error': 'ユーザーデータ取得エラー'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
