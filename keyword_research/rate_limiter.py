"""
Global Rate Limiter for Serper API (50 QPS)
"""

import redis
import time
from django.conf import settings


class SerperRateLimiter:
    """Rate Limiter برای Serper با Redis"""
    
    def __init__(self, max_qps=50):
        self.max_qps = max_qps
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.key = "serper_rate_limiter"
    
    def acquire(self, count=1, timeout=60):
        """
        درخواست Token برای ارسال Request
        
        Args:
            count: تعداد Request که می‌خوایم بفرستیم
            timeout: حداکثر زمان انتظار (ثانیه)
        
        Returns:
            bool: True اگه Token گرفت، False اگه Timeout شد
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Sliding Window: آخرین ثانیه رو چک می‌کنه
                now = time.time()
                window_start = now - 1.0
                
                # پاک کردن Request های قدیمی (بیش از 1 ثانیه)
                self.redis_client.zremrangebyscore(self.key, 0, window_start)
                
                # شمارش Request های فعلی
                current_count = self.redis_client.zcard(self.key)
                
                # چک کردن فضای خالی
                if current_count + count <= self.max_qps:
                    # اضافه کردن Request جدید
                    pipeline = self.redis_client.pipeline()
                    for i in range(count):
                        pipeline.zadd(self.key, {f"{now}_{i}": now})
                    pipeline.expire(self.key, 2)  # TTL: 2 ثانیه
                    pipeline.execute()
                    
                    return True
                
                # صبر کن تا فضا خالی بشه
                time.sleep(0.05)  # 50ms
            
            except Exception as e:
                print(f"❌ Rate Limiter Error: {str(e)}")
                time.sleep(0.1)
        
        return False
    
    def get_current_qps(self):
        """QPS فعلی"""
        try:
            now = time.time()
            window_start = now - 1.0
            self.redis_client.zremrangebyscore(self.key, 0, window_start)
            return self.redis_client.zcard(self.key)
        except:
            return 0