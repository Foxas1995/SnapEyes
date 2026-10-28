"""TEXT_HR: the customer-facing sentences of api/analyze.py in Croatian, with exactly the keys of TEXT_DE (the English
ones stay inline in analyze(), word for word; these translate them, not the German) and the same placeholders ({px} and
{good} in "closer"). Polite plural "vi" (lowercase inside a sentence) and the words of the capture guide: stražnja
kamera, prednja kamera, zum 2x, snimka, šarenica, vlakna, uzorak, odsjaj, zjenica, vjeđa, svjetiljka sa strane, dnevno
svjetlo. analyze() takes them for a request with "lang": "hr" (TEXTS in api/analyze.py, once wired); a block reason
without a key here would stop that request with a KeyError, so every reason has one ("eyelid" among them;
scripts/check_texts.mjs checks it at build time).

Lives in api/_lib/ (not next to api/analyze.py): Vercel turns every .py file directly under api/ into a function.

The capture screen recognises three tips by their words (src/try/shots.ts visibleTips / topTip), and these are the
Croatian ones for its patterns:
  "reflection" says "automatski"                        (hidden: it instructs nothing)
  "on_pupil"   says "Odsjaj" and "zjenici" (odsjaj, zjenic)  (hidden when the server flags pupil_reflection)
  "closer"     starts "Približite", and no other tip says "približ"  (topTip's pick when the iris is too small)
Until the page matches tip keys instead of words, keep those words in the three tips.
"""

TEXT_HR = {
    "no_eye": "Na ovoj fotografiji nismo pronašli oko. Neka jedno otvoreno oko ispuni kadar i pokušajte ponovno.",
    "lamp": "Svjetlo lampe mijenja boju vaših očiju. Dnevno svjetlo s prozora ili svjetiljka sa strane daju vjerniju boju.",
    "dark_iris": "Vaša je šarenica tamna, pa se njezina vlakna slabo vide. Danju stanite blizu svijetlog prozora (ne na "
                 "izravnom suncu), tako da je prozor sa strane, ili zamolite nekoga da drži svjetiljku sa strane, i "
                 "fotografirajte ponovno: više svjetla istaknut će ih. Topla stolna lampa mijenja boju vaših očiju.",
    "too_blurry": "Ova je fotografija previše mutna da bismo obnovili vašu vlastitu šarenicu, pa je nismo upotrijebili: "
                  "studio bi morao izmisliti uzorak. Molimo snimite je ponovno pri dnevnom svjetlu s prozora ili sa "
                  "svjetiljkom, sa strane, stražnjom kamerom uz zum 2x, dodirnite šarenicu na zaslonu da se izoštri i "
                  "držite telefon mirno.",
    "too_dark": "Vaša je šarenica tamna, a na ovoj fotografiji bilo je premalo svjetla da se vidi njezin vlastiti uzorak, "
                "pa je nismo upotrijebili: studio bi morao izmisliti uzorak. Molimo snimite je ponovno blizu svijetlog "
                "prozora pri dnevnom svjetlu, tako da je prozor sa strane (ne na izravnom suncu, bez sobne lampe i bez "
                "bljeskalice), ili sa svjetiljkom koju netko drži sa strane, stražnjom kamerom uz zum 2x, dodirnite "
                "šarenicu na zaslonu da se izoštri i držite telefon mirno.",
    "pupil_too_large": "Vaša je zjenica na ovoj fotografiji jako proširena, pa se vidi samo tanak prsten šarenice: to je "
                       "premalo za vaše umjetničko djelo. Više svjetla smanjuje zjenicu: stanite na minutu blizu svijetlog "
                       "prozora pri dnevnom svjetlu (ne na izravnom suncu), a zatim fotografirajte ponovno tako da je "
                       "prozor sa strane. Kad padne mrak, upalite sva stropna svjetla, najprije pričekajte minutu i "
                       "zamolite nekoga da drži svjetiljku sa strane. Ako su vam zjenice na pregledu očiju proširili "
                       "kapima, pričekajte da njihov učinak prođe.",
    "too_small": "Vaša je šarenica na ovoj fotografiji premalena, pa se vidi premalo njezina vlastitog uzorka: studio bi ga "
                 "morao izmisliti. Držite telefon oko 10 cm od oka, sa stražnjom kamerom uz zum 2x, tako da šarenica "
                 "ispuni otprilike trećinu kadra, dodirnite šarenicu da se izoštri i fotografirajte ponovno.",
    "eyelid": "Vaša vjeđa na ovoj fotografiji prekriva dio šarenice, pa tu fotografiju nismo upotrijebili: studio bi morao "
              "naslikati šarenicu preko vjeđe, a to izgleda lažno. Molimo snimite je ponovno: gledajte ravno u objektiv, "
              "ne ukoso, širom otvorenog oka, vrhom prsta nježno podignite gornju vjeđu i pazite da trepavice i maskara "
              "ne prelaze preko šarenice.",
    "closer": "Približite se ili upotrijebite zum 2x: šarenica ima {px} px, a nama treba {good} px ili više.",
    "fibres": "Vlakna još nisu jasno vidljiva. Dodirnite šarenicu na zaslonu da se kamera izoštri na nju, oslonite "
              "telefon na nešto čvrsto i fotografirajte ponovno.",
    "open": "Širom otvorite oko: gledajte ravno naprijed i vrhom prsta nježno podignite gornju vjeđu, tako da ni vjeđa ni "
            "trepavice ne prelaze preko šarenice. Trepavice preko šarenice na umjetničkom djelu izgledaju kao tamne "
            "pruge.",
    "on_pupil": "Odsjaj je na vašoj zjenici. Nagnite glavu ili pomaknite svjetlo u stranu, inače ćemo zjenicu morati "
                "obnoviti kao običnu tamu.",
    "reflection": "Pronašli smo odsjaj; uklonit ćemo ga automatski.",
    "glare": "Odsjaj prekriva dio vlakana šarenice, a ono što prekriva mora se rekonstruirati. Okrenite se tako da prozor "
             "ili lampa budu sa strane, a ne ravno ispred vas.",
    "soft": "Snimka je ispala malo mutna. Upotrijebite stražnju kameru uz zum 2x, dodirnite šarenicu da se izoštri i "
            "držite telefon mirno; prednje kamere s ove udaljenosti uopće ne mogu izoštriti sliku.",
    "no_lock": "Nismo mogli pouzdano pronaći okrugli rub vaše šarenice. Smjestite jedno oko u središte kadra, s malo "
               "prostora oko njega, i pazite da vam vjeđa ne smeta.",
    "good": "Odlična snimka. Vaša vlastita vlakna dovoljno su oštra za umjetničko djelo u punoj veličini.",
    "ok": "Od ovoga će nastati lijepo umjetničko djelo. Snimka iz veće blizine ili mirnija snimka sačuvala bi više detalja "
          "vaših vlastitih vlakana.",
    "weak": "Snimka je mala ili malo mutna, pa će se više sitnih detalja morati rekonstruirati. Iz veće blizine i mirnije "
            "dobit ćete vjernije umjetničko djelo.",
    "glare_ok": "Od ovoga će nastati lijepo umjetničko djelo. Snimka bez odsjaja na vašoj šarenici sačuvala bi više "
                "detalja vaših vlastitih vlakana.",
    "glare_weak": "Odsjaj prekriva prevelik dio vaše šarenice, pa bi se vlakna ispod njega morala rekonstruirati. "
                  "Pomaknite svjetlo u stranu i fotografirajte ponovno.",
    "unlocked": "Pronašli smo oko, ali nismo mogli pouzdano pronaći rub šarenice, pa bi izrez bio netočan. Molimo snimite "
                "još jednu fotografiju.",
}
