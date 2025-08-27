import logging

logger = logging.getLogger('uma_api')


class UmamusumeLog:
    def __init__(self, request=None):
        self.request = request
    
    def logwrite(self, msg: str, attribute: str):
        if msg == 'start':
            self.log_start(attribute)
        elif msg == 'end':
            self.log_end(attribute)
        elif msg == 'error':
            self.log_error(attribute)
        else:
            raise ValueError("msgの値に問題があります。")
    
    def _get_request_info(self):
        """リクエスト情報を取得する"""
        if not self.request:
            return ""
        
        info_parts = []
        
        # ユーザー情報
        if hasattr(self.request, 'user') and self.request.user:
            user_name = getattr(self.request.user, 'user_name', 'Anonymous')
            info_parts.append(f"user:{user_name}")
        
        # HTTPメソッド
        if hasattr(self.request, 'method'):
            info_parts.append(f"method:{self.request.method}")
        
        # リクエストデータ
        if hasattr(self.request, 'data') and self.request.data:
            # パスワードなどの機密情報を除外
            safe_data = {k: v for k, v in self.request.data.items() 
                        if k.lower() not in ['password', 'token', 'secret']}
            if safe_data:
                info_parts.append(f"data:{safe_data}")
        
        # GETパラメータ
        if hasattr(self.request, 'GET') and self.request.GET:
            info_parts.append(f"params:{dict(self.request.GET)}")
        
        # IPアドレス
        if hasattr(self.request, 'META'):
            ip = self.request.META.get('REMOTE_ADDR', 'unknown')
            info_parts.append(f"ip:{ip}")
        
        return " | ".join(info_parts)
    
    def log_start(self, attribute: str):
        request_info = self._get_request_info()
        if request_info:
            message = f'{attribute}の処理を開始します。 | {request_info}'
        else:
            message = f'{attribute}の処理を開始します。'
        
        # ログファイルに出力
        logger.info(message)
        # コンソールにも出力
        print(f"[INFO] {message}")
    
    def log_end(self, attribute: str):
        request_info = self._get_request_info()
        if request_info:
            message = f'{attribute}の処理を終了します。 | {request_info}'
        else:
            message = f'{attribute}の処理を終了します。'
        
        # ログファイルに出力
        logger.info(message)
        # コンソールにも出力
        print(f"[INFO] {message}")
    
    def log_error(self, attribute: str):
        request_info = self._get_request_info()
        if request_info:
            message = f'{attribute}に失敗しました。 | {request_info}'
        else:
            message = f'{attribute}に失敗しました。'
        
        # ログファイルに出力
        logger.error(message)
        # コンソールにも出力
        print(f"[ERROR] {message}")