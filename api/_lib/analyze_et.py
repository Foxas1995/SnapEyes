"""TEXT_ET: the customer-facing sentences of api/analyze.py in Estonian, with exactly the keys of TEXT_DE (the English
ones stay inline in analyze(), word for word; these translate them, not the German) and the same placeholders ({px} and
{good} in "closer"). Informal singular "sina" and the words of the capture guide: tagakaamera, esikaamera, 2x suurendus,
võte, iiris, kiud, muster, peegeldus, pupill, silmalaug, taskulamp küljelt, päevavalgus. What the model has to make up
is "rekonstrueerida" (never "taastada", which is the site's word for restoring the customer's own iris).
analyze() takes them for a request with "lang": "et" (TEXTS in api/analyze.py, once wired); a block reason without a
key here would stop that request with a KeyError, so every reason has one ("eyelid" among them;
scripts/check_texts.mjs checks it at build time).

Lives in api/_lib/ (not next to api/analyze.py): Vercel turns every .py file directly under api/ into a function.

The capture screen recognises three tips by their words (src/try/shots.ts visibleTips / topTip), and these are the
Estonian ones for its patterns (the page's patterns need these words added: "automaatselt", "peegeldus", "lähemale"):
  "reflection" says "automaatselt"                      (hidden: it instructs nothing)
  "on_pupil"   says "Peegeldus" and "pupillil"          (hidden when the server flags pupil_reflection)
  "closer"     starts "Tule lähemale", and no other tip says "lähemale"  (topTip's pick when the iris is too small)
Until the page matches tip keys instead of words, keep those words in the three tips.
"""

TEXT_ET = {
    "no_eye": "Me ei leidnud sellelt fotolt silma. Täida kaader ühe avatud silmaga ja proovi uuesti.",
    "lamp": "Lambivalgus muudab sinu silmade värvi. Päevavalgus aknast või taskulamp küljelt annab tõetruuma värvi.",
    "dark_iris": "Sinu iiris on tume, seega on selle kiud nõrgalt näha. Seisa päevavalguses heleda akna lähedal (mitte "
                 "otsese päikese käes), nii et aken jääb küljele, või palu kellelgi hoida taskulampi küljelt, ja "
                 "pildista uuesti: rohkem valgust toob need esile. Soe laualamp muudab sinu silmade värvi.",
    "too_blurry": "See foto on liiga udune, et saaksime sinu enda iirise taastada, seega me seda ei kasutanud: stuudio "
                  "peaks mustri välja mõtlema. Palun pildista uuesti akna päevavalguses või taskulambiga, küljelt, "
                  "tagakaamera 2x suurendusega, puuduta teravustamiseks ekraanil iirist ja hoia telefoni paigal.",
    "too_dark": "Sinu iiris on tume ja sellel fotol oli liiga vähe valgust, et selle enda mustrit näha, seega me seda ei "
                "kasutanud: stuudio peaks mustri välja mõtlema. Palun pildista uuesti päevavalguses heleda akna "
                "lähedal, nii et aken jääb küljele (mitte otsese päikese käes, ilma toalambi ja välguta), või "
                "taskulambiga, mida keegi hoiab küljelt, tagakaamera 2x suurendusega, puuduta teravustamiseks ekraanil "
                "iirist ja hoia telefoni paigal.",
    "pupil_too_large": "Sinu pupill on sellel fotol väga lai, seega on näha ainult õhuke rõngas sinu iirisest: sellest ei "
                       "piisa sinu kunstiteose valmistamiseks. Rohkem valgust teeb pupilli väiksemaks: seisa minut aega "
                       "päevavalguses heleda akna lähedal (mitte otsese päikese käes) ja pildista siis uuesti nii, et "
                       "aken jääb küljele. Pimedal ajal pane põlema kõik laelambid, oota esmalt minut ja palu kellelgi "
                       "hoida taskulampi küljelt. Kui silmakontrollis laiendati sinu pupille tilkadega, oota, kuni nende "
                       "mõju möödub.",
    "too_small": "Sinu iiris on sellel fotol liiga väike, seega on selle enda mustrit näha liiga vähe: stuudio peaks selle "
                 "välja mõtlema. Hoia telefoni umbes 10 cm kaugusel silmast, tagakaamera 2x suurendusega, nii et iiris "
                 "täidab umbes kolmandiku kaadrist, puuduta teravustamiseks iirist ja pildista uuesti.",
    "eyelid": "Silmalaug katab sellel fotol osa sinu iirisest, seega me seda ei kasutanud: stuudio peaks maalima iirise "
              "silmalau peale ja see näeb võlts välja. Palun pildista uuesti, vaadates otse objektiivi, mitte viltu, "
              "silm pärani lahti: tõsta ülemist laugu õrnalt sõrmeotsaga ning hoia ripsmed ja ripsmetušš iiriselt "
              "eemal.",
    "closer": "Tule lähemale või kasuta 2x suurendust: iiris on {px} px, meil on vaja {good} px või rohkem.",
    "fibres": "Kiud ei ole veel selgelt näha. Puuduta ekraanil iirist, et kaamera sellele teravustaks, toeta telefon "
              "millelegi kindlale ja pildista uuesti.",
    "open": "Ava silm pärani: vaata otse ette ja tõsta ülemist laugu õrnalt sõrmeotsaga, et laug ega ripsmed ei ulatuks "
            "iirise peale. Iirise peale ulatuvad ripsmed paistavad kunstiteosel tumedate triipudena.",
    "on_pupil": "Peegeldus on sinu pupillil. Kalluta pead või nihuta valgus küljele, muidu peame pupilli "
                "rekonstrueerima tavalise tumedusena.",
    "reflection": "Leidsime peegelduse; eemaldame selle automaatselt.",
    "glare": "Peegeldus katab osa iirise kiududest ja see, mida ta varjab, tuleb rekonstrueerida. Pööra end nii, et aken "
             "või lamp jääks küljele, mitte otse sinu ette.",
    "soft": "See tuli veidi udune. Kasuta tagakaamerat 2x suurendusega, puuduta teravustamiseks iirist ja hoia telefoni "
            "paigal; esikaamerad ei suuda nii lähedalt üldse teravustada.",
    "no_lock": "Me ei suutnud sinu iirise ümarat serva kindlalt leida. Sea üks silm kaadri keskele, nii et selle ümber "
               "jääb veidi ruumi, ja hoia silmalaug eest ära.",
    "good": "Suurepärane võte. Sinu enda kiud on täissuuruses kunstiteose jaoks piisavalt teravad.",
    "ok": "Sellest saab ilus kunstiteos. Lähemalt või kindlama käega tehtud võte säilitaks rohkem sinu enda kiudude "
          "detaile.",
    "weak": "Väike või udune, seega tuleb rohkem peeni detaile rekonstrueerida. Lähemalt ja kindlama käega tehtud võte "
            "annab tõetruuma kunstiteose.",
    "glare_ok": "Sellest saab ilus kunstiteos. Võte ilma peegelduseta sinu iirisel säilitaks rohkem sinu enda kiudude "
                "detaile.",
    "glare_weak": "Peegeldus katab liiga suure osa sinu iirisest, seega tuleks selle all olevad kiud rekonstrueerida. "
                  "Nihuta valgus küljele ja pildista uuesti.",
    "unlocked": "Leidsime silma, kuid ei suutnud iirise serva kindlalt leida, seega oleks väljalõige paigast ära. Palun "
                "tee uus foto.",
}
