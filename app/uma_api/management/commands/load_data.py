import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from uma_api.models import *

class Command(BaseCommand):
    help = 'Load initial data from JSON files'

    def handle(self, *args, **options):
        base_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
        
        # レースデータ
        race_file = os.path.join(base_path, 'Race.json')
        if os.path.exists(race_file):
            with open(race_file, 'r', encoding='utf-8') as f:
                race_data = json.load(f)
            self.load_races(race_data)
        
        # ウマ娘データ
        umamusume_file = os.path.join(base_path, 'Umamusume.json')
        if os.path.exists(umamusume_file):
            with open(umamusume_file, 'r', encoding='utf-8') as f:
                umamusume_data = json.load(f)
            self.load_umamusume(umamusume_data)
        
        # ライブデータ
        live_file = os.path.join(base_path, 'Live.json')
        if os.path.exists(live_file):
            with open(live_file, 'r', encoding='utf-8') as f:
                live_data = json.load(f)
            self.load_lives(live_data)

    # ------------------ RACE ------------------ #
    def load_races(self, race_data):
        for race_name, race_info in race_data.items():
            if not Race.objects.filter(race_name=race_name).exists():
                Race.objects.create(
                    race_name=race_info['名前'],
                    race_state=1 if race_info['馬場'] == 'ダート' else 0,
                    distance=self.get_race_distance(race_info['距離']),
                    distance_detail=int(race_info['距離詳細']) if '距離詳細' in race_info and race_info['距離詳細'] else None,
                    num_fans=int(race_info['獲得ファン数']) if '獲得ファン数' in race_info else 0,
                    race_months=int(race_info['出走月']),
                    half_flag=1 if race_info['前後半'] == '後半' else 0,
                    race_rank=self.get_race_rank(race_info['レースランク']),
                    junior_flag=1 if race_info.get('ジュニア') == '〇' else 0,
                    classic_flag=1 if race_info.get('クラシック') == '〇' else 0,
                    senior_flag=1 if race_info.get('シニア') == '〇' else 0,
                    scenario_flag=1 if race_info.get('特定シナリオ') == 'あり' else 0
                )
                self.stdout.write(f'{race_name}を登録しました。')

    # ------------------ UMAMUSUME ------------------ #
    def load_umamusume(self, umamusume_data):
        for umamusume_name, umamusume_info in umamusume_data.items():
            if not Umamusume.objects.filter(umamusume_name=umamusume_name).exists():
                umamusume = Umamusume.objects.create(
                    umamusume_name=umamusume_info['名前'],
                    turf_aptitude=umamusume_info['芝'],
                    dirt_aptitude=umamusume_info['ダート'],
                    sprint_aptitude=umamusume_info['短距離'],
                    mile_aptitude=umamusume_info['マイル'],
                    classic_aptitude=umamusume_info['中距離'],
                    long_distance_aptitude=umamusume_info['長距離'],
                    front_runner_aptitude=umamusume_info.get('逃げ', 'G'),
                    early_foot_aptitude=umamusume_info.get('先行', 'G'),
                    midfield_aptitude=umamusume_info.get('差し', 'G'),
                    closer_aptitude=umamusume_info.get('追込', 'G')
                )
                self.stdout.write(f'{umamusume_name}を登録しました。')
                
                # 声優情報
                acter_info = umamusume_info['声優']
                if not UmamusumeActer.objects.filter(acter_name=acter_info['名前']).exists():
                    birthday_date = self.format_date(acter_info['誕生日'])
                    UmamusumeActer.objects.create(
                        umamusume=umamusume,
                        acter_name=acter_info['名前'],
                        birthday=birthday_date,
                        gender=acter_info.get('性別', '不明'),
                        nickname=acter_info.get('愛称', '')
                    )
                    self.stdout.write(f'{umamusume_name}の声優に{acter_info["名前"]}を登録しました。')
                
                # シナリオレース
                self.load_scenario_races(umamusume_info['シナリオ'], umamusume)

    # ------------------ SCENARIO RACE ------------------ #
    def load_scenario_races(self, scenario_data, umamusume):
        race_number = 1
        random_group = 1
        
        for key, value in scenario_data.items():
            if isinstance(value, list):
                for race_info in value:
                    self.create_scenario_race(race_info, umamusume, race_number, random_group)
                    race_number += 1
                random_group += 1
            elif isinstance(value, dict):
                if '名前' in value:
                    self.create_scenario_race(value, umamusume, race_number, None)
                    race_number += 1
                else:
                    for sub_race in value.values():
                        self.create_scenario_race(sub_race, umamusume, race_number, random_group)
                        race_number += 1
                    random_group += 1
            else:
                self.create_scenario_race(value, umamusume, race_number, None)
                race_number += 1

    def create_scenario_race(self, race_info, umamusume, race_number, random_group):
        if isinstance(race_info, dict):
            race_name = race_info['名前']
            senior_flag = race_info.get('時期') == 'シニア'
        else:
            race_name = race_info
            senior_flag = None
        
        try:
            race = Race.objects.get(race_name=race_name)
            if not ScenarioRace.objects.filter(race=race, umamusume=umamusume, race_number=race_number).exists():
                ScenarioRace.objects.create(
                    umamusume=umamusume,
                    race=race,
                    race_number=race_number,
                    random_group=random_group,
                    senior_flag=1 if senior_flag else None
                )
                self.stdout.write(f'{umamusume.umamusume_name}にシナリオレースの{race_name}を登録しました。')
        except Race.DoesNotExist:
            self.stdout.write(f'レース {race_name} が見つかりません。')

    # ------------------ LIVE ------------------ #
    def load_lives(self, live_data):
        for live_name, live_info in live_data.items():
            if not Live.objects.filter(live_name=live_info['曲名']).exists():
                live = Live.objects.create(
                    live_name=live_info['曲名'],
                    composer=live_info.get('作曲', ''),
                    arranger=live_info.get('編曲', '')
                )
                self.stdout.write(f'{live_info["曲名"]}を登録しました。')
                
                singers = live_info['歌唱ウマ娘']
                if '1' in singers and singers['1'] == 'all':
                    for umamusume in Umamusume.objects.all():
                        if not VocalUmamusume.objects.filter(live=live, umamusume=umamusume).exists():
                            VocalUmamusume.objects.create(live=live, umamusume=umamusume)
                    self.stdout.write(f'{live_info["曲名"]}に全員を登録しました。')
                else:
                    for singer_name in singers.values():
                        try:
                            umamusume = Umamusume.objects.get(umamusume_name=singer_name)
                            if not VocalUmamusume.objects.filter(live=live, umamusume=umamusume).exists():
                                VocalUmamusume.objects.create(live=live, umamusume=umamusume)
                                self.stdout.write(f'{live_info["曲名"]}に{singer_name}を登録しました。')
                        except Umamusume.DoesNotExist:
                            self.stdout.write(f'ウマ娘 {singer_name} が見つかりません。')

    # ------------------ HELPERS ------------------ #
    def get_race_distance(self, distance_str):
        distance_map = {
            '短距離': 1,
            'マイル': 2,
            '中距離': 3,
            '長距離': 4
        }
        return distance_map.get(distance_str, 1)

    def get_race_rank(self, rank_str):
        rank_map = {
            'G1': 1,
            'G2': 2,
            'G3': 3,
            'PRE': 4,
            'OP': 5
        }
        return rank_map.get(rank_str, 1)
    
    def format_date(self, date_str):
        if date_str.startswith('9999/'):
            date_str = date_str.replace('9999/', '1999/')
        try:
            parts = date_str.split('/')
            if len(parts) == 3:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                return datetime(year, month, day).date()
            else:
                return datetime(1999, 1, 1).date()
        except:
            return datetime(1999, 1, 1).date()
