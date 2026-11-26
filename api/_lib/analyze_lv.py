"""TEXT_LV: the customer-facing sentences of api/analyze.py in Latvian, with exactly the keys of TEXT_DE (the English
ones stay inline in analyze(), word for word; these translate them, not the German) and the same placeholders ({px} and
{good} in "closer"). Polite plural "jūs" (lowercase inside a sentence) and the words of the capture guide: aizmugurējā
kamera, priekšējā kamera, 2x tuvinājums, kadrs, varavīksnene, šķiedras, raksts, atspīdums, zīlīte, plakstiņš, lukturītis
no sāniem, dienasgaisma. analyze() takes them for a request with "lang": "lv" (TEXTS in api/analyze.py, once wired); a
block reason without a key here would stop that request with a KeyError, so every reason has one ("eyelid" among them;
scripts/check_texts.mjs checks it at build time).

Lives in api/_lib/ (not next to api/analyze.py): Vercel turns every .py file directly under api/ into a function.

The capture screen recognises three tips by their words (src/try/shots.ts visibleTips / topTip), and these are the
Latvian ones for its patterns:
  "reflection" says "automātiski"                         (hidden: it instructs nothing)
  "on_pupil"   says "Atspīdums" and "zīlītes" (atspīd, zīlīt)  (hidden when the server flags pupil_reflection)
  "closer"     starts "Pieejiet tuvāk", and no other tip says "pieejiet tuvāk"  (topTip's pick when the iris is too small)
Until the page matches tip keys instead of words, keep those words in the three tips. The other tips say "2x
tuvinājums" and "no mazāka attāluma", never "zoom" or "tuvāk", so none of the page's older patterns catches them.
"""

TEXT_LV = {
    "no_eye": "Šajā fotogrāfijā neatradām aci. Lai viena atvērta acs aizpilda kadru, un mēģiniet vēlreiz.",
    "lamp": "Lampas gaisma maina jūsu acu krāsu. Dienasgaisma no loga vai lukturītis no sāniem dod patiesāku krāsu.",
    "dark_iris": "Jūsu varavīksnene ir tumša, tāpēc tās šķiedras ir vāji redzamas. Dienā nostājieties tuvu gaišam logam "
                 "(ne tiešos saules staros) tā, lai logs būtu sānos, vai palūdziet kādam turēt lukturīti no sāniem, un "
                 "fotografējiet vēlreiz: vairāk gaismas tās izcels. Silta galda lampa maina jūsu acu krāsu.",
    "too_blurry": "Šī fotogrāfija ir pārāk izplūdusi, lai mēs atjaunotu jūsu pašu varavīksneni, tāpēc to neizmantojām: "
                  "studijai rakstu nāktos izdomāt. Lūdzu, nofotografējiet vēlreiz dienasgaismā no loga vai ar "
                  "lukturīti, no sāniem, ar aizmugurējo kameru un 2x tuvinājumu, pieskarieties varavīksnenei ekrānā, "
                  "lai iefokusētu, un turiet telefonu nekustīgi.",
    "too_dark": "Jūsu varavīksnene ir tumša, un šajā fotogrāfijā bija par maz gaismas, lai redzētu tās pašas rakstu, "
                "tāpēc to neizmantojām: studijai rakstu nāktos izdomāt. Lūdzu, nofotografējiet vēlreiz dienasgaismā "
                "tuvu gaišam logam tā, lai logs būtu sānos (ne tiešos saules staros, bez istabas lampas un bez "
                "zibspuldzes), vai ar lukturīti, ko kāds tur no sāniem, ar aizmugurējo kameru un 2x tuvinājumu, "
                "pieskarieties varavīksnenei ekrānā, lai iefokusētu, un turiet telefonu nekustīgi.",
    "pupil_too_large": "Šajā fotogrāfijā jūsu zīlīte ir ļoti plata, tāpēc redzams tikai šaurs varavīksnenes gredzens: "
                       "tas ir par maz jūsu mākslas darbam. Vairāk gaismas samazina zīlīti: dienasgaismā minūti "
                       "pastāviet tuvu gaišam logam (ne tiešos saules staros) un pēc tam fotografējiet vēlreiz tā, lai "
                       "logs būtu sānos. Kad ir tumšs, ieslēdziet visas griestu lampas, vispirms minūti pagaidiet un "
                       "palūdziet kādam turēt lukturīti no sāniem. Ja zīlītes acu pārbaudē paplašinātas ar pilieniem, "
                       "pagaidiet, līdz to iedarbība beigsies.",
    "too_small": "Šajā fotogrāfijā jūsu varavīksnene ir pārāk maza, tāpēc redzams pārāk maz tās pašas raksta: studijai "
                 "to nāktos izdomāt. Turiet telefonu apmēram 10 cm no acs, ar aizmugurējo kameru un 2x tuvinājumu, lai "
                 "varavīksnene aizņem apmēram trešdaļu kadra, pieskarieties varavīksnenei, lai iefokusētu, un "
                 "fotografējiet vēlreiz.",
    "too_far": "Acs ir pārāk tālu. Kadrā jābūt tikai vienai acij, nevis visai sejai. Aizmugurējā kamera, apmēram 10 cm no acs.",
    "eyelid": "Šajā fotogrāfijā plakstiņš aizsedz daļu jūsu varavīksnenes, tāpēc to neizmantojām: studijai nāktos "
              "uzzīmēt varavīksneni pāri plakstiņam, un tas izskatās neīsti. Lūdzu, nofotografējiet vēlreiz: skatieties "
              "taisni objektīvā, nevis slīpi, ar plaši atvērtu aci, ar pirksta galu saudzīgi paceliet augšējo plakstiņu "
              "un raugieties, lai skropstas un skropstu tuša neaizsedz varavīksneni.",
    "closer": "Pieejiet tuvāk vai izmantojiet 2x tuvinājumu: varavīksnene ir {px} px, mums vajag {good} px vai vairāk.",
    "fibres": "Šķiedras vēl nav skaidri redzamas. Pieskarieties varavīksnenei ekrānā, lai kamera to iefokusē, "
              "atbalstiet telefonu pret kaut ko stabilu un fotografējiet vēlreiz.",
    "open": "Plaši atveriet aci: skatieties taisni uz priekšu un ar pirksta galu saudzīgi paceliet augšējo plakstiņu, "
            "lai plakstiņš un skropstas neaizsedz varavīksneni. Skropstas pār varavīksneni mākslas darbā izskatās kā "
            "tumšas svītras.",
    "on_pupil": "Atspīdums ir uz jūsu zīlītes. Nolieciet galvu vai pavirziet gaismu uz sāniem, citādi zīlīti nāksies "
                "atveidot kā vienkāršu tumsu.",
    "reflection": "Atradām atspīdumu; to noņemsim automātiski.",
    "glare": "Atspīdums aizsedz daļu varavīksnenes šķiedru, un aizsegto nākas rekonstruēt. Pagriezieties tā, lai logs "
             "vai lampa būtu sānos, nevis tieši jums priekšā.",
    "soft": "Kadrs iznāca nedaudz izplūdis. Izmantojiet aizmugurējo kameru ar 2x tuvinājumu, pieskarieties "
            "varavīksnenei, lai iefokusētu, un turiet telefonu nekustīgi; priekšējās kameras šādā attālumā vispār "
            "nespēj iefokusēt.",
    "no_lock": "Neizdevās droši atrast jūsu varavīksnenes apaļo malu. Novietojiet vienu aci kadra centrā ar nelielu "
               "brīvu vietu apkārt un raugieties, lai plakstiņš netraucē.",
    "good": "Lielisks kadrs. Jūsu pašu šķiedras ir pietiekami asas pilna izmēra mākslas darbam.",
    "ok": "No šī iznāks skaists mākslas darbs. Kadrs no mazāka attāluma vai nekustīgāks kadrs saglabātu vairāk jūsu "
          "pašu šķiedru detaļu.",
    "weak": "Kadrs ir mazs vai nedaudz izplūdis, tāpēc vairāk smalko detaļu nāksies rekonstruēt. No mazāka attāluma un "
            "nekustīgāk iegūsiet patiesāku mākslas darbu.",
    "glare_ok": "No šī iznāks skaists mākslas darbs. Kadrs bez atspīduma uz varavīksnenes saglabātu vairāk jūsu pašu "
                "šķiedru detaļu.",
    "glare_weak": "Atspīdums aizsedz pārāk lielu daļu jūsu varavīksnenes, tāpēc šķiedras zem tā nāktos rekonstruēt. "
                  "Pavirziet gaismu uz sāniem un fotografējiet vēlreiz.",
    "unlocked": "Atradām aci, bet neizdevās droši atrast varavīksnenes malu, tāpēc izgriezums būtu neprecīzs. Lūdzu, "
                "uzņemiet vēl vienu fotogrāfiju.",
}
