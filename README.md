Screeny z aplikacji:

![image](https://github.com/user-attachments/assets/3ce8aa98-d66e-4a70-9cbf-64791c2f8560)

![image](https://github.com/user-attachments/assets/5e7daea2-1343-4792-9e11-a3465baf3598)

![image](https://github.com/user-attachments/assets/d73ce62e-0af9-4c92-a724-e1984acdd92c)

![image](https://github.com/user-attachments/assets/94a5bee3-c71a-45d6-be45-8bc2a31df335)

Użyte technologie:
- pydantic do zarządzania Agentami
- Gemini z modelem 1.5-flash
- Web Scraping (w celu znalezienia najlepszych restauracji)
- Połączenie Agentów z GooglePlaces API

Pierwszy Agent odpowiedzialny za przetwarzanie requestu użytkownika w dobrą formę json, następnie przekazuje uzyskane wyniki do drugiego, który wyszukuje odpowiednie restauracje z jak największym dopasowaniem. 
Restauracja polecana przez eksperta pozyskiwana jest poprzez model przeszukujący internet, a konkretnie pdane mu linki do blogów i stron kulinarnych.

Business Case:

Aplikacja początkowo przeznaczona była dla wszystkich - osoby, które nie wiedziały co zjeść w nowym mieście albo szukające czegoś lokalnie mogły dzięki niej znaleźć odpwiednie rekomendaacje.
Dzięki wprowadzeniu nowych funkcjonalności, takich jak wyszukiwanie restauracji "hidden gems" oraz rekomendacje od ekspertów kulinarnych, aplikacja stała się bardziej przystosowana pod szerszą publikę. 
Teraz zarówno głodni turyści mogą znalźć coś do jedzenia, jak i doświadczeni smakosze, którzy chcą odkrywać ukryte miejsca w swojej okolicy i jadać w miejscach sprawdzonych przez godnych zaufania recenzentów.

Możliwość monetyzacji: 

Współpraca z restauracjami/krytykami, którzy mogliby reklamować swoje obiekty dzięki funkcjonalności eksperckich restauracji. Możliwe wprowadzenie reklam powiązanaych, np. serwisów typu Glovo, które od razu pozwalałyby na zamówienia, jeśli dana restauracjia oferuje dowóz.




