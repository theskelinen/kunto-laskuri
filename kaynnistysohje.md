## Ennakkotoimenpiteet

1. Kloonaa repositorio koneellesi ja siirry sen juurikansioon
2. Luo kansioon .env tiedosto ja määritä sen sisältö seuraavanlaiseksi:

   DATABASE_URL=postgresql+psycopg2:///user
   
   SECRET_KEY= Oma salainen avaimesi

Tässä "user" on oma käyttäjäkohtainen tunnuksesi.

SECRET_KEY:n voit luoda Pythonin tulkin kautta seuraavasti:

Kirjoita komentoriville:
- python3
- import secrets
- secrets.token_hex(16)
- kopioi avain

3. Asenna PostgreSQL tietokanta, mikäli sitä ei ole asennettu

Ohjeita asentamiseen löydät:

https://github.com/hy-tsoha/local-pg

https://www.postgresql.org/download/

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

Ohjelma toimii selaimessa ja pääset siihen klikkaamalla ctrl pohjassa paikallista osoitetta:

![Screenshot from 2023-07-23 17-54-51](https://github.com/theskelinen/kunto-laskuri/assets/81574636/7b4d99b7-54dd-4d61-9e93-679a1f062f38)
