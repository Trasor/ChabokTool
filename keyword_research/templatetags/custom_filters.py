from django import template

register = template.Library()


@register.filter
def get_top_akw(akw_str):
    """پیدا کردن AKW با بیشترین Search Volume"""
    if not akw_str:
        return ""
    
    try:
        parts = akw_str.split(" - ")
        keyword_data = []
        
        for part in parts:
            if ":" in part:
                kw, sv = part.rsplit(":", 1)
                try:
                    keyword_data.append({"keyword": kw.strip(), "sv": int(sv)})
                except ValueError:
                    continue
        
        if keyword_data:
            # اگه همه 0 باشن، Random
            if all(item["sv"] == 0 for item in keyword_data):
                import random
                return random.choice(keyword_data)["keyword"]
            
            # بیشترین رو برگردون
            top = max(keyword_data, key=lambda x: x["sv"])
            return top["keyword"]
    except:
        pass
    
    return ""


@register.filter
def get_keywords_without_akw(akw_str):
    """حذف Search Volume و AKW از Keywords"""
    if not akw_str:
        return ""
    
    # پیدا کردن AKW
    top_akw = get_top_akw(akw_str)
    
    try:
        parts = akw_str.split(" - ")
        keywords = []
        
        for part in parts:
            if ":" in part:
                kw, _ = part.rsplit(":", 1)
                kw = kw.strip()
                
                # حذف AKW
                if kw == top_akw:
                    continue
                
                keywords.append(kw)
            else:
                part = part.strip()
                if part == top_akw:
                    continue
                keywords.append(part)
        
        return " - ".join(keywords)
    except:
        return akw_str