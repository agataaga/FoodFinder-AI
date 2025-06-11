# from flask import Flask, request, render_template_string
# import os
# import requests
# from dotenv import load_dotenv

# import google.generativeai as genai
# from google.generativeai.types import HarmCategory, HarmBlockThreshold

# app = Flask(__name__)

# load_dotenv()
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# chat_session = None

# def start_chat(system_prompt="Jesteś pomocnym asystentem AI."):
#     global chat_session
#     model = genai.GenerativeModel(
#         model_name="gemini-1.5-flash",
#         system_instruction=system_prompt
#     )
#     chat_session = model.start_chat(history=[])
#     return chat_session

# def send_message(message):
#     global chat_session
#     if not chat_session:
#         return "Błąd: czat nie został zainicjowany"
#     try:
#         response = chat_session.send_message(message)
#         return response.text
#     except Exception as e:
#         return f"Błąd: {str(e)}"

# # Wczytaj klucze z .env
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# # HTML template (można później przenieść do osobnego pliku)
# HTML_TEMPLATE = """
# <!DOCTYPE html>
# <html>
# <head>
#     <title>FoodFinder AI</title>
#     <style>
#         body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
#         .tab { display: none; }
#         .active { display: block; }
#         button { padding: 10px 15px; margin: 5px; cursor: pointer; }
#         textarea, select, input { width: 100%; padding: 8px; margin: 5px 0 15px; }
#     </style>
# </head>
# <body>
#     <h1>🍽️ FoodFinder AI</h1>
    
#     <button onclick="switchTab('chat')">Czat z AI</button>
#     <button onclick="switchTab('form')">Formularz</button>
    
#     <div id="chat" class="tab {% if active_tab == 'chat' %}active{% endif %}">
#         <h2>Opisz czego szukasz:</h2>
#         <form method="POST" action="/chat">
#             <textarea name="user_query" rows="4" placeholder="np. 'Szukam romantycznej restauracji z widokiem na morze w Gdyni'"></textarea>
#             <button type="submit">Szukaj</button>
#         </form>
#     </div>
    
#     <div id="form" class="tab {% if active_tab == 'form' %}active{% endif %}">
#         <h2>Wybierz preferencje:</h2>
#         <form method="POST" action="/form">
#             <input type="text" name="city" placeholder="Miasto" required>
            
#             <select name="cuisine">
#                 <option value="">Dowolna kuchnia</option>
#                 <option value="włoska">Włoska</option>
#                 <option value="azjatycka">Azjatycka</option>
#                 <option value="vegańska">Vegańska</option>
#                 <!-- Dodaj więcej opcji -->
#             </select>
            
#             <select name="price">
#                 <option value="">Dowolna cena</option>
#                 <option value="1">$ (tanie)</option>
#                 <option value="2">$$ (średnie)</option>
#                 <option value="3">$$$ (drogie)</option>
#             </select>
            
#             <label>
#                 <input type="checkbox" name="high_rating" value="1">
#                 Tylko miejsca z oceną 4.5+
#             </label>
            
#             <button type="submit">Szukaj</button>
#         </form>
#     </div>

#     <script>
#         function switchTab(tabName) {
#             document.querySelectorAll('.tab').forEach(tab => {
#                 tab.classList.remove('active');
#             });
#             document.getElementById(tabName).classList.add('active');
#         }
        
#         // Ustaw domyślną zakładkę
#         window.onload = function() {
#             const urlParams = new URLSearchParams(window.location.search);
#             const tab = urlParams.get('tab') || 'chat';
#             switchTab(tab);
#         };
#     </script>
    
#     {% if results %}
#     <div style="margin-top: 30px;">
#         <h2>Wyniki wyszukiwania:</h2>
#         {% for place in results %}
#         <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px;">
#             <h3>{{ place.name }}</h3>
#             <p>⭐ {{ place.rating }} | 📍 {{ place.address }}</p>
#             <p><a href="{{ place.url }}" target="_blank">Zobacz w Google Maps</a></p>
#             {% if place.summary %}
#             <div style="background: #f5f5f5; padding: 10px; margin-top: 10px;">
#                 <strong>Podsumowanie AI:</strong>
#                 <p>{{ place.summary }}</p>
#             </div>
#             {% endif %}
#         </div>
#         {% endfor %}
#     </div>
#     {% endif %}
# </body>
# </html>
# """

# # Funkcje do wyszukiwania (pozostają bez zmian)
# def find_restaurants(city, cuisine_type, min_rating=None, max_price=None):
#     query = f"{cuisine_type} restaurants in {city}" if cuisine_type else f"restaurants in {city}"
#     url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
#     params = {
#         "query": query,
#         "type": "restaurant",
#         "key": GOOGLE_API_KEY
#     }
#     if min_rating:
#         params["min_rating"] = min_rating
#     response = requests.get(url, params=params)
#     return response.json().get("results", [])

# def get_place_details(place_id):
#     url = "https://maps.googleapis.com/maps/api/place/details/json"
#     params = {
#         "place_id": place_id,
#         "fields": "name,rating,formatted_address,reviews,url,price_level",
#         "key": GOOGLE_API_KEY
#     }
#     response = requests.get(url, params=params)
#     return response.json().get("result", {})

# def analyze_reviews_with_gemini(reviews):
#     if not reviews:
#         return None
    
#     prompt = "Przeanalizuj opinie i podsumuj w 2 zdaniach (co chwalą, co krytykują):\n" + \
#              "\n".join(f"- {review.get('text', '')[:200]}..." for review in reviews[:5])
    
#     start_chat("Jesteś ekspertem kulinarnym analizującym opinie.")
#     return send_message(prompt)

# @app.route('/chat', methods=['GET', 'POST'])
# def chat_search():
#     if request.method == 'POST':
#         user_query = request.form['user_query']
        
#         prompt = f"Użytkownik szuka: '{user_query}'. Wyciągnij parametry w formacie JSON: city, cuisine, min_rating, price_level."
#         start_chat("Jesteś asystentem tłumaczącym zapytania na parametry wyszukiwania.")
#         response = send_message(prompt)
        
#         try:
#             params = eval(response)
#         except:
#             params = {"city": "Warszawa"}
        
#         restaurants = find_restaurants(
#             city=params.get("city", ""),
#             cuisine_type=params.get("cuisine", ""),
#             min_rating=params.get("min_rating", None)
#         )
        
#         results = []
#         for place in restaurants[:3]:
#             details = get_place_details(place["place_id"])
#             results.append({
#                 "name": details.get("name"),
#                 "rating": details.get("rating", "Brak oceny"),
#                 "address": details.get("formatted_address", "Brak adresu"),
#                 "url": details.get("url", "#"),
#                 "summary": analyze_reviews_with_gemini(details.get("reviews", []))
#             })
        
#         return render_template_string(HTML_TEMPLATE, 
#                                    active_tab='chat',
#                                    results=results)
#     return render_template_string(HTML_TEMPLATE, active_tab='chat', results=None)

# # Form route - zmodyfikowana
# @app.route('/form', methods=['GET', 'POST'])
# def form_search():
#     if request.method == 'POST':
#         city = request.form['city']
#         cuisine = request.form['cuisine']
#         price = request.form['price']
#         high_rating = request.form.get('high_rating')
        
#         restaurants = find_restaurants(
#             city=city,
#             cuisine_type=cuisine,
#             min_rating=4.5 if high_rating else None
#         )
        
#         if price:
#             filtered = []
#             for place in restaurants:
#                 details = get_place_details(place["place_id"])
#                 if str(details.get("price_level", 1)) == price:
#                     filtered.append(place)
#             restaurants = filtered
        
#         results = []
#         for place in restaurants[:3]:
#             details = get_place_details(place["place_id"])
#             results.append({
#                 "name": details.get("name"),
#                 "rating": details.get("rating", "Brak oceny"),
#                 "address": details.get("formatted_address", "Brak adresu"),
#                 "url": details.get("url", "#"),
#                 "summary": analyze_reviews_with_gemini(details.get("reviews", []))
#             })
#         print(f"Znaleziono {len(results)} wyników:")
#         for r in results:
#             print(r['name'], r['rating'])
#         return render_template_string(HTML_TEMPLATE, 
#                                    active_tab='form',
#                                    results=results)
#     return render_template_string(HTML_TEMPLATE, active_tab='form', results=None)

# # Main route
# @app.route('/')
# def home():
#     return render_template_string(HTML_TEMPLATE, active_tab='chat', results=None)

# if __name__ == '__main__':
#     app.run(debug=True)