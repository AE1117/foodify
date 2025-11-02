This program was designed to inspire people to love cooking. Step-by-step recipes can be completed, the users inventory can be dynamically tracked, and recipe suggestions can be made based on the words typed, using rule-based artificial intelligence without an internet connection. These suggestions can also vary depending on the user. The technologies used in its development include:

    - Fronted = HTML, CSS, JS
    - Backend = Python, Flask, JSON

0.) Recipe File (recipe.json)
The application actually pulls all data from a single file and configures other files using the data it retrieves. The main database is recipes.json. This file stores recipe id, recipe name, keywords, ingredients, steps, preparation time, creator, and creation date in JSON format.
```python
{
    "id": "default-017",
    "title": "Kremalı Mantar Çorbası",
    "keywords": [
      "Çorba",
      "Mantar",
      "Kremalı",
      "Sıcak",
      "Başlangıç"
    ],
    "ingredients": [
      {"name": "Kültür Mantarı", "amount": "400 gr"},
      {"name": "Tereyağı", "amount": "2 yemek kaşığı"},
      {"name": "Un", "amount": "1 yemek kaşığı"},
      {"name": "Et Suyu", "amount": "4 su bardağı"},
      {"name": "Sıvı Krema", "amount": "200 ml"},
      {"name": "Tuz", "amount": "Gerektiği kadar"},
      {"name": "Karabiber", "amount": "Gerektiği kadar"}
    ],
    "steps": [
      {"asama_turu": "normal", "aciklama": "Mantarın yarısını küp küp doğrayın, diğer yarısını ince dilimleyin."},
      {"asama_turu": "normal", "aciklama": "Tencerede tereyağını eritin. Küp mantarları ekleyip suyunu salıp çekene kadar kavurun."},
      {"asama_turu": "normal", "aciklama": "Unu ekleyip 1 dakika daha kavurun."},
      {"asama_turu": "normal", "aciklama": "Sıcak suyu yavaş yavaş ve sürekli karıştırarak ekleyin."},
      {"asama_turu": "normal", "aciklama": "Tuz ve karabiberi ekleyin. Kaynamaya başlayınca ocağı kısın."},
      {"asama_turu": "kronometre", "kronometre_suresi": "15m", "aciklama": "Çorbayı kısık ateşte 15 dakika pişirin."},
      {"asama_turu": "normal", "aciklama": "İnce dilimlediğiniz mantarları bir tavada tereyağı ile soteleyin ve çorbaya ekleyin."},
      {"asama_turu": "normal", "aciklama": "Sıvı kremayı ekleyip karıştırın. Bir taşım kaynatıp ocaktan alın."},
      {"asama_turu": "normal", "aciklama": "Sıcak olarak servis yapın."}
    ],
    "estimated_time": "30m",
    "created_by": "system",
    "created_at": "2025-10-31T00:04:00+03:00"
  }
```
The application will only be fully functional if you provide it with enough data in this format. Other database files are as follows:

    - history.json 
    - preferences.json
    - maingrt.json 
    - user_inventory.json
    
    
    

1.) History File (history.json) :
Each time the user completes a recipe, the id number of the completed recipe is added to the "history.json" file.
```python
{
  "history": [
    "default-003",
    "default-003",
    "default-035",
    "default-035",
    "default-034",
    "default-015",
    "default-030"
  ]
}
```

2.) Learning userss likes (preferences.json) :
Each time a user completes a recipe, the keywords for that recipe are added to the "preferences.json" file. These keywords are kept as a counter. If different recipes have the same keywords, the counter for those keywords is incremented, allowing the user to determine their preferences.
```python
{
  "preferences": {
    "Sebze": 4,
    "Ana Yemek": 20,
    "Tuzlu": 4,
    "Hafif": 7,
    "Enginar": 2,
    "Köfte": 1,
    "Ekmek": 1,
    "Kırmızı Et": 1
  }
}
```

3.)Ingredients used in recipes (maingrt.json) : 
When the "malzemeleri yenile" button on the "add_to_inventory.html" page is clicked, the addable ingredients (ingredients in the recipes.json file) are automatically loaded into the "maingrt.json" file, and duplicate ingredients are filtered. The user can select ingredients from here and add them to their inventory.
```python
{
  "ingredients": [
    {
      "name": "Krema"
    },
    {
      "name": "Bayat Ekmek"
    },
    {
      "name": "Kıyma"
    },
    {
      "name": "Enginar"
    },
    {
      "name": "Tereyağı"
    },
    {
      "name": "Yumurta Sarısı"
    }
  ]
}
```

4.) User inventory (user_inventory.json) :
User inventory to show how much ingredients are missing to copmete the recipe.

```python
{
  "inventory": [
    {
      "name": "Krema",
      "amount": "1 adet"
    },
    {
      "name": "Bayat Ekmek",
      "amount": "1 adet"
    },
    {
      "name": "İrmik",
      "amount": "1 adet"
    },
    {
      "name": "Karabiber",
      "amount": "1 adet"
    }
  ]
}
```

--------------------------------------------------

Main file (test.py) :

This file is managing HTML files with flask. I preferred to make a dynamic web interface to reduce memory. You can man make unlimited recipes with only 5 JSON and 7 HTML files. Files are chanceing dynamicly based to "recipes.json"

--------------------------------------------------

AI file (food_ai.py) :
This code parses the users text to determine what kind of food they want, matching it with the recipe data. It then recalculates these scores, taking into account the users available ingredients.

The program first securely loads the recipe "recipes.json" and the users available ingredient list "user_inventory.json" if the files are missing or corrupted, the default empty structure is used.

During the text processing phase, the words in the users sentence are converted to lowercase and simplified, and all possible word candidates in the recipes (title, keyword, ingredient names) are collected into a pool. This pool is then used to determine which words to include in users sentence. Furthermore, this method categorizes words containing negative connotations (e.g., "değil",  "-sız", "istemiyorum", "hariç") as negative. Thus, if the user types "soğansız", the recipe containing "soğan" is automatically eliminated.

The recipe is then examined individually. Each recipe's title, keywords, and ingredients are matched with the user's text. A score is calculated for each section based on the likelihood of matching words, and these scores are combined with specific weights to create the overall score for that recipe. Title matches carry the highest weight, while keywords and features carry lower weights.

As a result of this process, the top-scoring few recipes are selected. However, this is a preliminary ranking based solely on the text. The second stage then begins: re-evaluating the features of the descriptions. This involves applying the rules of the recipe to the existing ingredients, identifying any missing ingredients, and applying a penalty point for each missing ingredient. This penalty is deducted from the recipe's previous score, resulting in a new value called the "adjusted_score."

In the final stage, the recipe is re-ranked based on these adjusted scores. This allows the program to maximize both the information and the user-friendly features available.

--------------------------------------------------

HTML files (index.html, profile.html, inventory.html, add_to_inventory.html, recipe.html, steps.html, ai_assistant.html) :

Just HTML files with bunch of JS codes. 



© 2025 All rights to this code owned by Murad Anıl Kurt
