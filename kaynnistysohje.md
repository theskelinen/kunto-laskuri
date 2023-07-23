## Ennakkotoimenpiteet

1. Kloonaa repositorio koneellesi ja siirry sen juurikansioon
2. Luo kansioon .env tiedosto ja määritä sen sisältö seuraavanlaiseksi:

   DATABASE_URL=postgresql+psycopg2:///user
   
   SECRET_KEY= Oma salainen avaimesi

Tässä "user" on oma käyttäjäkohtainen tunnuksesi.

SECRET_KEY:n voit luoda Pythonin tulkin kautta seuraavasti:

Kirjoita komentoriville:
1. python3
2. import secrets
3. secrets.token_hex(16)
4. kopioi avain

## Asennus

1. Aktivoi virtuaaliympäristö komennoilla:

- python3 -m venv venv

- source venv/bin/activate
  
3. Asenna riippuvuudet komennolla:

- pip install -r ./requirements.txt

4. Määritä tietokannan skeema:

- psql < kuntolaskuri/schema.sql

## Ohjelman suorittaminen

Suorittaminen tapahtuu komennolla:

- flask run
