from django.apps import AppConfig


class KeywordResearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'keyword_research'
    
    def ready(self):
        import keyword_research.signals