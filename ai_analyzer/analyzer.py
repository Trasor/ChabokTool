"""
Main AI Analyzer
"""

from django.conf import settings
from keyword_research.models import Keyword
import time


def get_ai_provider():
    """انتخاب Provider"""
    from .providers import GeminiProvider, GPTProvider, ClaudeProvider
    
    provider_name = getattr(settings, 'AI_PROVIDER', 'gemini')
    
    if provider_name == 'gemini':
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        return GeminiProvider(api_key)
    
    elif provider_name == 'gpt':
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        return GPTProvider(api_key)
    
    elif provider_name == 'claude':
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        return ClaudeProvider(api_key)
    
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")


def analyze_all_pkw(research_request, worker_name="", task_id_short=""):
    """تحلیل همه PKW ها"""
    
    if not getattr(settings, 'AI_ENABLED', False):
        print(f"[{worker_name}] [{task_id_short}] ⚠️ AI disabled")
        return
    
    try:
        provider = get_ai_provider()
    except Exception as e:
        print(f"[{worker_name}] [{task_id_short}] ❌ Provider init failed: {str(e)}")
        return
    
    pkw_keywords = Keyword.objects.filter(request=research_request, status=1).order_by('id')
    total_pkw = pkw_keywords.count()
    
    print(f"[{worker_name}] [{task_id_short}] 🤖 AI Analysis: {total_pkw} PKW")
    
    ai_start_time = time.time()
    
    for index, pkw in enumerate(pkw_keywords, 1):
        try:
            keyword = pkw.keyword
            
            if pkw.links and pkw.links != "خطا":
                links = pkw.links.split(" -------------- ")[:10]
            else:
                links = []
            
            if not links:
                print(f"[{worker_name}] [{task_id_short}] ⚠️ [{index}/{total_pkw}] No links: {keyword}")
                pkw.search_intent = "N/A"
                pkw.intent_mapping = "N/A"
                pkw.save()
                continue
            
            print(f"[{worker_name}] [{task_id_short}] 🤖 [{index}/{total_pkw}] {keyword}")
            
            search_intent, intent_mapping = provider.analyze(keyword, links, [])
            
            pkw.search_intent = search_intent
            pkw.intent_mapping = intent_mapping
            pkw.save()
            
            print(f"[{worker_name}] [{task_id_short}] ✅ {search_intent} | {intent_mapping}")
            
            # Rate Limit
            delay = getattr(settings, 'AI_RATE_LIMIT_DELAY', 4)
            time.sleep(delay)
        
        except Exception as e:
            print(f"[{worker_name}] [{task_id_short}] ❌ {keyword}: {str(e)}")
            pkw.search_intent = "N/A"
            pkw.intent_mapping = "N/A"
            pkw.save()
    
    ai_duration = time.time() - ai_start_time
    print(f"[{worker_name}] [{task_id_short}] 🤖 Completed in {ai_duration:.2f}s")