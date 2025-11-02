import json
import re
from collections import Counter

RECIPES_FILE = 'recipes.json'
INVENTORY_FILE = 'user_inventory.json'

NEGATION_WORDS = r'(?:olmasın|i̇stemiyor(?:um)?|deği̇l|sız|siz|suz|süz|hariç|dışında|dişinda|yok)'

# Ayarlanabilir ağırlıklar
name_score = 0.6
keyword_score = 0.3
ingredients_scr = 0.1

def safe_load_json(filename, default):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def tokenize_text(s):
    # Kelime tokenleri
    return [t for t in re.findall(r'\w+', (s or "").lower()) if t]

def phrase_in_text(phrase, text_lower):
    # phrase çok kelimeli olabilir; kelime-bazlı arama yapıyoruz (tam ifade değil, fakat bu fonksiyon artık daha az kullanılıyor çünkü token bazlı eşleme yapıyoruz)
    if not phrase:
        return False
    return re.search(r'\b' + re.escape(phrase.lower()) + r'\b', text_lower) is not None

def extract_positive_negative_from_text(text, all_candidates):
    text_lower = (text or "").lower()
    positives = set()
    negatives = set()
    for cand in all_candidates:
        if not cand or not cand.strip():
            continue
        # candidate token veya tam ifade görünüyor mu deniyor
        m = re.search(r'\b' + re.escape(cand) + r'\b', text_lower)
        if m:
            # check nearby context for negation
            start = max(0, m.start() - 20)
            end = min(len(text_lower), m.end() + 20)
            context = text_lower[start:end]
            if re.search(NEGATION_WORDS, context):
                negatives.add(cand)
            else:
                positives.add(cand)
    return positives, negatives

def rank_recipes_by_text(text_input, top_n=3):
    data = safe_load_json(RECIPES_FILE, {"recipes":[]})
    recipes = data.get("recipes", [])

    text_lower = (text_input or "").lower()
    if not text_lower.strip():
        # kullanıcı text vermediyse sonuç yok
        return []


    all_candidates = set()
    for r in recipes:
        title = (r.get("title","") or "").lower().strip()
        if title:
            all_candidates.add(title)
            # title kelime tokenlarını da ekle
            for t in tokenize_text(title):
                all_candidates.add(t)
        for k in r.get("keywords", []):
            if k:
                kl = k.lower().strip()
                all_candidates.add(kl)
                for t in tokenize_text(kl):
                    all_candidates.add(t)
        for ing in r.get("ingredients", []):
            name = (ing.get("name","") or "").lower().strip()
            if name:
                all_candidates.add(name)
                for t in tokenize_text(name):
                    all_candidates.add(t)

    positive_set, negative_set = extract_positive_negative_from_text(text_input, all_candidates)

    # eşleşme yoksa boş döndür
    if not positive_set:
        return []

    scored = []
    for r in recipes:
        title = (r.get("title","") or "").strip()
        title_lower = title.lower()
        keywords = [k.lower() for k in r.get("keywords", []) if k]
        ingredients = [ing.get("name","").lower() for ing in r.get("ingredients", []) if ing.get("name")]

        # negatifse geç
        recipe_tokens = set()
        if title_lower:
            recipe_tokens.add(title_lower)
            recipe_tokens.update(tokenize_text(title_lower))
        for k in keywords:
            recipe_tokens.add(k)
            recipe_tokens.update(tokenize_text(k))
        for ing in ingredients:
            recipe_tokens.add(ing)
            recipe_tokens.update(tokenize_text(ing))
        if any(neg in recipe_tokens for neg in negative_set):
            continue

        # weight name_score

        title_tokens = tokenize_text(title_lower)
        if title_tokens:
            matched_title_tokens = sum(1 for t in title_tokens if re.search(r'\b' + re.escape(t) + r'\b', text_lower))
            title_score = matched_title_tokens / len(title_tokens)
        else:
            title_score = 0.0

        # weight keyword_score
        keyword_tokens = []
        for k in keywords:
            keyword_tokens.extend(tokenize_text(k))
        if keyword_tokens:
            matched_keyword_tokens = sum(1 for t in keyword_tokens if re.search(r'\b' + re.escape(t) + r'\b', text_lower))
            keywords_score = matched_keyword_tokens / len(keyword_tokens)
        else:
            keywords_score = 0.0

        # weight ingredients_scr
        ing_tokens = []
        for ing in ingredients:
            ing_tokens.extend(tokenize_text(ing))
        if ing_tokens:
            matched_ing_tokens = sum(1 for t in ing_tokens if re.search(r'\b' + re.escape(t) + r'\b', text_lower))
            ingredients_score = matched_ing_tokens / len(ing_tokens)
        else:
            ingredients_score = 0.0

        final_score = (title_score * name_score) + (keywords_score * keyword_score) + (ingredients_score * ingredients_scr)

        scored.append({
            "id": r.get("id",""),
            "title": title,
            "title_score": round(title_score, 3),
            "keywords_score": round(keywords_score, 3),
            "ingredients_score": round(ingredients_score, 3),
            "final_score": round(final_score, 4)
        })

    # final_score
    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:top_n]

def get_recipe_by_input(q):
    recipe_list = []
    if not q:
        return "Enter text !"

    results = rank_recipes_by_text(q)
    if not results:
        pass
    else:
        for r in results:
            recipe_list.append(r)
    return recipe_list

import json

def safe_load_json(filename, default):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def apply_ingredient_dominance(results_list, ingredients_dominance,
                               recipes_file='recipes.json',
                               inventory_file='user_inventory.json'):

    #  recipes ve inventory yükle
    recipes_data = safe_load_json(recipes_file, {"recipes": []})
    recipes_by_id = {r.get("id",""): r for r in recipes_data.get("recipes", [])}

    inv_data = safe_load_json(inventory_file, {"inventory": []})
    inventory_set = {item.get("name","").lower() for item in inv_data.get("inventory", [])}

    enriched = []
    for item in results_list:
        try:
            rid = item.get("id", "")
        except:
            pass
        recipe = recipes_by_id.get(rid)
        # Eğer id bulunamazsa başlık üzerinden arama yapmayı dene
        if recipe is None:
            # try title match
            title = item.get("title","").lower()
            for r in recipes_by_id.values():
                if (r.get("title","").lower() == title):
                    recipe = r
                    break

        if recipe is None:
            # recipe bilgisi yoksa, eksik malzeme bilinemez; adjusted_score = final_score
            missing = []
        else:
            recipe_ings = [ing.get("name","").lower() for ing in recipe.get("ingredients", []) if ing.get("name")]
            # eksikleri hesapla
            missing = [ing for ing in recipe_ings if ing not in inventory_set]

        missing_count = len(missing)
        penalty = missing_count * float(ingredients_dominance)
        orig_score = float(item.get("final_score", 0.0))
        adjusted = orig_score - penalty

        new_item = dict(item)
        new_item["missing"] = missing
        new_item["missing_count"] = missing_count
        new_item["penalty"] = round(penalty, 4)
        new_item["adjusted_score"] = round(adjusted, 4)

        enriched.append(new_item)

    # sıralama adjusted_score
    enriched.sort(key=lambda x: x["adjusted_score"], reverse=True)
    return enriched



