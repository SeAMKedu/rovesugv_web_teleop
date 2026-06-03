![hankelogo](/images/rovesugv_logo.png)

# rovesugv_web_teleop
Verkkosovellus, jolla voi etäoperoida simuloitua mobiilirobottia tai Husarion Panther -mobiilirobottia.

![gui](/images/rovesugv_web_teleop.png)



## Ohjelmistoriippuvuudet

* ROS 2 Humble
* Nav2

```
$ sudo apt install ros-humble-navigation2
$ sudo apt install ros-humble-nav2-bringup
```

## How to
Etäohjattavaa mobiilirobottia varten on kehitetty kaksi eri ROS 2 -pakettia.
* [https://github.com/SeAMKedu/rovesugv_navsim](https://github.com/SeAMKedu/rovesugv_navsim)
* [https://github.com/SeAMKedu/rovesugv_gps_nav](https://github.com/SeAMKedu/rovesugv_gps_nav)

Ensimmäinen on tarkoitettu simuloitua, itse tehtyä mobiilirobottia varten. Robotti toimii Gazebo Fortress -simulaattorissa, joka sisältää Framin ja sen lähialueen karttapohjan ja rakennukset.

Jälkimmäinen paketti on tarkoitettu oikeaa, fyysistä Husarion Panther -mobiilirobottia varten. Pantherin antureihin kuuluu muun muassa Velodyne-LiDAR ja Fixposition Vision RTK-2 -satelliittivastaanotin.

Konfiguraationtiedostossa [app.yaml](/config/app.yaml) on **use_sim** parametri, jossa määritetään ohjataanko 
* simulaatiossa toimivaa robottia (use_sim: true)
* tai oikeaa Husarion Panther -mobiilirobottia (use_sim: false).

### Ohjelmien asennus

Kopioi ensin tiedostot omalle koneellesi.
```
git clone https://github.com/SeAMKedu/rovesugv_web_teleop.git
```

Siirry kopioituun kansioon.
```
cd rovesugv_web_teleop/
```

Luo seuraavaksi virtuaaliympäristö Pythonin **venv** paketin avulla.
```
python3 -m venv env
```

Aktivoi virtuaaliympäristö.
```
source env/bin/activate
```

Asenna tarvittavat Python-paketit.
```
pip3 install -r requirements.txt
```
### Nav2:sen käynnistys

Käynnistä joko simulaattori tai Pantherin GPS-navigaatio -paketti. Nav2-kirjaston on oltava käynnissä, että mobiilirobotin navigaatio on mahdollista.

### Terminaali #1: Palvelimen käynnistys

Aktivoi virtuaaliympäristö (vain, jos ei ole vielä aktiivinen).
```
source env/bin/activate
```

Palvelimen perustana on Flask-paketti. Flask-SocketIO-paketti mahdollistaa kaksisuuntaisen kommunikaation palvelimen ja verkkoselaimen välillä. Palvelin käynnistyy alla olevalla komennolla.
```
python3 app.py
```

Mene sitten verkkoselaimella osoitteeseen [http://127.0.0.1:5000](http://127.0.0.1:5000).

Terminaalissa, jossa palvelinta agetaan, tulisi näkyä myös toinen verkko-osoite. Avaamalla kyseisen verkko-osoitteen mobiililaitteessa, mobiilirobottia voidaan ohjata mobiililaitteen avulla. Mobiililaiteen ja tietokoneen, jolla palvelinta ajetaan, tulee olla samassa aliverkossa. Bootstrap CSS -ohjelmistokehyksen ansiosta verkkosivun sisältö mukautuu mobiililaitteen näytön kokoon.

Palvelin sammuu painamalla terminaalissa Ctrl+c.

### Terminaali #2: Telemetria-noodin käynnistys

Avaa toinen terminaali **rovesugv_web_teleop** kansiossa ja aktivoi virtuaaliympäristö.
```
source env/bin/activate
```
Käynnistä **telemetry** noodi, joka tilaa eri ROS 2 -aiheita ja välittää niihin julkaistuja viestejä palvelimelle.
```
python3 ros2web.py
```

Noodin ajon saa lopetettu painamalla Ctrl+c.

Huomautus: virtuaaliympäristön voi deaktivoida komennolla:
```
deactivate
```


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