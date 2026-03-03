![hankelogo](/images/rovesugv_logo.png)

# rovesugv_web_teleop
Verkkosovellus, jolla voi etäoperoida oikeaa tai simuloitua mobiilirobottia

Status: toimii toistaiseksi vain simuloidun robotin kanssa

## How to
Simulaattori on saatavilla osoitteessa [https://github.com/SeAMKedu/rovesugv_navsim](https://github.com/SeAMKedu/rovesugv_navsim).

Käynnistä ensimmäisessä terminaalissa verkkopalvelin alla olevilla komennoilla.
```
$ cd rovesugv_web_teleop
$ source env/bin/activate
$ python app.py
```

Käynnistä toisessa terminaalissa ROS 2 -sovellus alla olevilla komennoilla.
```
$ cd rovesugv_web_teleop
$ source env/bin/activate
$ python ros2web.py
```

Mene selaimella osoitteeseen [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Tekijätiedot

Hannu Hakalahti, Asiantuntija, TKI, Seinäjoen ammattikorkeakoulu (SEAMK).

## RovesUGV-hanke

RovesUGV-hanke keskittyy autonomisten logistiikkaratkaisujen kehittämiseen ja demonstrointiin Roveksen teollisuusalueella. Hankkeen tarpeen taustalla on Roveksen ja Kapernaumin teollisuusalueiden yritysten välinen jatkuva logistiikka ja tavaraliikenne, joka nykyisin toimii yritysten oman työvoiman, pakettiautojen, ja isompien kuorma-autojen avulla. Hankkeen tavoitteena on kehittää Proof-of-Concept (PoC) demo, jossa tavaraa siirretään autonomisesti Husarion Panther UGV -mobiilirobotin avulla.

* Hankkeen nimi: RovesUGV
* Hankkeen aikataulu: 01.04.2025 - 31.07.2026
* Hankkeen rahoittaja: Etelä-Pohjanmaan liitto, Euroopan aluekehitysrahasto (EAKR)

---
![eakr_logo](/images/Euroopan_unionin_osarahoittama_POS.png)

![epliitto_logo](/images/EPLiitto_logo_vaaka_vari.jpg)

![seamk_logo](/images/SEAMK_vaaka_fi_en_RGB_1200x486.jpg)