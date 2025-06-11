Screeny z aplikacji:

![image](https://github.com/user-attachments/assets/3ce8aa98-d66e-4a70-9cbf-64791c2f8560)

![image](https://github.com/user-attachments/assets/5e7daea2-1343-4792-9e11-a3465baf3598)

![image](https://github.com/user-attachments/assets/d73ce62e-0af9-4c92-a724-e1984acdd92c)

![image](https://github.com/user-attachments/assets/94a5bee3-c71a-45d6-be45-8bc2a31df335)

Użyte technologie:
- Pydantic – do zarządzania agentami i walidacji danych.
- Gemini 1.5 Flash – jako model językowy wspierający przetwarzanie zapytań.
- Web Scraping – w celu wyszukiwania najlepszych restauracji na blogach i stronach kulinarnych.
- Google Places API – do integracji z bazą restauracji i lokalizacji.

Architektura rozwiązania:

System działa w oparciu o dwóch agentów:

Agent przetwarzający – przekształca zapytanie użytkownika w strukturyzowany format JSON.

Agent wyszukujący – na podstawie danych od pierwszego agenta znajduje restauracje o najwyższym dopasowaniu. Dodatkowo, korzystając z modelu przeszukującego internet, identyfikuje rekomendacje od ekspertów kulinarnych na podstawie blogów i recenzji.

Business Case:

Aplikacja powstała z myślą o osobach szukających idealnego miejsca na posiłek – zarówno turystach, jak i lokalnych mieszkańcach. Dzięki wprowadzeniu funkcji takich jak:
- wyszukiwanie "hidden gems" (ukrytych perełek gastronomicznych),
- rekomendacje od ekspertów kulinarnych,
stała się atrakcyjna dla szerszego grona odbiorców.

Dziś korzystają z niej:
✔ Podróżni, którzy chcą szybko znaleźć dobrą restaurację w nowym mieście.
✔ Smakosze, poszukujący wyjątkowych miejsc sprawdzonych przez krytyków lub ukrytych perełek w swojej okolicy.

Możliwość monetyzacji: 

Współpraca z restauracjami/krytykami, którzy mogliby reklamować swoje obiekty dzięki funkcjonalności eksperckich restauracji. Możliwe wprowadzenie reklam powiązanaych, np. serwisów typu Glovo, które od razu pozwalałyby na zamówienia, jeśli dana restauracjia oferuje dowóz.




