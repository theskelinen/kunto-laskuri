# Kuntolaskuri

Kuntolaskuri on ohjelma, joka laskee käyttäjälle testikohtaisen kuntoluokan.

Kuntolaskuriin on tallennettu ikäkohtaiset viitearvot kolmesta eri lihaskuntotestistä, joista kyykistystestillä mitataan alaraajojen lihasvoimaa, istumaannousutestillä keskivartalon lihasvoimaa ja yläraajojen dynaamisella nostotestillä yläraajojen lihasvoimaa.

Lisäksi kuntolaskurilla voidaan laskea kuntoluokat Työterveyslaitoksen tasapainotestiin (yhden jalan seisonta) ja hartiaseudun liikkuvuus testiin.

Kuntolaskuri laskee kuntoluokan käyttäjän syöttämien taustatietojen (ikä ja sukupuoli), sekä testissä saadun tuloksen (esim. toistomäärä tai aika) pohjalta.

Käytännössä kuntolaskuri "laskee" kuntoluokan hakemalla sen ohjelmaan tallennetusta tietokannasta käyttäjäsyötteen perusteella. Tietokantaan on syötetty Toimia-tietokannasta löytyvät testikohtaiset viitearvot.

Kuntoluokka asettuu välille 1-5, jossa 1 = heikko, 2 = välttävä, 3 = keskinkertainen, 4 = hyvä ja 5 = erinomainen.

- [Sovelluksen käynnistysohje](/kaynnistysohje.md)

Linkki Toimia-tietokantaan: https://www.terveyspori.fi/apps/dtk/tmi?toc=802599

Kyykistystesti: https://www.terveysportti.fi/apps/dtk/tmi/article/tmm00056?toc=307488

Istumaannousutesti: https://www.terveysportti.fi/apps/dtk/tmi/article/tmm00058?toc=307483

Yläraajojen dynaaminen nostotesti: https://www.terveysportti.fi/apps/dtk/tmi/article/tmm00043?toc=307485
