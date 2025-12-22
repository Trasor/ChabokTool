"""
سرویس‌های مربوط به Serper API و ردیابی رتبه
"""
import requests
import logging
from urllib.parse import urlparse
from django.conf import settings

logger = logging.getLogger(__name__)


class SerperService:
    """
    سرویس ارتباط با Serper.dev API برای دریافت نتایج Google
    """
    API_KEY = '7ff1399efdf110530fed64f3742ed477de59e8e2'
    BASE_URL = 'https://google.serper.dev/search'

    def __init__(self):
        self.api_key = self.API_KEY

    def get_rank(self, keyword, target_domain):
        """
        پیدا کردن رتبه یک دامنه برای یک کلمه کلیدی

        Args:
            keyword (str): کلمه کلیدی جستجو
            target_domain (str): دامنه هدف (مثال: digikala.com)

        Returns:
            int or None: رتبه (1-100) یا None اگر پیدا نشد
        """
        try:
            payload = {
                "q": keyword,
                "gl": "ir",      # کشور: ایران
                "hl": "fa",      # زبان: فارسی
                "num": 100       # تعداد نتایج: 100 (با 1 کردیت!)
            }

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            response = requests.post(
                self.BASE_URL,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"✗ Serper API error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            rank = self._find_domain_in_results(data, target_domain)

            if rank:
                logger.info(f"✓ Found '{target_domain}' at rank {rank} for keyword '{keyword}'")
            else:
                logger.warning(f"⚠ Domain '{target_domain}' not found in top 100 for '{keyword}'")

            return rank

        except requests.exceptions.Timeout:
            logger.error(f"✗ Timeout while searching for '{keyword}'")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Request error for '{keyword}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"✗ Unexpected error for '{keyword}': {str(e)}")
            return None

    def _find_domain_in_results(self, results, target_domain):
        """
        پیدا کردن دامنه در نتایج organic

        Args:
            results (dict): پاسخ JSON از Serper
            target_domain (str): دامنه هدف

        Returns:
            int or None: رتبه (1-100) یا None
        """
        organic_results = results.get('organic', [])

        # نرمال‌سازی دامنه هدف
        target_domain_clean = target_domain.lower().replace('www.', '').strip()

        for index, result in enumerate(organic_results, start=1):
            link = result.get('link', '')
            if not link:
                continue

            # استخراج دامنه از URL
            try:
                parsed = urlparse(link)
                result_domain = parsed.netloc.lower().replace('www.', '')

                # مقایسه دامنه‌ها
                if target_domain_clean in result_domain or result_domain in target_domain_clean:
                    return index

            except Exception as e:
                logger.warning(f"⚠ Failed to parse URL '{link}': {str(e)}")
                continue

        return None

    def get_bulk_ranks(self, keywords_dict):
        """
        دریافت رتبه برای چندین کلمه کلیدی به صورت یکجا

        Args:
            keywords_dict (dict): دیکشنری {keyword: target_domain}

        Returns:
            dict: {keyword: rank}
        """
        results = {}
        for keyword, domain in keywords_dict.items():
            rank = self.get_rank(keyword, domain)
            results[keyword] = rank
        return results


class RankService:
    """
    سرویس‌های مدیریت رتبه و آپدیت پروژه‌ها
    """

    def __init__(self):
        self.serper = SerperService()

    def update_project_ranks(self, project):
        """
        آپدیت رتبه تمام کلمات کلیدی یک پروژه

        Args:
            project: RankProject instance

        Returns:
            dict: نتیجه آپدیت
        """
        from .models import RankProject
        import time

        # بررسی محدودیت ماهانه
        project.check_and_reset_monthly_counter()

        if not project.can_update:
            return {
                'status': 'failed',
                'error': 'محدودیت 4 آپدیت در ماه به پایان رسیده است.'
            }

        keywords = project.keywords.all()
        if not keywords.exists():
            return {
                'status': 'failed',
                'error': 'پروژه هیچ کلمه کلیدی ندارد.'
            }

        updated_count = 0
        failed_count = 0

        for keyword in keywords:
            try:
                # تاخیر 200ms بین هر request (برای جلوگیری از Rate Limit)
                time.sleep(0.2)

                # دریافت رتبه از Serper
                rank = self.serper.get_rank(keyword.keyword, project.target_domain)

                # آپدیت کلمه کلیدی
                keyword.update_rank(rank)
                updated_count += 1

            except Exception as e:
                logger.error(f"✗ Failed to update keyword '{keyword.keyword}': {str(e)}")
                failed_count += 1
                continue

        # آپدیت پروژه
        from django.utils import timezone
        project.update_count_current_month += 1
        project.last_update_at = timezone.now()
        project.save(update_fields=['update_count_current_month', 'last_update_at'])

        return {
            'status': 'success',
            'updated': updated_count,
            'failed': failed_count,
            'total': keywords.count()
        }
