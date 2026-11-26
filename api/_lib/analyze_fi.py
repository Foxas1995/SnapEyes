"""TEXT_FI: the customer-facing sentences of api/analyze.py in Finnish, with exactly the keys of TEXT_DE (the English
ones stay inline in analyze(), word for word; these translate them, not the German) and the same placeholders ({px} and
{good} in "closer"). Informal singular "sinä", as the capture screen (src/try/copy.fi.ts), and the words of the capture
guide: takakamera, etukamera, 2x-zoomi, otos, kuva, iiris, säikeet, kuvio, heijastus, pupilli, silmäluomi, taskulamppu
sivulta, päivänvalo. analyze() takes them for a request with "lang": "fi" (TEXTS in api/analyze.py, once wired); a block
reason without a key here would stop that request with a KeyError, so every reason has one ("eyelid" among them;
scripts/check_texts.mjs checks it at build time).

Lives in api/_lib/ (not next to api/analyze.py): Vercel turns every .py file directly under api/ into a function.

The capture screen recognises three tips by their words (src/try/shots.ts visibleTips / topTip), and these are the
Finnish ones its patterns need (add them there when "fi" is wired):
  "reflection" says "automaattisesti"                      (hidden: it instructs nothing)
  "on_pupil"   says "Heijastus" and "pupillisi" (heijastu, pupil)  (hidden when the server flags pupil_reflection)
  "closer"     starts "Mene lähemmäs", and no other tip says "lähemmäs"  (topTip's pick when the iris is too small)
Until the page matches tip keys instead of words, keep those words in the three tips.
"""

TEXT_FI = {
    "no_eye": "Emme löytäneet tästä kuvasta silmää. Täytä kuva yhdellä avoimella silmällä ja yritä uudelleen.",
    "lamp": "Lampun valo sävyttää silmiesi väriä. Päivänvalo ikkunasta tai taskulamppu sivulta antaa aidomman värin.",
    "dark_iris": "Iiriksesi on tumma, joten sen säikeet näkyvät heikosti. Seiso päivänvalossa lähellä valoisaa ikkunaa (ei "
                 "suorassa auringossa) niin, että ikkuna on sivullasi, tai pyydä jotakuta pitämään taskulamppua sivulla, "
                 "ja ota kuva uudelleen: lisävalo tuo säikeet esiin. Lämmin pöytälamppu muuttaa silmiesi väriä.",
    "too_blurry": "Käytä takakameraa, älä etukameraa (selfie). Tämä kuva on liian epätarkka, jotta voisimme entisöidä oman iiriksesi, joten emme käyttäneet sitä: "
                  "studio joutuisi keksimään kuvion. Ota kuva uudelleen päivänvalossa ikkunan luona tai taskulampun "
                  "kanssa, valo sivulta, 2x-zoomilla, tarkenna napauttamalla iiristä näytöllä ja pidä "
                  "puhelin vakaana.",
    "too_dark": "Iiriksesi on tumma, ja tässä kuvassa oli liian vähän valoa sen oman kuvion näkemiseen, joten emme "
                "käyttäneet kuvaa: studio joutuisi keksimään kuvion. Ota kuva uudelleen päivänvalossa lähellä valoisaa "
                "ikkunaa niin, että ikkuna on sivullasi (ei suorassa auringossa, ei huoneen lampun valossa eikä "
                "salamalla), tai sivulla pidetyn taskulampun kanssa, takakameralla ja 2x-zoomilla, tarkenna "
                "napauttamalla iiristä näytöllä ja pidä puhelin vakaana.",
    "pupil_too_large": "Pupillisi on tässä kuvassa hyvin laaja, joten iiriksestäsi näkyy vain ohut rengas: se on liian "
                       "vähän taideteoksesi tekemiseen. Lisävalo pienentää pupillia: seiso minuutti päivänvalossa lähellä "
                       "valoisaa ikkunaa (ei suorassa auringossa) ja ota sitten kuva uudelleen niin, että ikkuna on "
                       "sivullasi. Pimeän tultua sytytä kaikki kattovalot, odota ensin minuutti ja pyydä jotakuta "
                       "pitämään taskulamppua sivulla. Jos pupillisi laajennettiin tipoilla silmätutkimuksessa, odota, "
                       "että niiden vaikutus lakkaa.",
    "too_small": "Iiriksesi on tässä kuvassa liian pieni, joten sen omaa kuviota näkyy liian vähän: studio joutuisi "
                 "keksimään sen. Pidä puhelinta noin 10 cm:n päässä silmästäsi, käytä takakameraa ja 2x-zoomia niin, että "
                 "iiris täyttää noin kolmasosan kuvasta, tarkenna napauttamalla iiristä ja ota kuva uudelleen.",
    "too_far": "Silmä on liian kaukana. Kuvaan vain yksi silmä, ei koko kasvoja. Takakamera, noin 10 cm silmästä.",
    "eyelid": "Silmäluomesi peittää tässä kuvassa osan iiriksestäsi, joten emme käyttäneet kuvaa: studio joutuisi "
              "maalaamaan iiristä luomen päälle, ja se näyttää tekaistulta. Ota kuva uudelleen: katso suoraan linssiin, "
              "älä vinosti, pidä silmä aivan auki, nosta yläluomea varovasti sormenpäällä ja pidä ripset ja ripsiväri "
              "poissa iiriksen päältä.",
    "closer": "Mene lähemmäs tai käytä 2x-zoomia: iiris on {px} px, ja tarvitsemme vähintään {good} px.",
    "fibres": "Säikeet eivät vielä erotu. Napauta iiristä näytöllä, jotta kamera tarkentaa siihen, tue puhelin johonkin "
              "tukevaan ja ota kuva uudelleen.",
    "open": "Avaa silmä aivan auki: katso suoraan eteenpäin ja nosta yläluomea varovasti sormenpäällä, jotta luomi tai "
            "ripset eivät peitä iiristä. Iiriksen päällä olevat ripset näkyvät taideteoksessa tummina juovina.",
    "on_pupil": "Heijastus on pupillisi kohdalla. Kallista päätäsi tai siirrä valo sivulle, muuten joudumme rakentamaan "
                "pupillin uudelleen pelkkänä pimeytenä.",
    "reflection": "Löysimme heijastuksen; poistamme sen automaattisesti.",
    "glare": "Heijastus peittää osan iiriksen säikeistä, ja sen peittämä osa on rakennettava uudelleen. Käänny niin, "
             "että ikkuna tai lamppu on sivullasi eikä suoraan edessäsi.",
    "soft": "Käytä takakameraa, älä etukameraa (selfie). Otoksesta tuli pehmeä. Käytä 2x-zoomia, tarkenna napauttamalla iiristä ja pidä puhelin "
            "vakaana; etukamerat eivät pysty tarkentamaan tältä etäisyydeltä lainkaan.",
    "no_lock": "Emme saaneet varmasti kiinni iiriksesi pyöreästä reunasta. Aseta yksi silmä kuvan keskelle niin, että "
               "sen ympärille jää hieman tilaa, ja pidä silmäluomi poissa tieltä.",
    "good": "Hieno otos. Omat säikeesi ovat tarpeeksi terävät täysikokoiseen taideteokseen.",
    "ok": "Tästä tulee kaunis taideteos. Lähempää otettu tai vakaampi otos säilyttäisi enemmän omien säikeidesi "
          "yksityiskohtia.",
    "weak": "Otos on pieni tai pehmeä, joten suurempi osa hienoista yksityiskohdista joudutaan rakentamaan uudelleen. "
            "Lähempää ja vakaammin otettu kuva antaa aidomman taideteoksen.",
    "glare_ok": "Tästä tulee kaunis taideteos. Otos, jossa iiriksesi päällä ei ole heijastusta, säilyttäisi enemmän "
                "omien säikeidesi yksityiskohtia.",
    "glare_weak": "Heijastus peittää liian suuren osan iiriksestäsi, joten sen alla olevat säikeet jouduttaisiin "
                  "rakentamaan uudelleen. Siirrä valo sivulle ja ota kuva uudelleen.",
    "unlocked": "Löysimme silmän, mutta emme saaneet varmasti kiinni iiriksen reunasta, joten rajaus menisi pieleen. "
                "Ota vielä yksi kuva.",
}
