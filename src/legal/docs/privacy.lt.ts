// Privatumo politika (BDAR 13 straipsnis): the Lithuanian twin of `en` in src/legal/docs/privacy.ts,
// same section ids and blocks in the same order. Written from the same facts as the English file (see its header:
// what the code really does on 2026-09-29) and to be kept in step with it. GDPR is "BDAR" (Bendrasis duomenų apsaugos
// reglamentas) and its articles are cited the Lithuanian way ("BDAR 6 straipsnio 1 dalies f punktas").
// Not reviewed by a lawyer. Keep every sentence true when the code or a service changes.
import type { LegalDoc } from '../types';
import { ORDER_EMAIL_SENDER, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';

const companyLt = company('lt');
const addressLt = address('lt');
const WITHDRAWAL_ONLINE_LT = WITHDRAWAL_ONLINE.lt;

// What the online withdrawal function keeps (the "withdrawal" section), as WITHDRAW_PRIVACY.en
const WITHDRAW_PRIVACY_LT = `Jei sutarties atsisakote mūsų internetine funkcija (mygtukas „${WITHDRAWAL_ONLINE_LT.button}“, žr. [Teisė atsisakyti sutarties](doc:withdrawal#online)), Jūsų pareiškimą apie sutarties atsisakymą saugome kartu su Jūsų užsakymu: Jūsų vardą ir pavardę, el. pašto adresą, užsakymo numerį, pareiškimo tekstą ir jo gavimo datą bei laiką. Juo naudojamės, kad sustabdytume darbą su Jūsų failu, jei dar nepradėjome, el. paštu atsiųstume Jums gavimo patvirtinimą su pareiškimo turiniu, data ir laiku ir grąžintume pinigus. Be to, kiekvieną pareiškimą gauname el. paštu: po vieną arba, jei pareiškimas neatitinka nė vieno mūsų užsakymo ar susijęs su niekada neapmokėtu užsakymu, vienoje dienos suvestinėje. Jei sutarties atsisakymas įsigalioja, mūsų kasdienis automatinis valymas ištrina Jūsų užsakymo vaizdus, kai nuo sutarties atsisakymo praeina 14 dienų (jei Jūsų mokėjimas dar buvo apdorojamas, tik jam pasibaigus); užsakymo įrašas su Jūsų pareiškimu lieka (žr. [Kiek laiko saugome Jūsų duomenis](#retention)). Jei Jūsų pateikti duomenys neatitinka nė vieno mūsų užsakymo (be nuorodos iš Jūsų užsakymo puslapio ar sutarties atsisakymo nuorodos užsakymo patvirtinimo el. laiške el. pašto adresas turi būti tas, kurį nurodėte apmokėjimo metu), pareiškimą saugome atskirai, patikriname rankiniu būdu, vis tiek el. paštu atsiunčiame Jums gavimo patvirtinimą (laikydamiesi skyriuje [Sutarties atsisakymas internetu](doc:withdrawal#online) nurodytų piktnaudžiavimo prevencijos ribų) ir automatiškai jį ištriname praėjus maždaug 13 mėnesių nuo mėnesio, kurį jį gavome, pabaigos.`;

// The admin log and the admin sign-in guard, as ADMIN_LOG.en
const ADMIN_LOG_LT = {
  log: 'Kai tvarkome užsakymą savo administravimo skydelyje, pavyzdžiui, po kokybės patikros išleidžiame failą, dar kartą išsiunčiame el. laišką, grąžiname pinigus ar ištriname failus, skydelis padaro įrašą mūsų administravimo žurnale: kas padaryta, kada, kokiam užsakymo numeriui ir kuo baigėsi. Administravimo žurnale nėra vaizdų, el. pašto adresų ir nuorodų. Teisinis pagrindas: mūsų teisėtas interesas saugiai ir atsekamai tvarkyti užsakymus (BDAR 6 straipsnio 1 dalies f punktas). Žurnalas automatiškai ištrinamas po 24 mėnesių; įrašai apie užsakymą taip pat saugomi kartu su to užsakymo įrašu tol, kol saugomas pats įrašas (žr. [Kiek laiko saugome Jūsų duomenis](#retention)).',
  signin: 'Mūsų administravimo skydelis skirtas tik mums. Kad niekas negalėtų atspėti jo rakto, po nesėkmingo prisijungimo išsaugoma IP adreso, iš kurio jis atliktas, maiša, sudaryta slaptu raktu, bet niekada ne pats adresas; ji automatiškai ištrinama po 2 dienų. Teisinis pagrindas: mūsų teisėtas interesas užtikrinti savo sistemų saugumą (BDAR 6 straipsnio 1 dalies f punktas).',
};

// The admin panel's usage statistics and its admin log, as OPS.en
const OPS_LT = {
  events:
    'Kad matytume, ar paslauga veikia, kaip greitai ir kiek kainuoja, mūsų serveris mūsų privačioje Supabase saugykloje ES įrašo nedidelius techninius įvykius. Pavyzdžiui: kad nuotrauka buvo patikrinta (su rezultatu, pavyzdžiui, „akis nerasta“, įrenginio rūšimi, pavyzdžiui, iPhone, Android ar kompiuteris, informacija, ar nuotrauka padaryta kamera, ar paimta iš galerijos, ir puslapio kalba), kad buvo pašalinti atspindžiai, kad buvo sukurta peržiūra ar užsakytas failas ir kiek laiko tai užtruko, arba kad užklausa nepavyko (su jos klaidos kodu). Mūsų administravimo skydelis juos mums rodo, dažniausiai kaip dienos suvestines.',
  content:
    '**Šiuose įvykiuose nėra jokio vaizdo, Jūsų įvesto teksto, vardo, el. pašto adreso, IP adreso, naršyklės identifikatoriaus (user agent) ir nuorodos.** Nemokamos peržiūros įvykių su Jumis susieti neįmanoma. Tik įvykiuose apie apmokėto užsakymo failo kūrimą yra ir to užsakymo numeris, kad galėtume rasti lėtą ar nepavykusį kūrimą; per mūsų užsakymų įrašus šis numeris susijęs su Jūsų užsakymu.',
  basis:
    'Teisinis pagrindas: mūsų teisėtas interesas patikimai teikti paslaugą, rasti gedimus ir kontroliuoti jos sąnaudas (BDAR 6 straipsnio 1 dalies f punktas). Įvykiai ir iš jų sudarytos dienos suvestinės automatiškai ištrinami po 12 mėnesių. Bet kada galite nesutikti su tokiu tvarkymu (žr. [Jūsų teisės](#rights)).',
  admin: ADMIN_LOG_LT.log,
  signin: ADMIN_LOG_LT.signin,
};

const repLt = SELLER.representative ? ` Jai atstovauja ${SELLER.representative}.` : '';
const senderLt = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: el. laiškų apie Jūsų užsakymą siuntimas (Jūsų užsakymo puslapio nuoroda, užsakymo patvirtinimas ir, jei atsisakote sutarties, gavimo patvirtinimas). Šios paslaugos serveriai gali būti už ES ribų.`];
const hostingerLt = ORDER_EMAIL_SENDER === 'Hostinger'
  ? 'Hostinger: mūsų el. paštas, pašto dėžutė info@snapeyes.com, įskaitant el. laiškus apie Jūsų užsakymą.'
  : 'Hostinger: mūsų pašto dėžutė info@snapeyes.com.';

export const lt: LegalDoc = {
  title: 'Privatumo politika',
  description:
    'Kaip SnapEyes tvarko Jūsų akies nuotrauką, Jūsų peržiūrą ir, jei užsisakote, Jūsų užsakymo duomenis: ką tvarkome, kodėl, kokiomis paslaugomis, kiek laiko ir kokias teises turite.',
  lead:
    'Ši politika paaiškina, kas vyksta su Jūsų duomenimis, kai naudojatės svetaine snapeyes.com: nemokama peržiūra ir, jei užsisakote, Jūsų skaitmeniniu kūriniu. Trumpai: Jūsų nuotrauka naudojama tik Jūsų kūriniui sukurti, niekada kieno nors tapatybei nustatyti ir niekada DI mokyti. Nemokamų peržiūrų nesaugome. Apmokėtų užsakymų failai saugomi 12 mėnesių, kad galėtumėte juos vėl atsisiųsti, tada ištrinami.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'controller',
      title: 'Kas atsako už Jūsų duomenis',
      blocks: [
        `Jūsų duomenų valdytojas yra ${companyLt} (įmonės kodas ${SELLER.code}), ${addressLt}. SnapEyes yra jos prekės ženklas.${repLt}`,
        `Visais privatumo klausimais ir norėdami pasinaudoti bet kuria savo teise, rašykite adresu ${MAIL}. Duomenų apsaugos pareigūno nesame paskyrę.`,
      ],
    },
    {
      id: 'website',
      title: 'Kai lankotės svetainėje',
      blocks: [
        'Kai atidarote svetainės snapeyes.com puslapį, Jūsų naršyklė mūsų prieglobos paslaugų teikėjui Vercel siunčia techninius duomenis, pavyzdžiui, Jūsų IP adresą, datą ir laiką, užklaustą puslapį ir naršyklės tipą (user agent). Vercel šių duomenų reikia puslapiui pateikti ir paslaugai apsaugoti nuo atakų. Jie trumpai saugomi serverio žurnaluose ir tada ištrinami.',
        'Kad galėtume pasiūlyti kainas Jūsų valiuta, mūsų serveris taip pat gali nuskaityti šalį, kurią Vercel nustato pagal Jūsų IP adresą (pavyzdžiui, „AU“). Ji naudojama tik tam pasiūlymui, niekada nekeičia Jūsų matomų kainų ir nėra saugoma.',
        'Teisinis pagrindas: mūsų teisėtas interesas turėti saugią ir veikiančią svetainę (BDAR 6 straipsnio 1 dalies f punktas).',
        'Mūsų šriftai teikiami iš mūsų pačių serverio, todėl jokie duomenys nepatenka į Google Fonts ar kitą šriftų paslaugą. Šioje svetainėje nenaudojame kitų įmonių analitikos, reklamos ar sekimo priemonių ir niekas Jūsų neseka iš puslapio į puslapį ar tarp svetainių. Mūsų pačių anoniminė paslaugos statistika aprašyta skyriuje [Paslaugos statistika ir mūsų administravimo žurnalas](#operations).',
      ],
    },
    {
      id: 'preview',
      title: 'Jūsų nemokama peržiūra',
      blocks: [
        'Kad sukurtume Jūsų peržiūrą, iš savo naršyklės mūsų serverio funkcijoms siunčiate vieną ar kelias akies nuotraukas. Ten nuotrauka apdorojama atmintyje: randame rainelę, ją iškerpame, patikriname, ar ji pakankamai ryški ir šviesi, pašaliname atspindžius, su Google Gemini API atkuriame smulkias skaidulas ir perteikiame rainelę Jūsų matomais stiliais. Rezultatas grįžta į Jūsų naršyklę. Visi duomenų perdavimai šifruojami (HTTPS).',
        '**Jūsų nuotraukos, rainelės iškarpos ir peržiūros savo serveriuose nesaugome.** Jos ištrinamos, kai užklausa baigiasi. Peržiūra lieka Jūsų naršyklėje, kol uždarote puslapį (kol esate mokėjimo puslapyje, Jūsų naršyklės skirtuko sesijos saugykloje: žr. [Slapukai ir vietinė saugykla](#storage)), nebent ją išsisaugote patys. Rainelės iškarpą ir patvirtintą peržiūrą saugome tik tada, kai pradedate užsakymą: žr. [Kai užsisakote](#orders).',
        'Google apdoroja vaizdą, kad jį atkurtų. Naudojamės mokama Google API paslauga, pagal kurios sąlygas Google nenaudoja vaizdų savo produktams tobulinti ar savo modeliams mokyti. Google gali ribotą laiką saugoti užklausas, tik kad nustatytų piktnaudžiavimą ir įstatymų reikalaujamiems atskleidimams.',
        'Teisinis pagrindas: Jūs prašote sukurti peržiūrą, o tam reikalinga nuotrauka (BDAR 6 straipsnio 1 dalies b punktas, veiksmai, atliekami Jūsų prašymu).',
        'Mūsų programa automatiškai nusprendžia, ar nuotrauką galima panaudoti (pavyzdžiui, kai ji per neryški ar per tamsi). Šis sprendimas nesukelia Jums jokių teisinių ar panašiai reikšmingų pasekmių: galite tiesiog padaryti kitą nuotrauką.',
      ],
    },
    {
      id: 'iris',
      title: 'Jūsų rainelė niekada nenaudojama tapatybei nustatyti',
      blocks: [
        'Teoriškai pagal rainelę galima atpažinti žmogų. Mes to nedarome. Niekada nekuriame, nelyginame ir nesaugome rainelės šablono ar kito biometrinio identifikatoriaus, niekada nenaudojame Jūsų vaizdų kieno nors tapatybei nustatyti ar patikrinti, niekada jų neparduodame ir niekada nenaudojame DI mokyti, nei savo, nei kieno nors kito.',
        'Naudokite tik savo akį arba kito žmogaus akį, jei jis su tuo sutiko. Vaiko atveju sutikti turi vienas iš tėvų, globėjas ar rūpintojas.',
        'Jei pridedate kitų žmonių akis (pavyzdžiui, Couple Duo kūriniui), jų vaizdus tvarkome tik tam kūriniui, su kuriuo jie sutiko, sukurti. Teisinis pagrindas: Jūsų ir mūsų teisėtas interesas sukurti tą kūrinį (BDAR 6 straipsnio 1 dalies f punktas). Parodykite jiems šią politiką.',
      ],
    },
    {
      id: 'measurements',
      title: 'Techniniai matavimai (be vaizdų)',
      blocks: [
        'Su kiekviena nuotrauka mūsų serveris į savo žurnalus įrašo vieną eilutę, kad galėtume tobulinti fotografavimo patarimus ir paslaugos kokybę. Joje yra nuotraukos matavimai (pavyzdžiui, rainelės dydis pikseliais, ryškumas, šviesumas, šviesos spalvinis atspalvis ir tai, ar nuotrauką buvo galima panaudoti), techniniai duomenys apie Jūsų įrenginį (naršyklės tipas ir versija, ekrano dydis, ar nuotrauka padaryta kamera, ar paimta iš galerijos) ir, jei atsakote į mūsų neprivalomus klausimus apie kadrą, Jūsų atsakymai. Joje nėra vaizdo, vardo ir kontaktinių duomenų.',
        'Šios žurnalo eilutės trumpai saugomos pas mūsų prieglobos paslaugų teikėją ir tada ištrinamos. Teisinis pagrindas: mūsų teisėtas interesas tobulinti paslaugą (BDAR 6 straipsnio 1 dalies f punktas). Bet kada galite nesutikti su tokiu tvarkymu (žr. [Jūsų teisės](#rights)).',
      ],
    },
    {
      id: 'operations',
      title: 'Paslaugos statistika ir mūsų administravimo žurnalas',
      blocks: [OPS_LT.events, OPS_LT.content, OPS_LT.basis, OPS_LT.admin, OPS_LT.signin],
    },
    {
      id: 'orders',
      title: 'Kai užsisakote',
      blocks: [
        'Kai pradedate užsakymą, į mūsų privačią saugyklą įkeliami du kiekvienos akies vaizdai, kad Jūsų failas būtų sukurtas būtent iš to, ką matėte: iš Jūsų nuotraukos iškirptas kvadratas aplink rainelę (su pašalintais atspindžiais) ir Jūsų patvirtinta peržiūra. **Visa Jūsų telefono nuotrauka nesaugoma, net ir užsakymo atveju.** Užsakymo, kuris neapmokamas per 24 valandas, apmokėti nebegalima. Tada kartą per dieną veikiantis automatinis valymas ištrina jo vaizdus ir įrašus, paprastai per dvi dienas nuo užsakymo ir ne vėliau kaip per 30 dienų.',
        'Kad įkėlimai neviršytų ribų, mūsų serveris kiekvienam įkėlimui dar įrašo nedidelę žymę (jo dydį, dieną ir užsakymo numerį, be vaizdo). Šios žymės automatiškai ištrinamos po kelių dienų.',
        'Kad parduotume ir pristatytume Jūsų kūrinį, tvarkome: užsakymą (užsakymo numerį, datą, akis, stilių, išdėstymą, Jūsų pridėtus vardus ar užrašą, kalbą, kainą), Jūsų el. pašto adresą (jį įvedate mokėjimo puslapyje), iš Stripe gaunamą mokėjimo būseną, Jūsų sutikimą, kad pradėtume iš karto (žr. [Teisė atsisakyti sutarties](doc:withdrawal)), ir Jūsų užsakymo failus: du minėtus kiekvienos akies vaizdus, kiekvienos akies 4096 px atvaizdą ir baigtą kūrinį su techniniais kokybės įrašais.',
        'Šiuos failus saugome privačioje Supabase saugykloje, esančioje ES. Juos pasiekiate per savo užsakymo puslapį, kurio nuorodą atsiunčiame Jums el. paštu; joje yra privatus raktas, todėl kiekvienas, turintis nuorodą, gali atsisiųsti Jūsų kūrinį. Kiekviena ten sukurta atsisiuntimo nuoroda nustoja galioti po 7 dienų.',
        'Galime peržiūrėti Jūsų užsakymo failus, kad patikrintume jų kokybę, pavyzdžiui, kai mūsų automatinė patikra praneša apie skirtumą nuo Jūsų patvirtintos peržiūros.',
        'Teisinis pagrindas: sutartis su Jumis (BDAR 6 straipsnio 1 dalies b punktas); buhalterinės apskaitos įrašams: mūsų teisinės prievolės (BDAR 6 straipsnio 1 dalies c punktas).',
        'Kai pereinate į mokėjimo puslapį, kartu su Jūsų mokėjimu perduodame Stripe užsakymo duomenis: užsakymo numerį, kainą, akių skaičių, stilių, išdėstymą, kalbą, Jūsų pridėtus vardus ar užrašą ir Jūsų sutikimo versiją bei laiką. Stripe juos saugo su mokėjimo įrašu, o mes juos iš ten nuskaitome, kad sukurtume būtent tą kūrinį, už kurį sumokėjote.',
        'Mokėjimas: Jūsų mokėjimą apdoroja Stripe. Viso Jūsų kortelės numerio niekada nematome. Stripe mokėjimo duomenis taip pat tvarko pagal savo privatumo politiką, sukčiavimo prevencijos tikslais ir savo teisinėms prievolėms vykdyti.',
        'Jūsų el. pašto adreso mums reikia, kad atsiųstume Jums užsakymo puslapio nuorodą ir užsakymo patvirtinimą. Be jo galėtumėte prarasti prieigą prie savo failo.',
      ],
    },
    {
      id: 'email',
      title: 'Kai mums rašote',
      blocks: [
        'Jei rašote mums el. laišką, Jūsų adresą ir laišką naudojame, kad Jums atsakytume ir, jei jis susijęs su užsakymu, tą užsakymą sutvarkytume. Teisinis pagrindas: užsakymų atveju BDAR 6 straipsnio 1 dalies b punktas, kitais atvejais mūsų teisėtas interesas Jums atsakyti (BDAR 6 straipsnio 1 dalies f punktas). Jei atsiunčiate mums nuotraukų, pavyzdžiui, savo akies, kad patartume, kaip padaryti geresnį kadrą, jas naudojame tik Jūsų prašymui įvykdyti. Jūsų el. laiškus kartu su nuotraukomis saugome tol, kol jų reikia Jūsų prašymui ir tolesniems veiksmams.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Kai sutarties atsisakote internetu',
      blocks: [
        WITHDRAW_PRIVACY_LT,
        'Teisinis pagrindas: mūsų teisinė prievolė priimti Jūsų sutarties atsisakymą ir jį Jums patvirtinti (BDAR 6 straipsnio 1 dalies c punktas) ir sutartis su Jumis (BDAR 6 straipsnio 1 dalies b punktas). Pareiškimą kaip įrodymą saugome su Jūsų užsakymo įrašu tol, kol saugomas tas įrašas (žr. [Kiek laiko saugome Jūsų duomenis](#retention)).',
      ],
    },
    {
      id: 'services',
      title: 'Kokiomis paslaugomis naudojamės',
      blocks: [
        'SnapEyes veikia naudojant šias paslaugas:',
        {
          ul: [
            'Vercel: svetainės ir serverio funkcijų, kurios kuria Jūsų peržiūrą ir Jūsų failą, priegloba. Vercel duomenų centrai gali būti už ES ribų, pavyzdžiui, JAV.',
            'Google (Gemini API): DI rainelės atkūrimas ir Jūsų nuotraukos patikros. Google serveriai gali būti už ES ribų.',
            'Supabase: užsakymų failų privati saugykla ES regione.',
            'Stripe: mokėjimų apdorojimas, su skyriuje [Kai užsisakote](#orders) nurodytais užsakymo duomenimis.',
            hostingerLt,
            ...senderLt,
          ],
        },
        `Šie paslaugų teikėjai tvarko Jūsų duomenis mūsų vardu ir pagal mūsų nurodymus (Stripe iš dalies kaip savarankiškas duomenų valdytojas, žr. [Kai užsisakote](#orders)). Kai duomenys perduodami už ES ar EEE ribų, tai daroma taikant paslaugų teikėjų siūlomas apsaugos priemones, pavyzdžiui, Europos Komisijos standartines sutarčių sąlygas arba ES ir JAV duomenų privatumo sistemą. Šių apsaugos priemonių kopijos galite paprašyti adresu ${MAIL}.`,
        'Jūsų duomenų neparduodame ir niekam kitam neperduodame, nebent to reikalauja įstatymai.',
      ],
    },
    {
      id: 'retention',
      title: 'Kiek laiko saugome Jūsų duomenis',
      blocks: [
        {
          dl: [
            ['Nemokamos peržiūros', 'Mes jų nesaugome. Jos ištrinamos, kai užklausa baigiasi.'],
            ['Neapmokėti užsakymai', 'Užsakymo, kuris neapmokamas per 24 valandas, apmokėti nebegalima. Mūsų kasdienis automatinis valymas ištrina jo vaizdus ir įrašus, paprastai per dvi dienas nuo užsakymo ir ne vėliau kaip per 30 dienų.'],
            ['Įkėlimų ir pareiškimų žymės', 'Nedideli skaitikliai be vaizdų, vardų ir el. pašto adresų (gavimo patvirtinimų skaitiklyje yra tik trumpa el. pašto adreso maiša), automatiškai ištrinami po kelių dienų; mėnesiniai gavimo patvirtinimų skaitikliai ištrinami praėjus maždaug 40 dienų nuo jų mėnesio pabaigos.'],
            ['Apmokėti užsakymai', 'Jūsų užsakymo failai saugomi 12 mėnesių nuo apmokėjimo, kad galėtumėte juos vėl atsisiųsti iš savo užsakymo puslapio, tada juos ištrina mūsų kasdienis automatinis valymas. Jūsų prašymu juos ištriname anksčiau; po to Jūsų užsakymo puslapis failo nebegali pateikti.'],
            ['Užsakymai, kurių sutarties atsisakyta', 'Jei sutarties atsisakymas įsigalioja, mūsų kasdienis valymas ištrina užsakymo vaizdus, kai nuo sutarties atsisakymo praeina 14 dienų (jei mokėjimas dar buvo apdorojamas, jam pasibaigus).'],
            ['Pareiškimai apie sutarties atsisakymą, neatitinkantys jokio užsakymo', 'Saugomi atskirai, tikrinami rankiniu būdu ir automatiškai ištrinami praėjus maždaug 13 mėnesių nuo mėnesio, kurį juos gavome, pabaigos.'],
            ['Užsakymų įrašai', 'Kai failai ištrinami (po 12 mėnesių, po sutarties atsisakymo arba Jūsų prašymu), apmokėto užsakymo įrašą saugome: užsakymo numerį, datą, kainą, mokėjimą ir bet kokį pinigų grąžinimą, Jūsų el. pašto adresą, užsakyto kūrinio duomenis (tarp jų gali būti Jūsų pridėti vardai ar užrašas), Jūsų sutikimą, kad pradėtume iš karto, jei atsisakėte sutarties, Jūsų pareiškimą apie sutarties atsisakymą ir mūsų administravimo žurnalo įrašus apie Jūsų užsakymą. Jokių vaizdų. Jį saugome kaip sutarties įrodymą ir buhalterinei apskaitai tiek laiko, kiek reikalauja Lietuvos buhalterinės apskaitos ir mokesčių teisės aktai.'],
            ['Serverio žurnalai ir matavimai', 'Trumpai saugomi pas mūsų prieglobos paslaugų teikėją, tada ištrinami.'],
            ['Paslaugos statistika', 'Techniniai įvykiai ir jų dienos suvestinės (žr. [Paslaugos statistika ir mūsų administravimo žurnalas](#operations)): automatiškai ištrinami po 12 mėnesių.'],
            ['Administravimo žurnalas', 'Ką padarėme su užsakymu savo administravimo skydelyje: automatiškai ištrinama po 24 mėnesių; įrašai apie užsakymą lieka su jo užsakymo įrašu.'],
            ['Nesėkmingi prisijungimai prie mūsų administravimo skydelio', 'IP adreso maiša, sudaryta slaptu raktu, automatiškai ištrinama po 2 dienų.'],
            ['El. laiškai', 'Tol, kol jų reikia Jūsų prašymui ir tolesniems veiksmams.'],
          ],
        },
      ],
    },
    {
      id: 'rights',
      title: 'Jūsų teisės',
      blocks: [
        'Bet kuriuo metu turite šias teises:',
        {
          ul: [
            'Teisė susipažinti: sužinoti, kokius Jūsų duomenis turime, ir gauti jų kopiją (BDAR 15 straipsnis).',
            'Teisė reikalauti ištaisyti: kad neteisingi duomenys būtų ištaisyti (BDAR 16 straipsnis).',
            'Teisė reikalauti ištrinti: kad Jūsų duomenys būtų ištrinti, pavyzdžiui, Jūsų užsakymo failai dar nepasibaigus 12 mėnesių (BDAR 17 straipsnis).',
            'Teisė apriboti tvarkymą: kad tvarkymas būtų apribotas, kol aiškinamasi (BDAR 18 straipsnis).',
            'Teisė į duomenų perkeliamumą: gauti mums pateiktus duomenis įprastu, kompiuterio skaitomu formatu (BDAR 20 straipsnis).',
            'Teisė nesutikti: dėl priežasčių, susijusių su Jūsų konkrečia situacija, bet kuriuo metu nesutikti, kad duomenys būtų tvarkomi remiantis mūsų teisėtais interesais (BDAR 21 straipsnis).',
          ],
        },
        `Norėdami pasinaudoti bet kuria iš šių teisių, rašykite adresu ${MAIL}. Atsakome per vieną mėnesį.`,
        'Taip pat turite teisę pateikti skundą priežiūros institucijai. Mūsų priežiūros institucija yra Valstybinė duomenų apsaugos inspekcija (VDAI) Vilniuje, [vdai.lrv.lt](https://vdai.lrv.lt). Taip pat galite kreiptis į tos ES šalies, kurioje gyvenate ar dirbate, priežiūros instituciją.',
      ],
    },
    {
      id: 'storage',
      title: 'Slapukai ir vietinė saugykla',
      blocks: [
        'Ši svetainė nenaudoja slapukų. Joje nėra kitų įmonių analitikos, reklamos ar sekimo priemonių.',
        'Kai kalbos jungikliu pasirenkate kalbą, Jūsų naršyklė šį pasirinkimą įsimena savo vietinėje saugykloje raktu „snapeyes.lang“ (reikšmė yra kalbos kodas, pavyzdžiui, „lt“). Jis niekada nesiunčiamas mums ir bet kada galite jį ištrinti naršyklės nustatymuose. Jis būtinas Jūsų pageidaujamai funkcijai, todėl sutikimo nereikia (Direktyvos 2002/58/EB, e. privatumo direktyvos, 5 straipsnio 3 dalis).',
        'Jei pas mus patenkate per nuorodą su kainomis kita valiuta (pavyzdžiui, Australijos doleriais) arba valiutą pasirenkate mūsų valiutos jungikliu ar mūsų pasiūlyme rodyti kainas Jūsų valiuta, Jūsų naršyklė šį pasirinkimą taip pat įsimena savo vietinėje saugykloje raktu „snapeyes.market“ (pavyzdžiui, „au“, arba „eu“, kai atsisakote to pasiūlymo), kad svetainė ir toliau rodytų tas pačias kainas. Mūsų puslapiai jį perduoda savo nuorodose (m=au) ir siunčia kartu su užsakymu, kad Jums būtų taikomos Jūsų matytos kainos. Bet kada galite jį ištrinti naršyklės nustatymuose; jis būtinas Jūsų pageidaujamai funkcijai, todėl ir šiuo atveju sutikimo nereikia (Direktyvos 2002/58/EB, e. privatumo direktyvos, 5 straipsnio 3 dalis).',
        'Kai užsisakote, puslapis Jūsų naršyklės skirtuko sesijos saugykloje dar laiko du įrašus. Sesijos saugykla priklauso tik tam skirtukui ir ištrinama, kai jį uždarote:',
        {
          ul: [
            '„snapeyes.order“: kuriamo užsakymo numeris ir jo privatus raktas, kad puslapis galėtų tęsti Jūsų užsakymą, pavyzdžiui, kai grįžtate iš mokėjimo puslapio. Jis pašalinamas, kai tame skirtuke atsidaro Jūsų apmokėto užsakymo puslapis, ir pakeičiamas, kai pradedate naują užsakymą.',
            '„snapeyes.checkout“: tik kol esate mokėjimo puslapyje, Jūsų kūrinys toks, kokį jį palikote (rainelių iškarpos iš Jūsų nuotraukų, peržiūros, stilius, išdėstymas ir vardai), kad grįžus iš mokėjimo puslapio jis vėl būtų rodomas. Jis pašalinamas, kai tik grįžtate arba kai tame skirtuke atsidaro Jūsų apmokėto užsakymo puslapis.',
          ],
        },
        'Puslapis juos naudoja tik Jūsų užsakymui ir jie tam būtini, todėl sutikimo taip pat nereikia (Direktyvos 2002/58/EB, e. privatumo direktyvos, 5 straipsnio 3 dalis).',
        'Kai mokate, Stripe mokėjimo puslapis gali naudoti savo slapukus, reikalingus saugiam mokėjimui ir sukčiavimo prevencijai; ten taikoma Stripe privatumo ir slapukų politika.',
      ],
    },
    {
      id: 'required',
      title: 'Ar privalote pateikti mums duomenis?',
      blocks: ['Ne. Tačiau be nuotraukos negalime sukurti peržiūros, o be el. pašto adreso ir apmokėjimo negalime įvykdyti užsakymo.'],
    },
    {
      id: 'changes',
      title: 'Šios politikos pakeitimai',
      blocks: ['Šią politiką atnaujiname, kai keičiasi mūsų paslauga ar teisės aktai. Viršuje nurodyta data rodo galiojančią redakciją.'],
    },
  ],
};
