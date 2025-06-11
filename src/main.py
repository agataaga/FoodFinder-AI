import os
from re import search
import sys
import json
import logging
from typing import Dict, List, Optional, Any

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bs4 import BeautifulSoup
from flask import Flask, send_from_directory, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import google.generativeai as genai

from .models.user import db
from .routes.user import user_bp

# Ładowanie zmiennych środowiskowych
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Włączenie CORS
CORS(app)

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguracja Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY nie jest ustawiony w pliku .env")
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY nie jest ustawiony w pliku .env")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app.register_blueprint(user_bp, url_prefix='/api')

# Konfiguracja bazy danych (opcjonalna)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

    class RestaurantAI:
    
        def __init__(self):
            self.model = None
            self.extractor_model = None  # Nowy model do ekstrakcji parametrów
        
            if GEMINI_API_KEY:
                try:
                    # Główny model do ogólnych interakcji
                    self.model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction="Jesteś ekspertem kulinarnym i asystentem do wyszukiwania restauracji. Odpowiadaj w języku polskim."
                    )
                    # Specjalistyczny model do ekstrakcji parametrów
                    self.extractor_model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction="""Jesteś specjalistą od ekstrakcji parametrów wyszukiwania restauracji. 
                        Twoim zadaniem jest precyzyjne wyciąganie informacji z wypowiedzi użytkownika i zwracanie 
                        ich w ściśle określonym formacie JSON. Dla miast używaj formy mianownika (np. „Toruń” zamiast „w Toruniu”). Zastosuj tą logikę dla wszystkich parametrów. 
                        Odpowiadasz TYLKO w formacie JSON. Odpowiedż ma zawierać tylko wymagane pola, żadnych innych zbędnych słów na początku i na końcu"""
                    )
                except Exception as e:
                    logger.error(f"Błąd inicjalizacji modelu Gemini: {e}")
        
        def extract_search_params(self, query: str) -> Dict[str, Any]:
            """Ekstrakcja parametrów wyszukiwania przy użyciu specjalistycznego modelu"""
            if not self.extractor_model:
                return self._get_default_params()
            
            prompt = f"""
            Przeanalizuj dokładnie następujące zapytanie użytkownika i wyciągnij wszystkie możliwe parametry wyszukiwania restauracji.
            Jeśli jakiś parametr nie jest podany, ustaw wartość na null.
            
            Zapytanie: "{query}"
            
            Zwróć TYLKO poprawny JSON z następującymi polami:
            - city: nazwa miasta (string lub null)
            - cuisine: typ kuchni (string lub null)
            - min_rating: minimalna ocena 1-5 (number lub null)
            - price_level: poziom cen 1-4 (number lub null, gdzie 1=tanie, 4=bardzo drogie)
            - occasion: okazja (string: "romantyczna", "rodzinna", "biznesowa", "nieformalna" lub null)
            - amenities: udogodnienia (string: "wifi", "parking", "dostawa", "na_wynos", "ogródek" lub null)
            
            Przykłady:
            - "Szukam dobrej pizzerii w Warszawie" → {{"city": "Warszawa", "cuisine": "pizza", "min_rating": null, "price_level": null, "occasion": null, "amenities": null}}
            - "Romantyczna restauracja z widokiem na morze w Trójmieście" → {{"city": "Trójmiasto", "cuisine": null, "min_rating": null, "price_level": null, "occasion": "romantyczna", "amenities": null}}
            """
            
            try:
                response = self.extractor_model.generate_content(prompt)
                response_text = self._extract_response_text(response)
                
                logger.debug(f"Odpowiedź modelu (surowa): {response_text}")
                print(response_text)
               
                # Parsowanie JSON z walidacją
                result = json.loads(response_text)
                return result
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Błąd ekstrakcji parametrów: {e}")
                return self._get_default_params()
        
        def _extract_response_text(self, response) -> str:
            """Ekstrakcja i oczyszczenie tekstu z odpowiedzi modelu"""
            if hasattr(response, 'text'):
                text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                text = response.candidates[0].content.parts[0].text.strip()
            else:
                return ""

            # Usuwanie bloków markdown, jeśli występują
            if text.startswith("```json"):
                text = text.removeprefix("```json").strip()
            if text.endswith("```"):
                text = text.removesuffix("```").strip()
            return text

        
        
        def _get_default_params(self) -> Dict:
            """Domyślne parametry wyszukiwania"""
            return {
                "city": "Warszawa",
                "cuisine": None,
                "min_rating": None,
                "price_level": None,
                "occasion": None,
                "amenities": None
            }
        
        def parse_user_query(self, query: str) -> Dict[str, Any]:
            """Parsuje zapytanie użytkownika używając specjalistycznego modelu ekstrakcji"""
            return self.extract_search_params(query)
        
        def analyze_reviews(self, reviews: List[Dict]) -> Optional[str]:
            """Analizuje opinie o restauracji"""
            if not self.model or not reviews:
                return None
            
            review_texts = []
            for review in reviews[:5]:
                text = review.get('text', '')[:200]
                if text:
                    review_texts.append(f"- {text}...")
            
            if not review_texts:
                return None
            
            prompt = f"""
            Przeanalizuj następujące opinie o restauracji i napisz krótkie podsumowanie w 2-3 zdaniach.
            Skoncentruj się na tym, co goście chwalą i co krytykują.
            
            Opinie:
            {chr(10).join(review_texts)}
            
            Odpowiedz po polsku:
            """
            
            try:
                response = self.model.generate_content(prompt)
                return self._extract_response_text(response)
            except Exception as e:
                logger.error(f"Błąd analizy opinii: {e}")
                return None
            
        def find_expert_recommendation(self, city: str, cuisine: str) -> Optional[Dict[str, str]]:
            """Wyszukuje ekspercką rekomendację restauracji na blogach kulinarnych. Pamiętaj że miasto podane w argumencie musi zgadzać sie z tym w restauracji, tak samo jak typ kuchni"""
            try:
                food_blogs = [
                "https://eatzon.pl/blog/ranking-restauracji-polska/",
                "https://pyzamadeinpoland.pl/category/recenzje/",
                "https://www.mojapasjasmaku.pl/category/recenzje-restauracji/",
                "https://eatzon.pl/blog/ranking-restauracji-poznan/",
                "https://foodokracja.pl/najlepsze-restauracje-w-warszawie/",
                

    ]
            except Exception as e:
                logger.error(f"Błąd wyszukiwania Google: {e}")
                return None

            for url in food_blogs:
                try:
                    headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    response.raise_for_status()  # Raise exception for bad status codes
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.decompose()
                        
                    article_text = soup.get_text(separator="\n", strip=True)
                    

                    prompt = f"""
                    Przeanalizuj poniższy tekst z bloga kulinarnego i znajdź rekomendacje dokładnie 1 restauracji spełniające KONKRETNIE następujące kryteria:
                    - Typ kuchni: {cuisine}
                     - Lokalizacja: {city}
                    Jeśli nie ma takich informacji, odpowiedź null. Jeśli w tekście pojawia się kilka restauracji, wybierz jedną pasującą do miasta i do kuchni i zwróć jej nazwę i miasto.

                    Artykuł:
                    {article_text[:4000]}  # Ograniczenie do 4000 znaków

                    Odpowiedź w formacie JSON:
                    {{
                        "name": "...",
                        "summary": "...",
                        "source": "{url}"
                    }}
                    Jeśli nie znalazłeś żadnej restauracji, zwróć null.
                    """
                    
                    response = self.model.generate_content(prompt)
                    extracted = self._extract_response_text(response)
                    
                    # Skip if response is empty or null
                    if not extracted or extracted.lower() == "null":
                        continue
                        
                    result = json.loads(extracted)
                    
                    # Validate the result has required fields
                    if result and isinstance(result, dict) and result.get("name"):                        
                        return result
                        
                except json.JSONDecodeError:
                    logger.warning(f"Nie można przetworzyć odpowiedzi JSON z {url}")
                    continue
                except requests.RequestException as e:
                    logger.warning(f"Błąd pobierania {url}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Nieoczekiwany błąd przetwarzania {url}: {e}")
                    continue

            logger.info("Nie znaleziono żadnych rekomendacji w analizowanych źródłach")
            return None
        


    class GooglePlacesAPI:
        """Klasa do obsługi Google Places API"""
        
        def __init__(self, api_key: str):
            self.api_key = api_key
        
        def search_restaurants(self, city: str, cuisine_type: str = "", min_rating: float = None, 
                            occasion: str = "", amenities: str = "") -> List[Dict]:
            """Wyszukuje restauracje w danym mieście z dodatkowymi filtrami"""
            if not self.api_key:
                logger.error("Google API Key nie jest dostępny")
                return []
            
            # Budowanie zapytania z dodatkowymi parametrami
            query_parts = []
            if cuisine_type:
                query_parts.append(cuisine_type)
            
            # Dodanie okazji do zapytania
            if occasion:
                occasion_keywords = {
                    "romantyczna": "romantic",
                    "rodzinna": "family friendly",
                    "biznesowa": "business",
                    "nieformalna": "casual"
                }
                query_parts.append(occasion_keywords.get(occasion, occasion))
            
            # Dodanie udogodnień do zapytania
            if amenities:
                amenities_keywords = {
                    "wifi": "wifi",
                    "parking": "parking",
                    "dostawa": "delivery",
                    "na_wynos": "takeout",
                    "ogródek": "outdoor seating"
                }
                query_parts.append(amenities_keywords.get(amenities, amenities))
            
            query_parts.append("restaurants")
            query_parts.append(f"in {city}")
            
            query = " ".join(query_parts)
            
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": query,
                "type": "restaurant",
                "key": self.api_key
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                
                # Filtrowanie po ocenie jeśli podano
                if min_rating:
                    results = [r for r in results if r.get("rating", 0) >= min_rating]
                
                return results
            except requests.RequestException as e:
                logger.error(f"Błąd wyszukiwania restauracji: {e}")
                return []

    
        def find_hidden_gems(self, restaurants: List[Dict]) -> List[Dict]:
            """Znajduje 'perełki' - restauracje z małą liczbą opinii ale wysoką oceną"""
            hidden_gems = []

            ratings = [r.get("rating", 0) for r in restaurants if r.get("rating") is not None]
            average_rating = sum(ratings) / len(ratings) if ratings else 0
            
            for restaurant in restaurants:
                rating = restaurant.get("rating", 0)
                user_ratings_total = restaurant.get("user_ratings_total", 0)
                
                # Kryteria dla perełek:
                # - Ocena >= 4.3
                # - Liczba opinii między 10 a 100 (nie za mało, nie za dużo)
                # - Wyższa ocena niż średnia w okolicy
                if (rating >= 4.0 and 
                    10 <= user_ratings_total <= 500 and rating > average_rating):
                    hidden_gems.append(restaurant)
            
            # Sortowanie po ocenie (malejąco) i liczbie opinii (rosnąco)
            hidden_gems.sort(key=lambda x: (-x.get("rating", 0), x.get("user_ratings_total", 0)))
            
            return hidden_gems
        
        def get_place_details(self, place_id: str) -> Dict:
            """Pobiera szczegóły miejsca"""
            if not self.api_key:
                return {}
            
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": place_id,
                "fields": "name,rating,formatted_address,reviews,url,price_level,photos",
                "key": self.api_key
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                return data.get("result", {})
            except requests.RequestException as e:
                logger.error(f"Błąd pobierania szczegółów miejsca: {e}")
                return {}

# Inicjalizacja serwisów
restaurant_ai = RestaurantAI()
places_api = GooglePlacesAPI(GOOGLE_API_KEY) if GOOGLE_API_KEY else None


@app.route('/chat', methods=['GET', 'POST'])
def chat_search():
    """Endpoint dla wyszukiwania przez czat z AI"""
    if request.method == 'POST':
        try:
            user_query = request.form.get('user_query', '').strip()
            if not user_query:
                return render_template('index.html', 
                                    active_tab='chat',
                                    error="Proszę wprowadzić zapytanie")
            
            if not places_api:
                return render_template('index.html',
                                    active_tab='chat',
                                    error="Google Places API nie jest skonfigurowane")
            
            # Parsowanie zapytania przez specjalistyczny model AI
            params = restaurant_ai.parse_user_query(user_query)
            logger.info(f"Parametry z AI: {params}")
            
            # Wyszukiwanie restauracji z wszystkimi parametrami
            restaurants = places_api.search_restaurants(
                city=params.get("city", ""),
                cuisine_type=params.get("cuisine"),
                min_rating=params.get("min_rating"),
                occasion=params.get("occasion"),
                amenities=params.get("amenities")
            )
            
            # Filtrowanie po cenie jeśli podano
            price_level = params.get("price_level")
            if price_level and restaurants:
                restaurants = [place for place in restaurants 
                             if places_api.get_place_details(place["place_id"]).get("price_level") == price_level]
            
            # Przygotowanie wyników (ograniczenie do 5)
            results = []
            for place in restaurants[:8]:
                details = places_api.get_place_details(place["place_id"])
                
                result = {
                    "name": details.get("name", "Nieznana nazwa"),
                    "rating": details.get("rating", "Brak oceny"),
                    "address": details.get("formatted_address", "Brak adresu"),
                    "url": details.get("url", "#"),
                    "price_level": details.get("price_level"),
                    "summary": restaurant_ai.analyze_reviews(details.get("reviews", []))
                }
                results.append(result)
            
            logger.info(f"Znaleziono {len(results)} restauracji")
            print(params)
            city = params.get("city")
            cuisine = params.get("cuisine")

            expert_result = restaurant_ai.find_expert_recommendation(city=city, cuisine=cuisine)

            if expert_result:
                results.insert(0, {
                "name": expert_result["name"],
                "rating": None,
                "formatted_address": "Ekspercka rekomendacja",
                "review_summary": expert_result["summary"],
                "source": expert_result["source"],
                "is_expert_pick": True
            })

            return render_template('index.html', 
                                active_tab='chat',
                                results=results,
                                search_params=params)  # Możesz przekazać parametry do widoku
                                   
        except Exception as e:
            logger.error(f"Błąd w chat_search: {e}")
            return render_template('index.html',
                                active_tab='chat',
                                error=f"Wystąpił błąd: {str(e)}")
    
    return render_template('index.html', active_tab='chat')

@app.route('/form', methods=['GET', 'POST'])
def form_search():
    """Endpoint dla wyszukiwania przez formularz"""
    if request.method == 'POST':
        try:
            city = request.form.get('city', '').strip()
            cuisine = request.form.get('cuisine', '').strip()
            price = request.form.get('price', '').strip()
            occasion = request.form.get('occasion', '').strip()
            amenities = request.form.get('amenities', '').strip()
            high_rating = request.form.get('high_rating')
            hidden_gems = request.form.get('hidden_gems')
            
            if not city:
                return render_template('index.html', 
                                           active_tab='form',
                                           error="Proszę podać miasto")
            
            if not places_api:
                return render_template('index.html', 
                                           active_tab='form',
                                           error="Google Places API nie jest skonfigurowane")
            
            
            
            
            # Wyszukiwanie restauracji z nowymi parametrami
            min_rating = 4.5 if high_rating else None
            restaurants = places_api.search_restaurants(
                city=city,
                cuisine_type=cuisine,
                min_rating=min_rating,
                occasion=occasion,
                amenities=amenities
            )
            # Jeśli wybrano "szukaj perełek", filtruj wyniki
            if hidden_gems:
                print(len(restaurants))
                restaurants = places_api.find_hidden_gems(restaurants)
                logger.info(f"Znaleziono {len(restaurants)} perełek")
                print(len(hidden_gems))

            # Filtrowanie po cenie
            if price:
                try:
                    price_level = int(price)
                    filtered_restaurants = []
                    for place in restaurants:
                        details = places_api.get_place_details(place["place_id"])
                        if details.get("price_level") == price_level:
                            filtered_restaurants.append(place)
                    restaurants = filtered_restaurants
                except ValueError:
                    pass
            
            # Przygotowanie wyników (ograniczenie do 8 dla lepszego UX)
            results = []
            for place in restaurants[:8]:
                details = places_api.get_place_details(place["place_id"])
                
                result = {
                    "name": details.get("name", "Nieznana nazwa"),
                    "rating": details.get("rating", "Brak oceny"),
                    "address": details.get("formatted_address", "Brak adresu"),
                    "url": details.get("url", "#"),
                    "price_level": details.get("price_level"),
                    "user_ratings_total": place.get("user_ratings_total", 0),
                    "summary": restaurant_ai.analyze_reviews(details.get("reviews", [])),
                    "is_hidden_gem": hidden_gems and place.get("user_ratings_total", 0) <= 100
                }
                results.append(result)
            
            search_type = "perełki" if hidden_gems else "restauracje"
            logger.info(f"Znaleziono {len(results)} {search_type} dla miasta: {city}")

            expert_result = restaurant_ai.find_expert_recommendation(city=city, cuisine=cuisine)

            if expert_result:
                results.insert(0, {
                "name": expert_result["name"],
                "rating": None,
                "formatted_address": "Ekspercka rekomendacja",
                "review_summary": expert_result["summary"],
                "source": expert_result["source"],
                "is_expert_pick": True
            })
            
            return render_template('index.html', 
                                       active_tab='form',
                                       results=results,
                                       search_type=search_type)
                                       
        except Exception as e:
            logger.error(f"Błąd w form_search: {e}")
            return render_template('index.html', 
                                       active_tab='form',
                                       error=f"Wystąpił błąd: {str(e)}")
    
    return render_template('index.html', active_tab='form')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Główny endpoint - przekierowuje na stronę główną"""
    if path == "" or path == "index.html":
        return render_template('index.html', active_tab='form')
    
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return render_template('index.html', active_tab='form')

    if os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        return render_template('index.html', active_tab='form')

if __name__ == '__main__':
    import sys
    port = 5001
    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    app.run(host='0.0.0.0', port=port, debug=True)

