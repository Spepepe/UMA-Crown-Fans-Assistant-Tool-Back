ウマ娘全冠・因子厳選サポートツールのバックエンドAPI

## 概要

Django REST Frameworkを使用したウマ娘関連データ管理API。ユーザー認証、ウマ娘データ管理、レース情報、ジュエル管理、因子計算などの機能を提供。

## 技術スタック

- **Framework**: Django 5.1.1
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: JWT Token
- **Language**: Python 3.x

## 主要機能

### 認証機能
- ユーザー登録・ログイン
- JWT認証
- パスワード暗号化

### ウマ娘管理
- ウマ娘情報取得
- ユーザー別ウマ娘登録
- ファン数管理
- 適性情報管理

### レース管理
- レース情報取得
- 条件別レース検索
- ユーザー別出走レース管理

### ジュエル管理
- 日別ジュエル登録・更新
- 月別ジュエル履歴取得

### 因子計算
- 親因子計算API
- 距離・馬場・脚質別計算

## API エンドポイント

### 認証
- `POST /api/auth/login` - ログイン
- `POST /api/auth/regist` - ユーザー登録

### ウマ娘
- `GET /api/umamusume/list` - ウマ娘一覧取得
- `GET /api/umamusume/regist/list` - 未登録ウマ娘取得
- `POST /api/umamusume/regist` - ウマ娘登録
- `GET /api/umamusume/user/list` - ユーザー登録済みウマ娘取得
- `POST /api/umamusume/fan/up` - ファン数更新

### レース
- `POST /api/race/list` - レース一覧取得
- `GET /api/race/regist/list` - 登録可能レース取得
- `GET /api/race/remaining` - 残レース取得

### ジュエル
- `POST /api/jewel/list` - ジュエル履歴取得
- `POST /api/jewel/regist` - ジュエル登録・更新

### その他
- `GET /api/acter/list` - 声優情報取得
- `GET /api/live/list` - ライブ情報取得
- `GET /api/factor/calculate` - 因子計算

## データベース設計

### ER図

```mermaid
erDiagram
    UserPersonal ||--o{ RegistUmamusume : "1:N"
    UserPersonal ||--o{ RegistUmamusumeRace : "1:N"
    UserPersonal ||--o{ Jewel : "1:N"
    
    Umamusume ||--|| UmamusumeActer : "1:1"
    Umamusume ||--o{ RegistUmamusume : "1:N"
    Umamusume ||--o{ RegistUmamusumeRace : "1:N"
    Umamusume ||--o{ ScenarioRace : "1:N"
    Umamusume ||--o{ VocalUmamusume : "1:N"
    
    Race ||--o{ RegistUmamusumeRace : "1:N"
    Race ||--o{ ScenarioRace : "1:N"
    
    Live ||--o{ VocalUmamusume : "1:N"
    
    UserPersonal {
        int user_id PK
        string user_name UK
        string password
        string email
        boolean is_active
        boolean is_staff
    }
    
    Umamusume {
        int umamusume_id PK
        string umamusume_name
        string turf_aptitude
        string dirt_aptitude
        string front_runner_aptitude
        string early_foot_aptitude
        string midfield_aptitude
        string closer_aptitude
        string sprint_aptitude
        string mile_aptitude
        string classic_aptitude
        string long_distance_aptitude
    }
    
    UmamusumeActer {
        int acter_id PK
        int umamusume_id FK
        string acter_name
        string gender
        date birthday
        string nickname
    }
    
    Race {
        int race_id PK
        string race_name
        int race_state
        int distance
        int distance_detail
        int num_fans
        int race_months
        int half_flag
        int race_rank
        int junior_flag
        int classic_flag
        int senior_flag
        int scenario_flag
    }
    
    RegistUmamusume {
        int user_id FK
        int umamusume_id FK
        datetime regist_date
        bigint fans
    }
    
    RegistUmamusumeRace {
        int user_id FK
        int umamusume_id FK
        int race_id FK
        datetime regist_date
    }
    
    ScenarioRace {
        int umamusume_id FK
        int race_id FK
        int race_number
        int random_group
        int senior_flag
    }
    
    Live {
        int live_id PK
        string live_name
        string composer
        string arranger
    }
    
    VocalUmamusume {
        int live_id FK
        int umamusume_id FK
    }
    
    Jewel {
        int user_id FK
        int year
        int month
        int day
        int jewel_amount
    }
```

## セットアップ

### 前提条件
- Python 3.x
- PostgreSQL
- pip

### インストール

1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

2. データベース設定
```bash
python manage.py migrate
```

3. 開発サーバー起動
```bash
python manage.py runserver
```

## 環境変数

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## ログ機能

- APIアクセスログ: `uma_api.log`
- リクエスト/レスポンス詳細記録
- エラートラッキング

## 開発者向け情報

### モデル構造
- **UserPersonal**: カスタムユーザーモデル
- **Umamusume**: ウマ娘基本情報
- **Race**: レース情報
- **RegistUmamusume**: ユーザー別ウマ娘登録
- **Jewel**: ジュエル管理

### 認証方式
JWT Tokenベースの認証を使用。ヘッダーに`Authorization: Bearer <token>`を設定。