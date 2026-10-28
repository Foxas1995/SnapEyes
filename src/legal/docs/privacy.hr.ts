// Politika privatnosti (članak 13. OUZP-a): the Croatian twin of `en` in src/legal/docs/privacy.ts, same section ids and
// blocks in the same order. Written from the same facts as the English file (see its header: what the code really does
// on 2026-09-29) and to be kept in step with it. The GDPR is "Opća uredba o zaštiti podataka" (OUZP) in Croatian, and
// its articles are cited the Croatian way ("članak 6. stavak 1. točka (f) OUZP-a"); "hash" is written "hash vrijednost",
// as Croatian technical texts do. "rights" keeps the lead authority of the English text (the controller is
// established in Lithuania: the State Data Protection Inspectorate, VDAI) and names the Croatian authority a reader in
// Croatia may also turn to (Art. 77 GDPR): Agencija za zaštitu osobnih podataka (AZOP), Selska cesta 136, 10000 Zagreb.
// Not reviewed by a lawyer. Keep every sentence true when the code or a service changes.
import type { LegalDoc } from '../types';
import { ORDER_EMAIL_SENDER, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';

const companyHr = company('hr');
const addressHr = address('hr');
const WITHDRAWAL_ONLINE_HR = WITHDRAWAL_ONLINE.hr;

// What the online withdrawal function keeps (the "withdrawal" section), as WITHDRAW_PRIVACY.en
const WITHDRAW_PRIVACY_HR = `Ako narudžbu raskinete našom mrežnom funkcijom (gumb „${WITHDRAWAL_ONLINE_HR.button}“, pogledajte [Pravo na jednostrani raskid ugovora](doc:withdrawal#online)), vašu izjavu o raskidu pohranjujemo uz vašu narudžbu: vaše ime, adresu e-pošte, broj narudžbe, tekst izjave te datum i vrijeme kada nam je stigla. Koristimo je kako bismo zaustavili rad na vašoj datoteci ako još nismo počeli, kako bismo vam e-poštom poslali potvrdu primitka s njezinim sadržajem, datumom i vremenom te kako bismo vam vratili novac. Svaku izjavu primamo i e-poštom: pojedinačno ili, za izjave koje se ne podudaraju ni s jednom našom narudžbom i one o narudžbama koje nikada nisu plaćene, u jednoj zbirnoj poruci dnevno. Ako vaš raskid proizvede učinak, naše svakodnevno automatsko čišćenje briše slike vaše narudžbe kada prođe 14 dana od raskida (ako se vaše plaćanje još obrađivalo, tek kada je završeno); zapis o narudžbi s vašom izjavom ostaje (pogledajte [Koliko dugo čuvamo vaše podatke](#retention)). Ako se podaci koje navedete ne podudaraju ni s jednom našom narudžbom (bez poveznice s vaše stranice narudžbe ili poveznice za raskid u e-poruci s potvrdom narudžbe adresa e-pošte mora biti ona koju ste naveli pri plaćanju), izjavu čuvamo zasebno, ručno je provjeravamo, svejedno vam e-poštom šaljemo potvrdu primitka (u granicama protiv zlouporabe navedenima u odjeljku [Jednostrani raskid putem interneta](doc:withdrawal#online)) i automatski je brišemo otprilike 13 mjeseci nakon završetka mjeseca u kojem nam je stigla.`;

// The admin log and the admin sign-in guard, as ADMIN_LOG.en
const ADMIN_LOG_HR = {
  log: 'Kada narudžbu obrađujemo na našoj administratorskoj ploči, primjerice kada nakon provjere kvalitete odobrimo isporuku datoteke, ponovno pošaljemo e-poruku, izvršimo povrat novca ili izbrišemo datoteke, ploča upisuje unos u naš administratorski zapisnik: što je učinjeno, kada, za koji broj narudžbe i s kojim ishodom. Administratorski zapisnik ne sadrži slike, adrese e-pošte ni poveznice. Pravna osnova: naš legitimni interes da narudžbe obrađujemo sigurno i sljedivo (članak 6. stavak 1. točka (f) OUZP-a). Zapisnik se automatski briše nakon 24 mjeseca; unosi o narudžbi čuvaju se i uz zapis te narudžbe, sve dok se taj zapis čuva (pogledajte [Koliko dugo čuvamo vaše podatke](#retention)).',
  signin: 'Naša administratorska ploča namijenjena je samo nama. Kako nitko ne bi mogao pogoditi njezin ključ, neuspjela prijava pohranjuje hash vrijednost IP adrese s koje je došla, izrađenu tajnim ključem, nikada samu adresu, a ona se automatski briše nakon 2 dana. Pravna osnova: naš legitimni interes za sigurnost naših sustava (članak 6. stavak 1. točka (f) OUZP-a).',
};

// The admin panel's usage statistics and its admin log, as OPS.en
const OPS_HR = {
  events:
    'Kako bismo vidjeli radi li usluga, koliko je brza i koliko košta, naš poslužitelj bilježi male tehničke događaje u našoj privatnoj pohrani kod Supabasea u EU-u. Primjerice: da je fotografija provjerena (s rezultatom, poput „oko nije pronađeno“, vrstom uređaja, poput iPhonea, Androida ili računala, podatkom je li fotografija snimljena kamerom ili odabrana iz galerije te jezikom stranice), da su uklonjeni odsjaji, da je izrađen pregled ili naručena datoteka i koliko je to trajalo, ili da zahtjev nije uspio (s kodom pogreške). Dok testiramo cijene, događaji navode i koji je cjenik (kratki kod) prikazan, pregledan, otvoren za plaćanje ili plaćen, a za plaćenu narudžbu i iznos. Naša administratorska ploča prikazuje nam ih, uglavnom kao dnevne zbrojeve.',
  counter:
    'Kako bismo vidjeli koliko ljudi stigne do svakog koraka internetske stranice, naš poslužitelj broji i korake do kojih stranica stigne: da je otvorena prva stranica, da je otvorena stranica za fotografiju, da je fotografija odabrana ili snimljena, da je prikazan pregled (sa sekundama koje su mu trebale od fotografije), da je kartica za kupnju pokazala da narudžbe još nisu otvorene, da je pritisnut gumb za kupnju i da je otvorena stranica narudžbe. Svako brojanje mali je zapis brojeva i kratkih kodova: korak, jezik stranice, tržište (valuta), vrsta uređaja (iPhone, Android ili računalo), vrsta preglednika (primjerice Chrome, Safari ili ugrađeni preglednik aplikacije Facebook ili Instagram) i zemlja (dva slova koja Vercel izvodi iz vaše IP adrese). Kako bi utvrdio uređaj i preglednik, naš poslužitelj na trenutak čita identifikator vašeg preglednika (user agent), a kako bi zaustavio klijenta koji šalje previše brojanja, kraće od minute drži u memoriji hash vrijednost vaše IP adrese, izrađenu ključem koji se gubi pri ponovnom pokretanju poslužitelja; ne pohranjuje ni jedno ni drugo. Ta brojanja ne koriste kolačić ni broj posjetitelja i ne sadrže IP adresu, identifikator preglednika, adresu stranice ni poveznicu s koje ste došli, pa se ne mogu povezati s vama. Na našoj administratorskoj ploči vidimo ih zbrojene po danima.',
  campaign:
    'Ako do nas dođete putem oglasa ili naše poveznice s kodom kampanje ili s druge internetske stranice, vaš preglednik čuva taj kod tijekom vašeg posjeta (pogledajte [Kolačići i lokalna pohrana](#storage)), a gore navedena brojanja, provjere fotografija i pregledi koje izradite, stranica za plaćanje i vaša narudžba prenose ga, kako bismo mogli vidjeti koji je oglas doveo do kojeg koraka, koliko je koštao po koraku i koju je narudžbu donio. Kod je isti za sve koji su slijedili taj oglas i nije izveden iz vaših podataka.',
  feedback:
    'Na zaslonu s rezultatom i na kartici koja traži drugu fotografiju mali okvir za povratne informacije nudi šest odgovora (primjerice „Sviđa mi se“ ili „Boje ne izgledaju točno“) i, ako želite, tekst do 300 znakova. Ništa se ne šalje dok ne pritisnete „Pošalji“. Okvir nema polje za vaše ime ni adresu e-pošte: molimo vas da ih ne upisujete, kao ni brojeve telefona ili poveznice. Kada pritisnete „Pošalji“, naš poslužitelj bilježi vaš odgovor kao još jedan mali događaj od kodova (odgovor, stil koji je bio na zaslonu ili razlog zbog kojeg je fotografija odbijena, broj očiju, je li uz njega bio tekst te isti podaci kao u gore opisanim brojanjima koraka: kod kampanje, jezik stranice, tržište, vrsta uređaja i preglednika te zemlja). Tekst se pohranjuje zasebno, s tim kodovima i ničim drugim, i samo ako prođe provjeru: tekst koji sadrži znak „@“, broj telefona, poveznicu ili nešto što izgleda kao neželjena pošta ne čuva se (vaš se odgovor svejedno broji). Tekstove čitamo na našoj administratorskoj ploči; ne možemo odgovoriti jer ne znamo tko ih je napisao. Svaki se tekst automatski briše nakon 90 dana, a možemo ga izbrisati i ranije. Budući da vas ništa u okviru ne identificira, vaš tekst kasnije možemo pronaći samo ako nam kažete što je u njemu pisalo. Okvir ništa ne zapisuje u vaš preglednik.',
  content:
    '**Ti događaji ne sadrže sliku, tekst koji ste upisali (tekst napisan u okviru za povratne informacije pohranjuje se odvojeno od njih, kako je gore opisano), ime, adresu e-pošte, IP adresu, identifikator preglednika (user agent) ni poveznicu.** Događaji iz besplatnog pregleda ne mogu se povezati s vama. Samo događaji o izradi datoteke plaćene narudžbe sadrže i njezin broj narudžbe, kako bismo mogli pronaći sporu ili neuspjelu izradu; putem naših zapisa o narudžbama taj je broj povezan s vašom narudžbom.',
  basis:
    'Pravna osnova: naš legitimni interes da uslugu pružamo pouzdano, pronalazimo pogreške, držimo njezine troškove pod kontrolom i saznamo što odbija posjetitelje (članak 6. stavak 1. točka (f) OUZP-a). Događaji i dnevni zbrojevi izrađeni iz njih automatski se brišu nakon 12 mjeseci, a tekstovi iz okvira za povratne informacije nakon 90 dana. U bilo kojem trenutku možete uložiti prigovor (pogledajte [Vaša prava](#rights)).',
  admin: ADMIN_LOG_HR.log,
  signin: ADMIN_LOG_HR.signin,
};

const repHr = SELLER.representative ? ` Društvo zastupa ${SELLER.representative}.` : '';
const senderHr = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: slanje e-poruka o vašoj narudžbi (poveznica na vašu stranicu narudžbe, potvrda narudžbe i, ako raskinete ugovor, potvrda primitka). Poslužitelji te usluge mogu biti izvan EU-a.`];
const hostingerHr = ORDER_EMAIL_SENDER === 'Hostinger'
  ? 'Hostinger: naša e-pošta, poštanski sandučić info@snapeyes.com, uključujući e-poruke o vašoj narudžbi.'
  : 'Hostinger: naš poštanski sandučić info@snapeyes.com.';

export const hr: LegalDoc = {
  title: 'Politika privatnosti',
  description:
    'Kako SnapEyes postupa s fotografijom vašeg oka, vašim pregledom i, ako naručite, podacima o vašoj narudžbi: što obrađujemo, zašto, kojim uslugama, koliko dugo i koja su vaša prava.',
  lead:
    'Ova politika objašnjava što se događa s vašim podacima kada koristite snapeyes.com: besplatni pregled i, ako naručite, vaše digitalno umjetničko djelo. Ukratko: vaša se fotografija koristi samo za izradu vašeg umjetničkog djela, nikada za identifikaciju bilo koga i nikada za treniranje umjetne inteligencije. Besplatne preglede ne pohranjujemo. Datoteke plaćenih narudžbi čuvaju se 12 mjeseci kako biste ih mogli ponovno preuzeti, a zatim se brišu.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'controller',
      title: 'Tko je odgovoran za vaše podatke',
      blocks: [
        `Voditelj obrade vaših podataka je ${companyHr} (matični broj ${SELLER.code}), ${addressHr}. SnapEyes je robna marka tog društva.${repHr}`,
        `Za sva pitanja o privatnosti i za ostvarivanje bilo kojeg od svojih prava pišite na ${MAIL}. Službenika za zaštitu podataka nismo imenovali.`,
      ],
    },
    {
      id: 'website',
      title: 'Kada posjećujete internetsku stranicu',
      blocks: [
        'Kada otvorite stranicu snapeyes.com, vaš preglednik šalje tehničke podatke našem pružatelju usluga smještaja (hostinga) Vercel, poput vaše IP adrese, datuma i vremena, zatražene stranice i vrste preglednika (user agent). Vercelu su ti podaci potrebni kako bi isporučio stranicu i zaštitio uslugu od napada. Kratko se čuvaju u zapisnicima poslužitelja, a zatim se brišu.',
        'Kako bismo vam mogli predložiti cijene u vašoj valuti, naš poslužitelj može pročitati i zemlju koju Vercel izvodi iz vaše IP adrese (primjerice „AU“). Koristi se za taj prijedlog i nikada ne mijenja cijene koje vidite. Ne pohranjuje se ni s čim što bi vas moglo identificirati: njezin jedini trag su dva slova zemlje u našim anonimnim brojanjima (pogledajte [Statistika usluge i naš administratorski zapisnik](#operations)).',
        'Pravna osnova: naš legitimni interes za sigurnu internetsku stranicu koja radi (članak 6. stavak 1. točka (f) OUZP-a).',
        'Naši se fontovi poslužuju s našeg vlastitog poslužitelja, pa nikakvi podaci ne odlaze usluzi Google Fonts ni drugoj usluzi fontova. Na ovoj internetskoj stranici ne koristimo alate za analitiku, oglašavanje ni praćenje drugih tvrtki i ništa vas ne prati sa stranice na stranicu ni između internetskih stranica. Naša vlastita anonimna statistika usluge opisana je u odjeljku [Statistika usluge i naš administratorski zapisnik](#operations).',
      ],
    },
    {
      id: 'preview',
      title: 'Vaš besplatni pregled',
      blocks: [
        'Kako bismo izradili vaš pregled, iz svojeg preglednika šaljete jednu ili više fotografija oka našim poslužiteljskim funkcijama. Ondje se fotografija obrađuje u memoriji: pronalazimo šarenicu, izrezujemo je, provjeravamo je li dovoljno oštra i svijetla, uklanjamo odsjaje, obnavljamo fina vlakna pomoću Googleova Gemini API-ja i prikazujemo šarenicu u stilovima koje vidite. Rezultat se vraća u vaš preglednik. Svaki je prijenos šifriran (HTTPS).',
        '**Vašu fotografiju, izrezak šarenice ni pregled ne pohranjujemo na našim poslužiteljima.** Odbacuju se kada zahtjev završi. Pregled ostaje u vašem pregledniku dok ne zatvorite stranicu (dok ste na stranici za plaćanje, u pohrani sesije kartice vašeg preglednika: pogledajte [Kolačići i lokalna pohrana](#storage)), osim ako ga sami ne spremite. Izrezak šarenice i pregled koji ste odobrili čuvamo samo kada započnete narudžbu: pogledajte [Kada naručujete](#orders).',
        'Google obrađuje sliku kako bi izvršio obnovu. Koristimo Googleovu plaćenu API uslugu, prema čijim uvjetima Google ne koristi slike za poboljšanje svojih proizvoda ni za treniranje svojih modela. Google može ograničeno vrijeme čuvati zahtjeve, isključivo radi otkrivanja zlouporabe i za otkrivanja podataka koja zahtijeva zakon.',
        'Pravna osnova: tražite od nas da izradimo vaš pregled, a za to je potrebna fotografija (članak 6. stavak 1. točka (b) OUZP-a, radnje poduzete na vaš zahtjev).',
        'Naš softver automatski odlučuje može li se fotografija upotrijebiti (primjerice kada je previše mutna ili pretamna). Ta odluka nema pravnih ni sličnih značajnih učinaka na vas: jednostavno možete snimiti drugu fotografiju.',
      ],
    },
    {
      id: 'iris',
      title: 'Vaša šarenica nikada se ne koristi za identifikaciju',
      blocks: [
        'Šarenica se u načelu može koristiti za prepoznavanje osobe. Mi to ne činimo. Nikada ne izrađujemo, ne uspoređujemo ni ne pohranjujemo predložak šarenice ni bilo koji drugi biometrijski identifikator, nikada ne koristimo vaše slike za identifikaciju ili provjeru bilo koga, nikada ih ne prodajemo i nikada ih ne koristimo za treniranje umjetne inteligencije, ni naše ni tuđe.',
        'Koristite samo vlastito oko ili oko osobe koja je na to pristala. Za dijete mora pristati roditelj ili skrbnik.',
        'Ako dodate oči drugih osoba (primjerice za par), njihove slike obrađujemo samo za izradu umjetničkog djela na koje su pristale. Pravna osnova: vaš i naš legitimni interes za izradu tog umjetničkog djela (članak 6. stavak 1. točka (f) OUZP-a). Pokažite im ovu politiku.',
      ],
    },
    {
      id: 'measurements',
      title: 'Tehnička mjerenja (bez slika)',
      blocks: [
        'Uz svaku fotografiju naš poslužitelj upisuje jedan redak u svoje zapisnike kako bismo mogli poboljšati upute za snimanje i kvalitetu usluge. Redak sadrži mjerenja fotografije (primjerice veličinu šarenice u pikselima, oštrinu, svjetlinu, obojenost svjetla i je li se fotografija mogla upotrijebiti), tehničke podatke o vašem uređaju (vrstu i verziju preglednika, veličinu zaslona, je li fotografija snimljena kamerom ili odabrana iz galerije) i, ako odgovorite na naša neobvezna pitanja o snimci, vaše odgovore. Ne sadrži sliku, ime ni podatke za kontakt.',
        'Te retke zapisnika naš pružatelj usluga smještaja čuva kratko vrijeme, a zatim se brišu. Pravna osnova: naš legitimni interes za poboljšanje usluge (članak 6. stavak 1. točka (f) OUZP-a). U bilo kojem trenutku možete uložiti prigovor (pogledajte [Vaša prava](#rights)).',
      ],
    },
    {
      id: 'operations',
      title: 'Statistika usluge i naš administratorski zapisnik',
      blocks: [OPS_HR.events, OPS_HR.counter, OPS_HR.campaign, OPS_HR.feedback, OPS_HR.content, OPS_HR.basis, OPS_HR.admin, OPS_HR.signin],
    },
    {
      id: 'orders',
      title: 'Kada naručujete',
      blocks: [
        'Kada započnete narudžbu, u našu privatnu pohranu učitavaju se dvije slike svakog oka, kako bi vaša datoteka bila izrađena upravo od onoga što ste vidjeli: kvadrat oko vaše šarenice izrezan iz vaše fotografije (s uklonjenim odsjajima) i pregled koji ste odobrili. Uz njih čuvamo kratak zapis mjerenja izrađenih iz tog pregleda (boje oko vaše šarenice, kategoriju boje, oblik zjenice, dvije vrijednosti kvalitete i kod koji označava pregled). Taj zapis ne sadrži sliku i briše se zajedno sa slikama. **Vaša cijela fotografija s mobitela ne pohranjuje se, čak ni za narudžbu.** Narudžba koja nije plaćena u roku od 24 sata više se ne može platiti. Automatsko čišćenje koje se pokreće jednom dnevno tada briše njezine slike i zapise, obično u roku od dva dana od narudžbe, a najkasnije u roku od 30 dana.',
        'Kako bi učitavanja ostala u granicama, naš poslužitelj za svako učitavanje upisuje i malu oznaku (njegovu veličinu, dan i broj narudžbe, bez slike). Te se oznake automatski brišu nakon nekoliko dana.',
        'Kako bismo vam prodali i isporučili vaše umjetničko djelo, obrađujemo: narudžbu (broj narudžbe, datum, oči, stil, raspored, redoslijed očiju, imena, datum ili natpis koje dodate, jezik, cijenu), vašu adresu e-pošte (upisujete je na stranici za plaćanje), status plaćanja koji primamo od Stripea, vaš pristanak da odmah započnemo (pogledajte [Pravo na jednostrani raskid ugovora](doc:withdrawal)) i datoteke vaše narudžbe: dvije gore navedene slike svakog oka, prikaz svakog oka u 4096 px i gotovo umjetničko djelo, s tehničkim zapisima o kvaliteti.',
        'Te datoteke čuvamo u privatnoj pohrani kod Supabasea, smještenoj u EU-u. Do njih dolazite putem svoje stranice narudžbe, čiju vam poveznicu šaljemo e-poštom; ona sadrži privatni ključ, pa svatko tko ima poveznicu može preuzeti vaše umjetničko djelo. Svaka poveznica za preuzimanje koju stranica izradi istječe nakon 7 dana.',
        'Datoteke vaše narudžbe možemo pregledati kako bismo provjerili njihovu kvalitetu, primjerice kada naša automatska provjera prijavi razliku u odnosu na pregled koji ste odobrili.',
        'Pravna osnova: ugovor s vama (članak 6. stavak 1. točka (b) OUZP-a); za računovodstvene zapise naše pravne obveze (članak 6. stavak 1. točka (c) OUZP-a).',
        'Kada prijeđete na stranicu za plaćanje, uz vaše plaćanje Stripeu prosljeđujemo podatke o narudžbi: broj narudžbe, cijenu (a kada se primjenjivao test cijena, njegov naziv, kod vašeg cjenika i cijene tog cjenika), broj očiju, stil (i njegovu varijantu), raspored, redoslijed očiju, jezik, imena, datum ili natpis koje ste dodali, kratki kod koji označava plan umjetničkog djela i verziju našeg softvera koji ga izrađuje, verziju i vrijeme vašeg pristanka te, ako ste došli putem oglasa, njegov kod kampanje. Stripe ih čuva uz zapis o plaćanju, a mi ih odande ponovno čitamo kako bismo izradili upravo ono umjetničko djelo koje ste platili.',
        'Plaćanje: vaše plaćanje obrađuje Stripe. Nikada ne vidimo vaš cijeli broj kartice. Stripe podatke o plaćanju obrađuje i prema vlastitoj politici privatnosti, radi sprječavanja prijevara i ispunjavanja vlastitih zakonskih obveza.',
        'Vaša adresa e-pošte potrebna nam je kako bismo vam poslali poveznicu na vašu stranicu narudžbe i potvrdu narudžbe. Bez nje biste mogli izgubiti pristup svojoj datoteci.',
      ],
    },
    {
      id: 'email',
      title: 'Kada nam pišete',
      blocks: [
        'Ako nam pošaljete e-poruku, vašu adresu i poruku koristimo kako bismo vam odgovorili i, ako se odnosi na narudžbu, obradili tu narudžbu. Pravna osnova: za narudžbe članak 6. stavak 1. točka (b) OUZP-a, inače naš legitimni interes da vam odgovorimo (članak 6. stavak 1. točka (f) OUZP-a). Ako nam pošaljete fotografije, primjerice svojeg oka kako bismo vam savjetovali kako snimiti bolju fotografiju, koristimo ih samo za vaš zahtjev. Vaše e-poruke, zajedno s fotografijama, čuvamo dok su nam potrebne za vaš zahtjev i daljnje postupanje.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Kada ugovor raskidate putem interneta',
      blocks: [
        WITHDRAW_PRIVACY_HR,
        'Pravna osnova: naša pravna obveza da prihvatimo vaš raskid i da vam ga potvrdimo (članak 6. stavak 1. točka (c) OUZP-a) i ugovor s vama (članak 6. stavak 1. točka (b) OUZP-a). Izjavu čuvamo uz zapis o vašoj narudžbi, kao dokaz, sve dok se taj zapis čuva (pogledajte [Koliko dugo čuvamo vaše podatke](#retention)).',
      ],
    },
    {
      id: 'services',
      title: 'Usluge kojima se koristimo',
      blocks: [
        'Za rad usluge SnapEyes koristimo se ovim uslugama:',
        {
          ul: [
            'Vercel: smještaj (hosting) internetske stranice i poslužiteljskih funkcija koje izrađuju vaš pregled i vašu datoteku. Vercelovi podatkovni centri mogu biti izvan EU-a, primjerice u SAD-u.',
            'Google (Gemini API): obnova šarenice pomoću umjetne inteligencije i provjere vaše fotografije. Googleovi poslužitelji mogu biti izvan EU-a.',
            'Supabase: privatna pohrana datoteka narudžbi, u regiji EU-a.',
            'Stripe: obrada plaćanja, s podacima o narudžbi navedenima u odjeljku [Kada naručujete](#orders).',
            hostingerHr,
            ...senderHr,
          ],
        },
        `Ti pružatelji usluga obrađuju vaše podatke u naše ime i prema našim uputama (Stripe djelomično kao samostalni voditelj obrade, pogledajte [Kada naručujete](#orders)). Kada se podaci prenose izvan EU-a ili EGP-a, to se čini uz zaštitne mjere koje nude pružatelji usluga, poput standardnih ugovornih klauzula Europske komisije ili Okvira za privatnost podataka između EU-a i SAD-a. Kopiju tih zaštitnih mjera možete zatražiti na ${MAIL}.`,
        'Vaše podatke ne prodajemo i ne prosljeđujemo ih nikome drugome, osim ako nas na to obvezuje zakon.',
      ],
    },
    {
      id: 'retention',
      title: 'Koliko dugo čuvamo vaše podatke',
      blocks: [
        {
          dl: [
            ['Besplatni pregledi', 'Ne pohranjujemo ih. Odbacuju se kada zahtjev završi.'],
            ['Neplaćene narudžbe', 'Narudžba koja nije plaćena u roku od 24 sata više se ne može platiti. Naše svakodnevno automatsko čišćenje briše njezine slike i zapise, obično u roku od dva dana od narudžbe, a najkasnije u roku od 30 dana.'],
            ['Oznake učitavanja i izjava', 'Mali brojači bez slika, imena ili adresa e-pošte (brojač potvrda primitka sadrži samo kratku hash vrijednost adrese e-pošte), automatski se brišu nakon nekoliko dana; mjesečni brojači potvrda primitka otprilike 40 dana nakon završetka svojeg mjeseca.'],
            ['Plaćene narudžbe', 'Datoteke vaše narudžbe čuvaju se 12 mjeseci od plaćanja kako biste ih mogli ponovno preuzeti sa svoje stranice narudžbe, a zatim ih briše naše svakodnevno automatsko čišćenje. Na vaš zahtjev brišemo ih ranije; nakon toga vaša stranica narudžbe više ne može isporučiti datoteku.'],
            ['Raskinute narudžbe', 'Ako raskid proizvede učinak, naše svakodnevno čišćenje briše slike narudžbe kada prođe 14 dana od raskida (ako se plaćanje još obrađivalo, kada je završeno).'],
            ['Izjave o raskidu koje se ne podudaraju ni s jednom narudžbom', 'Čuvaju se zasebno, ručno se provjeravaju i automatski se brišu otprilike 13 mjeseci nakon završetka mjeseca u kojem su nam stigle.'],
            ['Zapisi o narudžbama', 'Kada se datoteke izbrišu (nakon 12 mjeseci, nakon raskida ili na zahtjev), čuvamo zapis o plaćenoj narudžbi: broj narudžbe, datum, cijenu, plaćanje i eventualni povrat novca, vašu adresu e-pošte, kod kampanje oglasa putem kojeg ste došli (ako postoji), podatke o naručenom umjetničkom djelu (koji mogu uključivati imena, datum ili natpis koje ste dodali te kratak sažetak mjerenja izrađenih iz vaših pregleda: kategoriju boje, prosječnu boju prstena i oblik zjenice svakog oka), vaš pristanak da odmah započnemo, vašu izjavu o raskidu (ako ste raskinuli ugovor) i unose našeg administratorskog zapisnika o vašoj narudžbi. Bez slika. Čuvamo ga kao dokaz ugovora i za računovodstvo, onoliko dugo koliko to zahtijevaju litavski računovodstveni i porezni propisi.'],
            ['Zapisnici poslužitelja i mjerenja', 'Kratko ih čuva naš pružatelj usluga smještaja, a zatim se brišu.'],
            ['Statistika usluge', 'Tehnički događaji i njihovi dnevni zbrojevi (pogledajte [Statistika usluge i naš administratorski zapisnik](#operations)): automatski se brišu nakon 12 mjeseci.'],
            ['Tekstovi povratnih informacija', 'Neobvezni tekstovi iz okvira za povratne informacije (pogledajte [Statistika usluge i naš administratorski zapisnik](#operations)): automatski se brišu nakon 90 dana, ili ranije ako ih mi izbrišemo. Sami odgovori samo su kodovi i dio tehničkih događaja te se čuvaju kako je gore opisano.'],
            ['Administratorski zapisnik', 'Što smo učinili s narudžbom na našoj administratorskoj ploči: automatski se briše nakon 24 mjeseca; unosi o narudžbi ostaju uz njezin zapis o narudžbi.'],
            ['Neuspjele prijave na našu administratorsku ploču', 'Hash vrijednost IP adrese, izrađena tajnim ključem, automatski se briše nakon 2 dana.'],
            ['E-poruke', 'Dok su nam potrebne za vaš zahtjev i daljnje postupanje.'],
          ],
        },
      ],
    },
    {
      id: 'rights',
      title: 'Vaša prava',
      blocks: [
        'Ova prava imate u bilo kojem trenutku:',
        {
          ul: [
            'Pristup: saznati koje podatke o vama imamo i dobiti njihovu kopiju (članak 15. OUZP-a).',
            'Ispravak: zatražiti ispravak netočnih podataka (članak 16. OUZP-a).',
            'Brisanje: zatražiti brisanje svojih podataka, primjerice datoteka svoje narudžbe prije isteka 12 mjeseci (članak 17. OUZP-a).',
            'Ograničenje obrade: zatražiti ograničenje obrade dok se pitanje razjašnjava (članak 18. OUZP-a).',
            'Prenosivost podataka: dobiti podatke koje ste nam dali u uobičajenom, strojno čitljivom formatu (članak 20. OUZP-a).',
            'Prigovor: u bilo kojem trenutku, na temelju razloga koji se odnose na vašu posebnu situaciju, uložiti prigovor na obradu koja se temelji na našim legitimnim interesima (članak 21. OUZP-a).',
          ],
        },
        `Kako biste ostvarili bilo koje od tih prava, pišite na ${MAIL}. Odgovaramo u roku od mjesec dana.`,
        'Imate i pravo podnijeti pritužbu nadzornom tijelu. Naše nadzorno tijelo je litavski Državni inspektorat za zaštitu podataka (Valstybinė duomenų apsaugos inspekcija, VDAI) u Vilniusu, [vdai.lrv.lt](https://vdai.lrv.lt). Možete se obratiti i nadzornom tijelu države EU-a u kojoj živite ili radite; u Hrvatskoj je to Agencija za zaštitu osobnih podataka (AZOP), Selska cesta 136, 10000 Zagreb, [www.azop.hr](https://www.azop.hr).',
      ],
    },
    {
      id: 'storage',
      title: 'Kolačići i lokalna pohrana',
      blocks: [
        'Ova internetska stranica ne postavlja kolačiće. Ne koristi alate za analitiku, oglašavanje ni praćenje drugih tvrtki.',
        'Kada prekidačem jezika odaberete jezik, vaš preglednik pamti taj odabir u svojoj lokalnoj pohrani pod ključem „snapeyes.lang“ (vrijednost je kod jezika, primjerice „hr“). Nikada nam se ne šalje i u bilo kojem ga trenutku možete izbrisati u postavkama preglednika. Nužan je za funkciju koju ste zatražili, pa ne zahtijeva privolu (članak 5. stavak 3. Direktive 2002/58/EZ, Direktive o e-privatnosti).',
        'Ako do nas dođete putem poveznice s cijenama u drugoj valuti (primjerice u australskim dolarima) ili odaberete valutu našim prekidačem valute ili u našoj ponudi cijena u vašoj valuti, vaš preglednik i taj odabir pamti u svojoj lokalnoj pohrani pod ključem „snapeyes.market“ (primjerice „au“, ili „eu“ nakon što odbijete tu ponudu), kako bi vam stranica i dalje prikazivala iste cijene. Naše ga stranice prenose u svojim poveznicama (m=au) i šalju uz narudžbu, kako biste platili cijene koje ste vidjeli. U bilo kojem ga trenutku možete izbrisati u postavkama preglednika; nužan je za funkciju koju ste zatražili, pa ni on ne zahtijeva privolu (članak 5. stavak 3. Direktive 2002/58/EZ, Direktive o e-privatnosti).',
        'Kada testiramo cijene (samo povremeno i na ograničeno vrijeme), vaš preglednik može u svojoj lokalnoj pohrani pod ključem „snapeyes.vid“ čuvati nasumičan anonimni broj posjetitelja. Izrađuje se samo dok se za tržište (valutu) koje gledate provodi test cijena i ponovno se briše čim test više ne traje; najkasnije nakon 90 dana zamjenjuje se novim. Sastoji se od 32 nasumična znaka i dana kada je izrađen: nije izveden iz vaših podataka, ne sadrži ime, adresu e-pošte ni podatke o uređaju i nikada se ne povezuje s narudžbom. Vaš ga preglednik šalje našem poslužitelju u zaglavlju zahtjeva (nikada u adresi stranice) kada traži cijene; naša ga aplikacija koristi samo kako bi svaki put na isti način utvrdila koji od cjenika testa vidite i ne pohranjuje ga: ne vodimo popis brojeva posjetitelja. Poslužitelj odgovara potpisanom oznakom vašeg cjenika, koju vaš preglednik vraća kada prijeđete na stranicu za plaćanje, kako biste platili upravo one cijene koje su vam prikazane (cijena ili cjenik koje pošalje preglednik nikada se ne koriste). Za statistiku naš poslužitelj bilježi anonimne zbrojeve po cjeniku: da je cjenik prikazan, da je izrađen pregled, da je otvorena stranica za plaćanje i da je narudžba plaćena (pogledajte [Statistika usluge i naš administratorski zapisnik](#operations)); ti zbrojevi ne sadrže broj posjetitelja. Vaš preglednik u lokalnoj pohrani pamti i koje je od tih zbrojeva već poslao („snapeyes.expseen“) te vaš posljednji cjenik („snapeyes.pricing“), kako bi se iste cijene odmah prikazale. Koji cjenik vidite nikada ne ovisi o tome gdje živite, nego samo o tržištu (valuti) koje odaberete, a cijena koju plaćate uvijek je ona koja vam je prikazana prije plaćanja; vaša potvrda narudžbe navodi cjenik koji se primijenio. Te unose koristimo samo za ovaj test cijena, nikada za oglašavanje i nikada kako bismo vas pratili na drugim internetskim stranicama. Ako ne želite sudjelovati, [otvorite ovu poveznicu](/?pricetest=off&lang=hr): vaš preglednik tada čuva samo oznaku „snapeyes.notest“, briše broj posjetitelja i ostale ovdje navedene unose te prikazuje i naplaćuje standardne cijene; putem [ove poveznice](/?pricetest=on&lang=hr) ponovno sudjelujete. Ako vaš preglednik šalje signal „Global Privacy Control“, i to se smatra tim odabirom. Sve te unose također možete u bilo kojem trenutku izbrisati u postavkama preglednika (tada dobivate novo nasumično izvlačenje). Pravna osnova: naš legitimni interes za određivanje poštenih cijena (članak 6. stavak 1. točka (f) OUZP-a). U bilo kojem trenutku možete uložiti prigovor (pogledajte [Vaša prava](#rights)).',
        'Ako do nas dođete putem oglasa ili naše poveznice s kodom kampanje ili s druge internetske stranice, vaš preglednik čuva kratak kod u pohrani sesije kartice vašeg preglednika pod ključem „snapeyes.c“: parametre adrese koji imenuju oglas, onako kako ih je upisao njegov autor (utm_source, utm_medium, utm_campaign, utm_term i utm_content: platforma, vrsta, kampanja, grupa i oglas; primjerice „utm_source=fb&utm_medium=placeno&utm_campaign=proljece“), ili, kada ih nema, samo vrstu internetske stranice s koje ste došli (primjerice „ref=facebook“: Facebook, Instagram, TikTok, Google, izravan dolazak ili druga stranica). Pohrana sesije pripada samo toj jednoj kartici i briše se kada je zatvorite. Kod je isti za sve koji su slijedili isti oglas: nije izveden iz vaših podataka i ne sadrži ime, adresu e-pošte, podatke o uređaju ni broj klika („fbclid“ ili sličan broj u adresi nikada se ne čita). Naše ga stranice šalju uz svoja anonimna brojanja stranica i zahtjeve (provjera fotografije, pregled, stranica za plaćanje); zapis o narudžbi ga čuva, a Stripeova stranica za plaćanje prima ga u metapodacima plaćanja, kako bismo mogli vidjeti koji je oglas doveo do kojeg koraka i do narudžbe (pogledajte [Statistika usluge i naš administratorski zapisnik](#operations) i [Kada naručujete](#orders)). Koristimo ga samo za to, nikada za oglašavanje, profiliranje ni kako bismo vas pratili na drugim internetskim stranicama. Nije vam potreban za korištenje stranice: ako ga izbrišete ili vaš preglednik blokira pohranu sesije, sve radi jednako, samo nedostaje to brojanje. Pravna osnova: naš legitimni interes da znamo djeluje li naše vlastito oglašavanje (članak 6. stavak 1. točka (f) OUZP-a). U bilo kojem trenutku možete uložiti prigovor (pogledajte [Vaša prava](#rights)).',
        'Kada naručujete, stranica u pohrani sesije kartice vašeg preglednika čuva i dva unosa. Pohrana sesije pripada samo toj jednoj kartici i briše se kada je zatvorite:',
        {
          ul: [
            '„snapeyes.order“: broj narudžbe koju sastavljate i njezin privatni ključ, kako bi stranica mogla nastaviti vašu narudžbu, primjerice kada se vratite sa stranice za plaćanje. Uklanja se kada se u toj kartici otvori stranica vaše plaćene narudžbe, a zamjenjuje se kada započnete novu narudžbu.',
            '„snapeyes.checkout“: samo dok ste na stranici za plaćanje, vaše umjetničko djelo onako kako ste ga ostavili (izresci šarenica s vaših fotografija, pregledi, nekoliko brojeva izmjerenih iz njih, stil i njegova varijanta, raspored, redoslijed očiju te imena i datum), kako bi se pri povratku sa stranice za plaćanje ponovno prikazalo. Uklanja se čim se vratite ili kada se u toj kartici otvori stranica vaše plaćene narudžbe.',
          ],
        },
        'Stranica ih koristi samo za vašu narudžbu i za nju su nužni, pa ni oni ne zahtijevaju privolu (članak 5. stavak 3. Direktive 2002/58/EZ, Direktive o e-privatnosti).',
        'Kada plaćate, Stripeova stranica za plaćanje može koristiti vlastite kolačiće potrebne za sigurno plaćanje i sprječavanje prijevara; ondje vrijede Stripeova pravila o privatnosti i kolačićima.',
      ],
    },
    {
      id: 'required',
      title: 'Morate li nam dati podatke?',
      blocks: ['Ne. No bez fotografije ne možemo izraditi pregled, a bez adrese e-pošte i plaćanja ne možemo isporučiti narudžbu.'],
    },
    {
      id: 'changes',
      title: 'Izmjene ove politike',
      blocks: ['Ovu politiku ažuriramo kada se promijeni naša usluga ili zakon. Datum na vrhu pokazuje važeću verziju.'],
    },
  ],
};
