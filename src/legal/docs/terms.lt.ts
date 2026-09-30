// Pardavimo sąlygos: the Lithuanian twin of `en` in src/legal/docs/terms.ts, same section ids and blocks in the same
// order, the same facts from src/landing/config.ts (through ../facts). Everything the English header says holds here
// too: no ODR link, no VAT number, no promise the code does not keep, the right of withdrawal ends when making the file
// begins (or with the 14-day period, counted as withdraw.py period_end counts it), the seller line has no phone (owner
// decision).
// Lithuanian law behind the wording (Civilinis kodeksas, Šeštoji knyga, nuotolinės sutartys):
//  - 6.228(8) str. 3 d.: the order button says "užsakymas su prievole sumokėti" or an equally unambiguous wording. Our
//    "Pereiti prie apmokėjimo" places no order; the binding order is Stripe's pay button (Stripe Checkout, locale "lt"),
//    which the terms say ("užsakymą su prievole sumokėti pateikiate, kai ... patvirtinate mokėjimą mokėjimo mygtuku").
//    Whether Stripe's "Mokėti" alone is unambiguous enough is a question for a lawyer, as the German "Bezahlen" is.
//  - 6.228(10): 14 days from the conclusion of the contract; 2 d. 13 p. a and b, the digital content exception (express
//    consent to start early, acknowledgement of losing the right), c is the confirmation email; 11-15 d. the online
//    function ("atsisakyti sutarties čia", "patvirtinti sutarties atsisakymą"). 6.228(11): refund within 14 days.
//  - CK 1.118 and 1.121 str. 2 d.: a term starts the next day and a last day on a non-working day moves to the next
//    working day, as withdraw.py period_end counts it.
//  - Out of court: Valstybinė vartotojų teisių apsaugos tarnyba (VVTAT); no ODR link (the platform closed on 20 July 2025).
//  - VAT: the owner's sentence word for word wherever a price is final, "MB „Portretizuokis“ nėra PVM mokėtoja, todėl PVM
//    netaikomas.", built from company('lt') so that it follows config.ts.
//  - The contract languages are named ("Sutarties kalbos: lietuvių, anglų, vokiečių ir vengrų."): the English, German and
//    Hungarian terms name Lithuanian too (the build checks it, scripts/check_texts.mjs).
// Not reviewed by a lawyer.
import type { LegalDoc, LegalSection } from '../types';
import { DELIVERY_MAX_HOURS, HU_PRICES, MAIL, MAX_EYES, PRICE_CENTS, SELLER, address, company, eur, huf, phoneSuffix, representedSuffix } from '../facts';
import { valandasAcc } from '../../shared/lt';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE } from '../../shared/legal';

const companyLt = company('lt');
const addressLt = address('lt');
const phoneSuffixLt = phoneSuffix('lt');
const representedSuffixLt = representedSuffix('lt');
const eurLt = (cents: number) => eur(cents, 'lt');
const WITHDRAWAL_ONLINE_LT = WITHDRAWAL_ONLINE.lt;
const CHECKOUT_LEGAL_LT = CHECKOUT_LEGAL.lt;

const TRANSPARENCY_LT = 'Spalva paimta iš Jūsų pačių nuotraukos. Kur telefonas neužfiksavo smulkiausių skaidulų, jas atkuria mūsų DI.';
const ART = 'Celestial Gold, Deep Nebula, Emerald Aurora, Obsidian Smoke, Supernova';
const PX = '4096 px';
const SQUARE = '4096 × 4096 px';

export const lt: LegalDoc = {
  title: 'Pardavimo sąlygos',
  description:
    'SnapEyes skaitmeninio rainelės kūrinio užsakymo sąlygos: produktas, kainos, apmokėjimas, pristatymas, naudojimo licencija, teisė atsisakyti sutarties ir pretenzijos.',
  lead: 'Šios sąlygos taikomos kiekvienam užsakymui, pateiktam svetainėje snapeyes.com. Prieš užsisakant perskaitykite jas. Nemokama peržiūra siūloma be jokių įsipareigojimų.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'parties',
      title: 'Su kuo sudarote sutartį',
      blocks: [
        `Sutartį sudarote su ${companyLt}, mažąja bendrija pagal Lietuvos Respublikos teisę${representedSuffixLt}, įmonės kodas ${SELLER.code}, ${addressLt}, el. paštas ${MAIL}${phoneSuffixLt} (toliau vadinama „mes“ arba „SnapEyes“). Visi rekvizitai pateikti puslapyje [Rekvizitai](doc:imprint).`,
        'Mūsų pasiūlymas skirtas vartotojams. Jei Jums dar nėra 18 metų, paprašykite, kad užsakymą už Jus pateiktų vienas iš tėvų, globėjas ar rūpintojas.',
      ],
    },
    {
      id: 'product',
      title: 'Ką perkate',
      blocks: [
        `Personalizuotą skaitmeninį kūrinį, sukurtą iš Jūsų pačių akies (arba kelių akių) nuotraukos, Jūsų pasirinktu stiliumi, išdėstymu ir su Jūsų pasirinktu užrašu. Gausite vieną vaizdo failą (JPEG) be vandens ženklo: vienos akies kūrinys yra ${SQUARE}, kelių akių kūrinio ilgoji kraštinė yra ${PX}. Kūrinys pateikiamas tik kaip skaitmeninis failas, jį atsisiunčiant. Spaudinių, rėmelių ar kitų fizinių produktų neparduodame.`,
        `${TRANSPARENCY_LT} Todėl kūrinys yra meninis atkūrimas, o ne medicininis ar mikroskopinis vaizdas, ir jis netinka jokiems medicininiams tikslams ar asmens tapatybei nustatyti.`,
      ],
    },
    {
      id: 'preview',
      title: 'Jūsų peržiūra ir Jūsų failas',
      blocks: [
        'Prieš užsakymą matote nemokamą peržiūrą su vandens ženklu ir ją patvirtinate. Jūsų failas atitinka patvirtintą peržiūrą: ta pati akis, stilius, išdėstymas ir užrašas, tos pačios spalvos ir tonai, vieną kartą sukurta visa raiška. Visu dydžiu mūsų DI prideda smulkias skaidulų detales, kurių peržiūra dėl mažo dydžio parodyti negali, todėl pačios smulkiausios detalės gali šiek tiek skirtis nuo peržiūros.',
        'Jei Jūsų failas aiškiai skiriasi nuo patvirtintos peržiūros (pavyzdžiui, spalva, šviesumu ar vyzdžiu), tai yra trūkumas: žr. [Pretenzijos ir trūkumai](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'Kaip sudaroma sutartis',
      blocks: [
        `Mūsų svetainėje pateiktos peržiūros ir kainos dar nėra oferta (pasiūlymas sudaryti sutartį). Prieš mokėjimą galite patikrinti savo akis, stilių, išdėstymą ir užrašą ir ištaisyti bet kokias įvesties klaidas, grįždami atgal arba iš naujo fotografuodami. Tada mūsų mygtuku „${CHECKOUT_LEGAL_LT.continueButton}“ atidarote mūsų mokėjimo paslaugų teikėjo Stripe mokėjimo puslapį; šis mygtukas dar nepateikia užsakymo. Tame puslapyje įvedate savo el. pašto adresą ir mokėjimo duomenis ir galite juos pataisyti. Užsakymą su prievole sumokėti pateikiate, kai ten patvirtinate mokėjimą mokėjimo mygtuku.`,
        'Sutartis sudaroma, kai patvirtinamas Jūsų mokėjimas. Tada atsidaro Jūsų užsakymo puslapis, o jo nuorodą kartu su užsakymo patvirtinimu atsiunčiame Jums el. paštu. Kai tik tas el. laiškas išsiųstas, ten pradedame kurti Jūsų failą.',
        'Sutarties kalbos: lietuvių, anglų, vokiečių ir vengrų.',
        'Jūsų užsakymą saugome su sutarties duomenimis: užsakytas kūrinys, kaina, data, Jūsų el. pašto adresas ir Jūsų sutikimas, kad pradėtume iš karto. Jūsų užsakymo puslapyje šie duomenys matomi tol, kol saugome Jūsų užsakymą. Atskiros šių sąlygų kopijos kiekvienam užsakymui nesaugome. Vietoj to Jūsų užsakymo patvirtinimo el. laiške tekstu pateikiami Jūsų užsakymo duomenys, šios sąlygos ir informacija apie teisę atsisakyti sutarties su pavyzdine sutarties atsisakymo forma, užsakymo metu galiojusios redakcijos: išsaugokite tą el. laišką. Šį puslapį taip pat bet kada galite išsaugoti arba atsispausdinti.',
      ],
    },
    {
      id: 'prices',
      title: 'Kainos ir apmokėjimas',
      blocks: [
        {
          dl: [
            ['Viena akis, Studio Black', eurLt(PRICE_CENTS.studioBlack)],
            ['Viena akis su meniniu fonu', `${eurLt(PRICE_CENTS.artBackground)} (${ART})`],
            ['Dvi akys (Couple Duo), bet kuris stilius', eurLt(PRICE_CENTS.coupleDuo)],
            ['Kiekviena papildoma akis', `+${eurLt(PRICE_CENTS.extraEye)}, iki ${MAX_EYES} akių viename kūrinyje`],
          ],
        },
        `Visos kainos yra galutinės ir nurodytos eurais. ${companyLt} nėra PVM mokėtoja, todėl PVM netaikomas. Pristatymo išlaidų nėra.`,
        'Pirmiau pateikta lentelė yra mūsų standartinis kainoraštis. Kartkartėmis ribotą laiką kai kuriems atsitiktinai parinktiems lankytojams išbandome kitus kainoraščius. Visada mokate kainas, kurios Jums parodytos kūrinio puslapyje prieš apmokėjimą ir mokėjimo puslapyje, o Jūsų užsakymo patvirtinimo el. laiške nurodomas kainoraštis, kuris taikytas Jūsų užsakymui. Koks kainoraštis Jums rodomas, niekada nepriklauso nuo šalies, kurioje gyvenate, o tik nuo Jūsų pasirinktos rinkos (valiutos).',
        'Mokate iš anksto per mūsų mokėjimo paslaugų teikėją Stripe, mokėjimo puslapyje rodomais mokėjimo būdais.',
      ],
    },
    {
      id: 'delivery',
      title: 'Pristatymas',
      blocks: [
        `Jūsų užsakymo puslapis sukuria Jūsų failą, kai tik išsiunčiamas užsakymo patvirtinimo el. laiškas, paprastai per minutę nuo apmokėjimo; kūrimas paprastai užtrunka kelias minutes (maždaug pusę minutės vienai akiai). Jei uždarote puslapį, kol failas dar nebaigtas, kūrimas tęsiamas, kai vėl jį atidarote per el. laiške esančią nuorodą. Jei mūsų automatinė kokybės patikra pažymi failą, prieš jį pateikdami patys jį peržiūrime ir, kai jis paruoštas, parašome Jums el. laišką. **Vėliausiai per ${valandasAcc(DELIVERY_MAX_HOURS)} nuo Jūsų mokėjimo patvirtinimo Jūsų failą galėsite atsisiųsti savo užsakymo puslapyje.** Užsakymo puslapyje failą galite atsisiųsti bet kada, kol jį saugome: 12 mėnesių nuo apmokėjimo (žr. [privatumo politiką](doc:privacy)). Kiekviena ten sukurta atsisiuntimo nuoroda galioja 7 dienas; kaskart atidarius puslapį sukuriama nauja. Jei el. laišką praradote, parašykite mums.`,
        'Jūsų užsakymo puslapio nuorodoje yra privatus raktas: kiekvienas, kas ją turi, gali atsisiųsti Jūsų kūrinį, todėl niekam jos neperduokite. Atsisiųskite savo failą ir pasilikite kopiją. Po 12 mėnesių jis ištrinamas ir jo atkurti nebeįmanoma.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Teisė atsisakyti sutarties',
      blocks: [
        `Vartotojai paprastai turi teisę per 14 dienų atsisakyti sutarties. Skaitmeninio failo atveju ši teisė baigiasi anksčiau: prieš mokėjimą paprašome Jūsų sutikti, kad Jūsų failą pradėtume kurti iš karto, dar nepasibaigus sutarties atsisakymo terminui, ir pripažinti, kad pradėjus kurti netenkate teisės atsisakyti sutarties. Todėl ši teisė baigiasi, kai tik pradedame kurti Jūsų failą (vykdyti sutartį); pradedame tik po to, kai išsiunčiamas užsakymo patvirtinimo el. laiškas, paprastai per minutę nuo apmokėjimo, kol Jūsų užsakymo puslapis atidarytas. Tai galioja ir tada, kai failas dar kuriamas arba laukia mūsų kokybės patikros. Jei dar nepradėjome, teisė baigiasi pasibaigus 14 dienų sutarties atsisakymo terminui: Jūsų mokėjimo diena neskaičiuojama, o jei paskutinė termino diena yra šeštadienis, sekmadienis arba oficiali šventės diena, terminas baigiasi kitos darbo dienos pabaigoje. Kol turite teisę atsisakyti sutarties, galite tai padaryti el. paštu, paštu arba internetu, mygtuku „${WITHDRAWAL_ONLINE_LT.button}“; užsakymo patvirtinimo el. laiške esanti sutarties atsisakymo nuoroda atidaro šią funkciją Jūsų užsakymui, nepradėdama kurti Jūsų failo. Visa informacija, internetinė funkcija ir pavyzdinė sutarties atsisakymo forma pateiktos puslapyje [Teisė atsisakyti sutarties](doc:withdrawal).`,
      ],
    },
    {
      id: 'photos',
      title: 'Jūsų nuotraukos',
      blocks: [
        'Įkelkite tik savo arba kito žmogaus akies nuotraukas, jei tas žmogus su tuo sutiko (vaiko atveju sutikti turi vienas iš tėvų, globėjas ar rūpintojas). Įkeldami nuotrauką patvirtinate, kad galite ją naudoti šiam tikslui.',
        'Teisės į Jūsų nuotrauką lieka Jums. Ją naudojame tik Jūsų peržiūrai ir kūriniui sukurti, kaip aprašyta mūsų [privatumo politikoje](doc:privacy).',
        'Galime atsisakyti vykdyti užsakymą ir grąžinti visą sumokėtą sumą, jei nuotrauka akivaizdžiai pažeidžia šias taisykles.',
      ],
    },
    {
      id: 'licence',
      title: 'Ką galite daryti su savo kūriniu',
      blocks: [
        'Gaunate neišimtinę, neterminuotą licenciją naudoti savo kūrinį asmeniniais, nekomerciniais tikslais. Pavyzdžiui, galite jį atsispausdinti sau (namuose arba spaustuvėje), įrėminti, padovanoti, naudoti kaip ekrano foną savo įrenginiuose ir dalytis juo savo asmeninėse socialinių tinklų paskyrose.',
        'Be mūsų leidimo (pakanka el. laiško) negalite parduoti kūrinio ar iš jo pagamintų produktų, suteikti į jį teisių kitiems asmenims ar naudoti jo reklamai ar kitiems komerciniams tikslams.',
        'Stiliai, fonai, išdėstymai ir SnapEyes dizainas lieka mūsų, įskaitant bet kokias autorių teises į juos. Tai taikoma ir peržiūroms su vandens ženklu.',
      ],
    },
    {
      id: 'defects',
      title: 'Pretenzijos ir trūkumai',
      blocks: [
        `Visa apimtimi taikomos įstatymų Jums suteikiamos teisės, kai skaitmeninis turinys neatitinka sutarties sąlygų. Jei Jūsų failas turi trūkumų, pavyzdžiui, jo nepavyksta atsisiųsti ar atidaryti, jis sugadintas, mažesnis nei žadėta arba aiškiai skiriasi nuo patvirtintos peržiūros, parašykite mums adresu ${MAIL} ir nurodykite užsakymo numerį. Failą nemokamai sukursime iš naujo arba, jei tai trūkumo nepašalins, grąžinsime pinigus.`,
      ],
    },
    {
      id: 'liability',
      title: 'Atsakomybė',
      blocks: [
        'Be apribojimų atsakome už žalą, padarytą tyčia arba dėl didelio neatsargumo, už žalą asmens gyvybei ar sveikatai ir visais atvejais, kai tai numato imperatyviosios teisės normos. Kitais atvejais už žalą, padarytą dėl paprasto neatsargumo, atsakome tik tada, kai pažeidžiamos esminės sutartinės prievolės, ir tik už tokio pobūdžio sutarčiai būdingą ir protingai numatomą žalą. Nemokama peržiūra teikiama tokia, kokia yra, be jokių garantijų dėl jos prieinamumo.',
      ],
    },
    {
      id: 'disputes',
      title: 'Ginčai ir taikytina teisė',
      blocks: [
        'Jei kas nors ne taip, pirmiausia parašykite mums: dauguma problemų greitai išsprendžiamos el. paštu.',
        'Jei nepavyksta susitarti, vartotojai gali kreiptis į Valstybinę vartotojų teisių apsaugos tarnybą ([vvtat.lt](https://vvtat.lt)), kuri vartojimo ginčus sprendžia ne teismo tvarka, arba į savo šalies vartotojų teisių apsaugos institucijas ir teismus.',
        'Taikoma Lietuvos Respublikos teisė. Vartotojams, gyvenantiems kitoje ES šalyje, išlieka tos šalies imperatyviųjų vartotojų teisių apsaugos normų suteikiama apsauga.',
      ],
    },
    {
      id: 'changes',
      title: 'Šių sąlygų pakeitimai',
      blocks: ['Jūsų užsakymui taikomos sąlygos, galiojusios užsakymo pateikimo metu.'],
    },
  ],
};

/** "Kainos ir apmokėjimas" of the Hungarian edition (the hu market, prices in forints, src/shared/legal.ts legalEdition
 *  "hu"): the same section with the forint table; the rest of the terms is the base text above. */
export const ltHufPrices: LegalSection = {
  id: 'prices',
  title: 'Kainos ir apmokėjimas',
  blocks: [
    {
      dl: [
        ['Viena akis, Studio Black', huf(HU_PRICES.one_eye_studio_black, 'lt')],
        ['Viena akis su meniniu fonu', `${huf(HU_PRICES.one_eye_art, 'lt')} (${ART})`],
        ['Dvi akys (Couple Duo), bet kuris stilius', huf(HU_PRICES.two_eyes, 'lt')],
        ['Kiekviena papildoma akis', `+${huf(HU_PRICES.each_further_eye, 'lt')}, iki ${MAX_EYES} akių viename kūrinyje`],
      ],
    },
    `Visos kainos yra galutinės ir nurodytos Vengrijos forintais (Ft). ${companyLt} nėra PVM mokėtoja, todėl PVM netaikomas. Pristatymo išlaidų nėra. Jei svetainė Jums rodo kainas kita valiuta, mokėjimo puslapyje ir užsakymo patvirtinimo el. laiške nurodoma valiuta ir suma, kurią iš tikrųjų mokate.`,
    'Pirmiau pateikta lentelė yra mūsų standartinis kainoraštis. Kartkartėmis ribotą laiką kai kuriems atsitiktinai parinktiems lankytojams išbandome kitus kainoraščius. Visada mokate kainas, kurios Jums parodytos kūrinio puslapyje prieš apmokėjimą ir mokėjimo puslapyje, o Jūsų užsakymo patvirtinimo el. laiške nurodomas kainoraštis, kuris taikytas Jūsų užsakymui. Koks kainoraštis Jums rodomas, niekada nepriklauso nuo šalies, kurioje gyvenate, o tik nuo Jūsų pasirinktos rinkos (valiutos).',
    'Mokate iš anksto per mūsų mokėjimo paslaugų teikėją Stripe, mokėjimo puslapyje rodomais mokėjimo būdais.',
  ],
};
