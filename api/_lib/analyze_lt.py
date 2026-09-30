"""TEXT_LT: the Lithuanian customer sentences of api/analyze.py, with exactly the keys of TEXT_DE (the English ones stay
inline in analyze(), the German ones are TEXT_DE) and the same placeholders ({px}, {good} in "closer"). analyze() takes
them for a request with "lang": "lt" (TEXTS in api/analyze.py). A block reason api/analyze.py can give without a key
here would stop that request with a KeyError, so every reason has one ("eyelid" among them; scripts/check_texts.mjs checks it at build time).

Polite "Jūs" (capitalised in every form), the words of the capture guide (src/try/copy.lt.ts): galinė kamera,
2x priartinimas, bakstelėkite rainelę, dienos šviesa pro langą iš šono, kadras, skaidulos, raštas, kūrinys, vokas.

The capture screen recognises three tips by their words (src/try/shots.ts visibleTips and topTip):
  "reflection" says "automatiškai"                        (hidden: it instructs nothing)
  "on_pupil"   says "Atspindys" and "vyzdžio" (atspind, vyzd)  (hidden when the server flags pupil_reflection)
  "closer"     says "arčiau", and no other tip does       (topTip's pick when the iris is too small)
"""

TEXT_LT = {
    "no_eye": "Šioje nuotraukoje neradome akies. Užpildykite kadrą viena atmerkta akimi ir bandykite dar kartą.",
    "lamp": "Lempos šviesa iškraipo Jūsų akių spalvą. Dienos šviesa pro langą perteikia tikresnę spalvą.",
    "dark_iris": "Jūsų rainelė tamsi, todėl jos skaidulos vos matomos. Dieną atsistokite arti šviesaus lango (ne "
                 "tiesioginiuose saulės spinduliuose), kad langas būtų iš šono, ir fotografuokite dar kartą: daugiau "
                 "šviesos jas išryškins. Stalinė lempa ar žibintuvėlis pakeičia Jūsų akių spalvą.",
    "too_blurry": "Ši nuotrauka per neryški, kad atkurtume Jūsų rainelę, todėl jos nepanaudojome: studijai tektų raštą "
                  "išgalvoti. Fotografuokite iš naujo dienos šviesoje prie lango iš šono, galine kamera su 2x "
                  "priartinimu, bakstelėkite rainelę ekrane, kad kamera ją sufokusuotų, ir laikykite telefoną "
                  "stabiliai.",
    "too_dark": "Jūsų rainelė tamsi, o šioje nuotraukoje buvo per mažai šviesos, kad būtų matomas jos raštas, todėl jos "
                "nepanaudojome: studijai tektų raštą išgalvoti. Fotografuokite iš naujo arti šviesaus lango dienos "
                "šviesoje, kad langas būtų iš šono (ne tiesioginiai saulės spinduliai, ne lempa ir ne blykstė), galine "
                "kamera su 2x priartinimu, bakstelėkite rainelę ekrane, kad kamera ją sufokusuotų, ir laikykite "
                "telefoną stabiliai.",
    "pupil_too_large": "Šioje nuotraukoje Jūsų vyzdys labai išsiplėtęs, todėl matomas tik siauras rainelės žiedas: per "
                       "mažai kūriniui sukurti. Daugiau šviesos vyzdį sumažina: minutę pastovėkite arti šviesaus lango "
                       "dienos šviesoje (ne tiesioginiuose saulės spinduliuose), tada fotografuokite dar kartą, kad "
                       "langas būtų iš šono. Sutemus įjunkite visas lubų lempas ir pirmiausia palaukite minutę. Jei "
                       "akių tyrimo metu vyzdžiai buvo išplėsti lašais, palaukite, kol jų poveikis praeis.",
    "too_small": "Šioje nuotraukoje Jūsų rainelė per maža, todėl matyti per mažai jos rašto: studijai tektų jį "
                 "išgalvoti. Laikykite telefoną maždaug 10 cm nuo akies, galine kamera su 2x priartinimu, kad rainelė "
                 "užpildytų maždaug trečdalį kadro, bakstelėkite rainelę, kad kamera ją sufokusuotų, ir fotografuokite "
                 "dar kartą.",
    "eyelid": "Šioje nuotraukoje Jūsų vokas dengia dalį rainelės, todėl jos nepanaudojome: studijai tektų ant voko piešti "
              "rainelę, o tai atrodo netikra. Nufotografuokite iš naujo: žiūrėkite tiesiai į kamerą, ne įstrižai, "
              "plačiai atmerkite akį, piršto galiuku švelniai pakelkite viršutinį voką ir saugokite, kad blakstienos ir "
              "blakstienų tušas nepatektų ant rainelės.",
    "closer": "Fotografuokite iš arčiau arba naudokite 2x priartinimą: rainelė yra {px} px, o mums reikia {good} px ar "
              "daugiau.",
    "fibres": "Skaidulos dar neišryškėjo. Bakstelėkite rainelę ekrane, kad kamera ją sufokusuotų, atremkite telefoną į "
              "ką nors tvirto ir fotografuokite dar kartą.",
    "open": "Plačiai atmerkite akį: žiūrėkite tiesiai į priekį ir piršto galiuku švelniai pakelkite viršutinį voką, kad "
            "nei vokas, nei blakstienos nedengtų rainelės. Blakstienos virš rainelės kūrinyje atrodo kaip tamsūs "
            "dryžiai.",
    "on_pupil": "Atspindys yra ant Jūsų vyzdžio. Pakreipkite galvą arba patraukite šviesą į šoną, kitaip vyzdį "
                "atkursime kaip vientisą tamsą.",
    "reflection": "Radome atspindį, jį pašalinsime automatiškai.",
    "glare": "Atspindys dengia dalį rainelės skaidulų, o tai, ką jis dengia, tenka atkurti. Pasisukite taip, kad langas "
             "ar lempa būtų iš šono, o ne tiesiai priešais Jus.",
    "soft": "Kadras išėjo šiek tiek neryškus. Naudokite galinę kamerą su 2x priartinimu, bakstelėkite rainelę, kad kamera "
            "ją sufokusuotų, ir laikykite telefoną stabiliai; priekinės kameros tokiu atstumu apskritai negali "
            "sufokusuoti.",
    "no_lock": "Nepavyko patikimai nustatyti apvalaus Jūsų rainelės krašto. Nufotografuokite vieną akį kadro centre, su "
               "šiek tiek vietos aplink, ir pasirūpinkite, kad vokas netrukdytų.",
    "good": "Puikus kadras. Jūsų pačių skaidulos pakankamai ryškios viso dydžio kūriniui.",
    "ok": "Iš to išeis gražus kūrinys. Iš arčiau arba stabiliau padarytas kadras išsaugotų daugiau Jūsų pačių skaidulų "
          "detalių.",
    "weak": "Kadras mažas arba šiek tiek neryškus, todėl daugiau smulkių detalių bus atkurta. Iš arčiau ir stabiliau "
            "padarytas kadras duos tikresnį kūrinį.",
    "glare_ok": "Iš to išeis gražus kūrinys. Kadras be atspindžio ant Jūsų rainelės išsaugotų daugiau Jūsų pačių "
                "skaidulų detalių.",
    "glare_weak": "Atspindys dengia per didelę Jūsų rainelės dalį, todėl po juo esančios skaidulos būtų atkurtos. "
                  "Patraukite šviesą į šoną ir fotografuokite dar kartą.",
    "unlocked": "Radome akį, bet nepavyko patikimai nustatyti rainelės krašto, todėl iškarpa būtų netiksli. Padarykite "
                "kitą nuotrauką.",
}
