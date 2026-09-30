"""TEXT_HU: the customer-facing sentences of api/analyze.py in Hungarian, with exactly the keys of TEXT_DE (the English
ones stay inline in analyze(), word for word; these translate them, not the German) and the same placeholders ({px} and
{good} in "closer"). Friendly "te" and the words of /try (src/try/copy.hu.ts): hátsó kamera, 2x-es zoom, felvétel,
írisz, rostok, tükröződés, pupilla, szemhéj. analyze() takes them for a request with "lang": "hu" (TEXTS in api/analyze.py);
a block reason without a key here would stop that request with a KeyError, so every reason has one ("eyelid" among them; scripts/check_texts.mjs checks it at build time).

Lives in api/_lib/ (not next to api/analyze.py): Vercel turns every .py file directly under api/ into a function.

The capture screen recognises three tips by their words (src/try/shots.ts visibleTips / topTip): "automatikusan",
"tükröződés" + "pupilla" and "zoom" (the last one also matches the English/German expression). Until the page matches tip
keys instead of words, keep those words in the three tips.
"""

TEXT_HU = {
    "no_eye": "Ezen a fotón nem találtunk szemet. Egy nyitott szem töltse ki a képet, és próbáld újra.",
    "lamp": "A lámpafény elszínezi a szemed színét. Egy ablakon beeső nappali fény valódibb színt ad.",
    "dark_iris": "Az íriszed sötét, ezért a rostjai csak halványan látszanak. Nappal állj közel egy világos ablakhoz (ne "
                 "közvetlen napfényben), úgy, hogy az ablak oldalt legyen, és fotózz újra: több fénynél előtűnnek. Az "
                 "asztali lámpa vagy a zseblámpa megváltoztatja a szemed színét.",
    "too_blurry": "Ez a fotó túl elmosódott ahhoz, hogy a saját íriszedet helyreállítsuk, ezért nem használtuk: a "
                  "stúdiónak ki kellene találnia a mintázatot. Kérjük, fotózd újra nappali fénynél, oldalt lévő "
                  "ablaknál, a hátsó kamerával 2x-es zoommal, koppints a képernyőn az íriszre az élességállításhoz, és "
                  "tartsd stabilan a telefont.",
    "too_dark": "Az íriszed sötét, és ezen a fotón túl kevés volt a fény ahhoz, hogy a saját mintázata látsszon, ezért nem "
                "használtuk: a stúdiónak ki kellene találnia a mintázatot. Kérjük, fotózd újra nappal, egy világos "
                "ablak közelében, úgy, hogy az ablak oldalt legyen (ne közvetlen napfényben, se lámpa, se vaku), a "
                "hátsó kamerával 2x-es zoommal, koppints a képernyőn az íriszre az élességállításhoz, és tartsd "
                "stabilan a telefont.",
    "pupil_too_large": "Ezen a fotón nagyon tág a pupillád, ezért csak egy vékony gyűrű látszik az íriszedből: ez túl "
                       "kevés az alkotásodhoz. Több fénynél kisebb lesz a pupilla: állj egy percre közel egy világos "
                       "ablakhoz nappali fényben (ne közvetlen napfényben), majd fotózz újra úgy, hogy az ablak oldalt "
                       "legyen. Sötétedés után kapcsold fel az összes mennyezeti lámpát, és előtte várj egy percet. Ha "
                       "egy szemvizsgálaton cseppekkel tágították a pupilládat, várd meg, amíg a hatásuk elmúlik.",
    "too_small": "Az íriszed túl kicsi ezen a fotón, ezért túl kevés látszik a saját mintázatából: a stúdiónak ki kellene "
                 "találnia. Tartsd a telefont kb. 10 cm-re a szemedtől, a hátsó kamerával 2x-es zoommal, hogy az írisz a "
                 "kép kb. harmadát kitöltse, koppints az íriszre az élességállításhoz, és fotózz újra.",
    "eyelid": "A szemhéjad ezen a fotón eltakarja az íriszed egy részét, ezért nem használtuk: a stúdiónak az íriszt a "
              "szemhéjra kellene festenie, és ez hamisnak tűnik. Kérjük, fotózd újra: nézz egyenesen a kamerába, ne "
              "ferdén, nyisd tágra a szemed, egy ujjheggyel óvatosan emeld meg a felső szemhéjadat, és ügyelj rá, hogy "
              "a szempillák és a szempillaspirál ne lógjanak az íriszre.",
    "closer": "Menj közelebb, vagy használd a 2x-es zoomot: az írisz {px} px, nekünk legalább {good} px kell.",
    "fibres": "A rostok még nem vehetők ki élesen. Koppints a képernyőn az íriszre, hogy a kamera arra állítsa az "
              "élességet, támaszd a telefont valami stabilhoz, és fotózz újra.",
    "open": "Nyisd tágra a szemed: nézz egyenesen előre, és egy ujjheggyel óvatosan emeld meg a felső szemhéjadat, hogy se "
            "a szemhéj, se a szempillák ne takarják az íriszt. Az íriszen átlógó szempillák sötét csíkként jelennek meg az "
            "alkotáson.",
    "on_pupil": "A tükröződés a pupilládon van. Döntsd meg a fejed, vagy vidd oldalra a fényt, különben a pupillát "
                "egyszerű sötétként kell újraépítenünk.",
    "reflection": "Tükröződést találtunk; automatikusan eltávolítjuk.",
    "glare": "Egy tükröződés eltakarja az íriszrostok egy részét, és amit eltakar, azt újra kell építeni. Fordulj úgy, hogy "
             "az ablak vagy a lámpa oldalt legyen, ne közvetlenül előtted.",
    "soft": "Ez kissé életlen lett. Használd a hátsó kamerát 2x-es zoommal, koppints az íriszre az élességállításhoz, és "
            "tartsd stabilan a telefont; az előlapi kamerák erről a távolságról egyáltalán nem tudnak élesre állni.",
    "no_lock": "Nem tudtuk biztosan megtalálni az íriszed kerek szélét. Helyezd az egyik szemed a kép közepére, egy kis "
               "hellyel körülötte, és a szemhéjad ne lógjon bele.",
    "good": "Remek felvétel. A saját rostjaid elég élesek a teljes méretű alkotáshoz.",
    "ok": "Ebből szép alkotás lesz. Egy közelebbi vagy stabilabb felvétel több részletet őrizne meg a saját rostjaidból.",
    "weak": "Kicsi vagy kissé életlen, ezért a finom részletek nagyobb részét kell újraépítenünk. Közelebbről és stabilabban "
            "valódibb alkotás lesz belőle.",
    "glare_ok": "Ebből szép alkotás lesz. Egy felvétel az íriszeden lévő tükröződés nélkül több részletet őrizne meg a "
                "saját rostjaidból.",
    "glare_weak": "Egy tükröződés túl sokat eltakar az íriszedből, ezért az alatta lévő rostokat újra kellene építeni. "
                  "Vidd oldalra a fényt, és fotózz újra.",
    "unlocked": "Találtunk egy szemet, de az írisz szélét nem tudtuk biztosan megtalálni, így a kivágás pontatlan lenne. "
                "Kérjük, készíts egy újabb fotót.",
}
