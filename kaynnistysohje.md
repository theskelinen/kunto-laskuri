# Kunto-laskuri - Käynnistysohjeet

## Yleiskuvaus

Kunto-laskuri on Flask-pohjainen web-sovellus kuntotestien tulosten tallentamiseen ja analysointiin.

## Vaatimukset

- Docker Desktop (Mac/Windows) tai Docker Engine (Linux)
- Git

## Asennus ja käynnistys

### 1. Kloonaa repositorio

```bash
git clone https://github.com/theskelinen/kunto-laskuri.git
cd kunto-laskuri
```

### 2. Asenna riippuvuudet

- Flask-sovellus käyttää Python-riippuvuuksia, jotka on määritelty `requirements.txt`-tiedostossa.
- Docker hoitaa riippuvuuksien asennuksen automaattisesti, mutta varmista, että tiedosto on mukana projektissa.

### 3. Varmista että Docker Desktop on käynnissä

#### Mac
- Avaa Docker Desktop -sovellus
- Odota että Docker on käynnistynyt (ikoni menu barissa ei ole harmaana)

#### Windows
- Avaa Docker Desktop -sovellus
- Odota että Docker on käynnistynyt (ikoni system trayssa näyttää että Docker on käynnissä)

#### Linux
- Docker daemon käynnistyy automaattisesti
- Voit tarkistaa tilan komennolla: `sudo systemctl status docker`
- Jos ei ole käynnissä: `sudo systemctl start docker`

### 4. Käynnistä sovellus Dockerilla

**ENSIMMÄINEN KÄYNNISTYS:**
```bash
# Poista vanhat volumet jos olemassa
docker-compose down -v

# Käynnistä palvelut
docker-compose up --build
```

### 5. Käytä sovellusta selaimessa

- Kun kaikki palvelut ovat käynnissä, avaa selain ja siirry osoitteeseen:
  ```
  http://localhost:5000
  ```
- Sovelluksen pitäisi olla nyt käytettävissä.

### 6. Lopeta sovellus

- Voit pysäyttää sovelluksen painamalla `Ctrl + C` terminaalissa, jossa `docker-compose up` oli käynnissä.
- Vapauta resurssit tarvittaessa komennolla:
  ```bash
  docker-compose down
  ```
## Vianmääritys

### 1. Portti 5000 on jo käytössä
```bash
# Tarkista mikä käyttää porttia
# Mac/Linux:
lsof -i :5000
# Windows (PowerShell):
netstat -ano | findstr :5000

# Pysäytä vanha prosessi tai muuta porttia docker-compose.yml:ssä
```

### 2. Tietokanta ei käynnisty
```bash
# Poista vanhat volumet ja käynnistä uudelleen
docker-compose down -v
docker-compose up --build
```

### 3. Docker cache -ongelmat
```bash
# Rakenna uudelleen ilman cachea
docker-compose build --no-cache
docker-compose up