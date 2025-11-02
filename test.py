from flask import Flask, render_template, jsonify, abort, request
import json
import os
from food_ai import get_recipe_by_input, apply_ingredient_dominance


app = Flask(__name__)

def load_recipes():
    with open("recipes.json", "r", encoding="utf-8") as f:
        return json.load(f)["recipes"]

def load_inventory():
    with open("user_inventory.json", "r", encoding="utf-8") as f:
        return json.load(f)["inventory"]

@app.route("/")
def home():
    recipes = load_recipes()
    inventory = load_inventory()

    # tarif kt
    for recipe in recipes:
        total_ingredients = len(recipe["ingredients"])
        available_count = 0
        for ing in recipe["ingredients"]:
            for item in inventory:
                if ing["name"] == item["name"]:
                    available_count += 1
                    break
        recipe["percent_available"] = int((available_count / total_ingredients) * 100)

    # malzeme sıraama
    recipes_sorted = sorted(recipes, key=lambda x: x["percent_available"], reverse=True)

    return render_template("index.html", recipes=recipes_sorted, inventory=inventory)

# Profil sayfası
@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/recipe/<recipe_id>")
def recipe_detail(recipe_id):
    recipes = load_recipes()  # tarifleri çek
    for recipe in recipes:
        if recipe.get("id") == recipe_id:
            return render_template("recipe.html", recipe=recipe)
    abort(404)

@app.route("/steps/<recipe_id>")
def recipe_steps(recipe_id):
    recipes = load_recipes()
    for recipe in recipes:
        if recipe.get("id") == recipe_id:
            return render_template("steps.html", recipe=recipe)
    abort(404)



@app.route("/add_to_history/<recipe_id>", methods=["POST"])
def add_to_history(recipe_id):
    """
    1) history.json'a recipe_id ekler.
    2) recipes.json içinden recipe_id'yi bulursa, recipe['keywords'] listesindeki
       anahtarlar için preferences.json içindeki sayaçları arttırır, yoksa ekler.
    """
    HISTORY_FILE = "history.json"
    PREFS_FILE = "preferences.json"


    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"history": []}, f, ensure_ascii=False, indent=2)

    try:
        # read current history (koruma: bozuk içerik varsa sıfırla)
        with open(HISTORY_FILE, "r+", encoding="utf-8") as f:
            try:
                history_data = json.load(f)
                if not isinstance(history_data, dict) or "history" not in history_data:
                    history_data = {"history": []}
            except json.JSONDecodeError:
                history_data = {"history": []}


            history_data["history"].append(recipe_id)

            f.seek(0)
            json.dump(history_data, f, ensure_ascii=False, indent=2)
            f.truncate()
    except Exception as e:
        return jsonify({"status": "error", "message": f"history write error: {e}"}), 500


    try:
        # tarif bilgilerini yukarıdaki load_recipes() fonksiyonu ile al
        recipes = load_recipes()
        recipe_obj = None
        for r in recipes:
            if r.get("id") == recipe_id:
                recipe_obj = r
                break

        # geri uyumluluk
        keywords = []
        if recipe_obj:
            # prefer 'keywords' (geri uyumluluk için tastes yoksa keywords kontrolü)
            keywords = recipe_obj.get("keywords") or recipe_obj.get("tastes") or []
            if not isinstance(keywords, list):
                keywords = []

        # preferences.json yoksa oluştur
        if not os.path.exists(PREFS_FILE):
            with open(PREFS_FILE, "w", encoding="utf-8") as f:
                json.dump({"preferences": {}}, f, ensure_ascii=False, indent=2)

        # Oku ve güncelle
        with open(PREFS_FILE, "r+", encoding="utf-8") as f:
            try:
                prefs_data = json.load(f)
                if not isinstance(prefs_data, dict) or "preferences" not in prefs_data:
                    prefs_data = {"preferences": {}}
            except json.JSONDecodeError:
                prefs_data = {"preferences": {}}

            # keywords listesi üzerinden sayaçları artır
            for kw in keywords:
                if not isinstance(kw, str):
                    continue
                key = kw.strip()
                if key == "":
                    continue
                current = prefs_data["preferences"].get(key, 0)
                prefs_data["preferences"][key] = current + 1

            # yaz
            f.seek(0)
            json.dump(prefs_data, f, ensure_ascii=False, indent=2)
            f.truncate()

    except Exception as e:
        return jsonify({"status": "error", "message": f"preferences write error: {e}"}), 500

    return jsonify({"status": "ok"})

@app.route("/get_history")
def get_history():
    HISTORY_FILE = "history.json"
    if not os.path.exists(HISTORY_FILE):
        return jsonify({"history": []})
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return jsonify({"history": data.get("history", [])})
        except:
            return jsonify({"history": []})

@app.route("/inventory")
def inventory_page():
    return render_template("inventory.html")

@app.route("/get_inventory")
def get_inventory():
    INVENTORY_FILE = "user_inventory.json"
    if not os.path.exists(INVENTORY_FILE):
        return jsonify({"inventory": []})
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return jsonify({"inventory": data.get("inventory", [])})
        except:
            return jsonify({"inventory": []})


@app.route("/remove_from_inventory/<item_name>", methods=["POST"])
def remove_from_inventory(item_name):
    INVENTORY_FILE = "user_inventory.json"
    try:
        with open(INVENTORY_FILE, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict) or "inventory" not in data:
                    data = {"inventory": []}
            except json.JSONDecodeError:
                data = {"inventory": []}

            # ögeyi filtrele
            original_len = len(data["inventory"])
            data["inventory"] = [i for i in data["inventory"] if i["name"] != item_name]

            if len(data["inventory"]) == original_len:
                return jsonify({"status":"error", "message":"Öğe bulunamadı"}), 404

            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()

        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500


@app.route("/add_to_inventory_item/<item_name>", methods=["POST"])
def add_to_inventory_item(item_name):
    INVENTORY_FILE = "user_inventory.json"

    if not os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"inventory": []}, f, ensure_ascii=False, indent=2)

    try:
        with open(INVENTORY_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            # Aynı isim yoksa ekle
            if not any(i["name"]==item_name for i in data["inventory"]):
                data["inventory"].append({"name": item_name, "amount": "1 adet"})
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
    except Exception as e:
        return jsonify({"status":"error", "message":str(e)}), 500

    return jsonify({"status":"ok"})

@app.route("/add_to_inventory", methods=["GET"])
def add_to_inventory_page():
    # Envanteri ve tüm malzemeleri yükle
    with open("user_inventory.json", "r", encoding="utf-8") as f:
        inventory = json.load(f)["inventory"]
    inventory_names = [item["name"] for item in inventory]

    with open("maingrt.json", "r", encoding="utf-8") as f:
        all_items = json.load(f)["ingredients"]

    # Kullanıcıda olmayanları listele
    available_items = [item for item in all_items if item["name"] not in inventory_names]

    return render_template("add_to_inventory.html", items=available_items)

@app.route("/refresh_ingredients", methods=["POST"])
def refresh_ingredients():
    import json, os

    RECIPES_FILE = "recipes.json"
    MAINGRT_FILE = "maingrt.json"

    # 1) recipes.json'dan tüm malzemeleri çek
    try:
        with open(RECIPES_FILE, "r", encoding="utf-8") as f:
            recipes = json.load(f).get("recipes", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"status": "error", "message": "recipes.json okunamadı"}), 500

    new_ingredients = set()
    for r in recipes:
        for ing in r.get("ingredients", []):
            name = ing.get("name", "").strip()
            if name:
                new_ingredients.add(name)

    # 2) maingrt.json'ı aç ve mevcut malzemeleri al
    existing_ingredients = set()
    if os.path.exists(MAINGRT_FILE):
        try:
            with open(MAINGRT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("ingredients", []):
                    existing_ingredients.add(item.get("name", "").strip())
        except (json.JSONDecodeError, FileNotFoundError):
            data = {"ingredients": []}
    else:
        data = {"ingredients": []}

    # 3) yeni malzemeleri ekle, tekrarlayanları filitrele
    to_add = new_ingredients - existing_ingredients
    for name in to_add:
        data["ingredients"].append({"name": name})

    # 4) maingrt.json dosyasına yaz
    try:
        with open(MAINGRT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Dosya yazılamadı: {e}"}), 500

    return jsonify({"status": "ok", "added": list(to_add)})

# AI Assistant sayfası
@app.route("/ai_assistant")
def ai_assistant():
    return render_template("ai_assistant.html")


@app.route("/ai_assistant")
def ai_assistant_page():
    # ai_assistant.html render eder
    return render_template("ai_assistant.html")


@app.route("/ai_query", methods=["POST"])
def ai_query():
    """
    JSON body: { "text": "kullanıcı mesajı" }
    Döner: { recipe_list: [...], dominanced_list: [...] }
    """
    try:
        body = request.get_json(force=True) or {}
        text = (body.get("text") or "").strip()
        if text == "":
            return jsonify({"status": "error", "message": "Metin boş."}), 400

        # 1) Eşleşen tarifleri al
        try:
            recipe_list = get_recipe_by_input(text)
            if not isinstance(recipe_list, list):
                recipe_list = list(recipe_list) if recipe_list is not None else []
        except Exception as e:
            return jsonify({"status": "error", "message": f"get_recipe_by_input hata: {e}"}), 500

        # 2) malzeme ağırlığı uygulayıp yeni skorları al
        try:
            dominanced_list = apply_ingredient_dominance(results_list=recipe_list, ingredients_dominance=0.2)
            if not isinstance(dominanced_list, list):
                dominanced_list = list(dominanced_list) if dominanced_list is not None else []
        except Exception as e:
            # Eğer apply başarısız olursa, yine recipe_list'i döndürür ama dominanced_list boş olur
            dominanced_list = []
            app.logger.exception("apply_ingredient_dominance hatası: %s", e)

        # Başarılı cevap
        return jsonify({
            "status": "ok",
            "recipe_list": recipe_list,
            "dominanced_list": dominanced_list
        })
    except Exception as e:
        app.logger.exception("ai_query genel hata: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
