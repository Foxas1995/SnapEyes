// Privaatsuspoliitika (GDPR Art. 13): the Estonian twin of `en` in src/legal/docs/privacy.ts, same section ids and
// blocks in the same order. Written from the same facts as the English file (see its header: what the code really does
// on 2026-09-29) and to be kept in step with it. The GDPR is "isikuandmete kaitse üldmäärus" (IKÜM) in Estonian, named in
// full once ("website") and then by its abbreviation, and its articles are cited the Estonian way ("IKÜMi artikli 6
// lõike 1 punkt f"); a hash is "räsi", the admin panel "halduspaneel", local storage "kohalik salvestusruum", session
// storage "seansisalvestusruum". "rights" keeps the lead authority of the English text (the controller is established
// in Lithuania: the State Data Protection Inspectorate, VDAI) and names the Estonian authority a reader in Estonia may
// also turn to (Art. 77 GDPR): Andmekaitse Inspektsioon, www.aki.ee. That is one link more than the English text has.
// Formal "teie", written in lower case. Not reviewed by a lawyer. Keep every sentence true when the code or a service
// changes.
import type { LegalDoc } from '../types';
import { ORDER_EMAIL_SENDER, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';

const companyEt = company('et');
const addressEt = address('et');
const WITHDRAWAL_ONLINE_ET = WITHDRAWAL_ONLINE.et;

// What the online withdrawal function keeps (the "withdrawal" section), as WITHDRAW_PRIVACY.en
const WITHDRAW_PRIVACY_ET = `Kui taganete tellimusest meie veebipõhise funktsiooniga (nupp „${WITHDRAWAL_ONLINE_ET.button}“, vt [Taganemisõigus](doc:withdrawal#online)), salvestame teie taganemisavalduse teie tellimuse juurde: teie nimi, e-posti aadress, tellimuse number, avalduse sõnastus ning kuupäev ja kellaaeg, mil see meieni jõudis. Kasutame seda selleks, et peatada töö teie failiga, kui me ei ole veel alustanud, saata teile e-kirjaga kättesaamise kinnitus avalduse sisu, kuupäeva ja kellaajaga ning tagastada teile raha. Saame iga avalduse ka e-kirjaga: ükshaaval või avalduste puhul, mis ei vasta ühelegi meie tellimusele või puudutavad tellimusi, mille eest ei ole kunagi makstud, ühe kokkuvõttena päevas. Kui teie taganemine jõustub, kustutab meie igapäevane puhastus teie tellimuse pildid automaatselt, kui taganemisest on möödunud 14 päeva (kui teie makse oli veel töötlemisel, siis alles pärast makse laekumist); tellimuse kirje koos teie avaldusega jääb alles (vt [Kui kaua me teie andmeid säilitame](#retention)). Kui teie esitatud andmed ei vasta ühelegi meie tellimusele (ilma teie tellimuse lehe lingita või tellimuse kinnituskirjas oleva taganemislingita peab e-posti aadress olema see, millega maksite), säilitame avalduse eraldi, kontrollime seda käsitsi, saadame teile siiski e-kirjaga kättesaamise kinnituse (kuritarvitamise vastaste piirangute raames, mida on kirjeldatud jaotises [Taganemine veebis](doc:withdrawal#online)) ja kustutame selle automaatselt umbes 13 kuud pärast selle kuu lõppu, mil see meieni jõudis.`;

// The admin log and the admin sign-in guard, as ADMIN_LOG.en
const ADMIN_LOG_ET = {
  log: 'Kui käsitleme tellimust oma halduspaneelis, näiteks väljastame faili pärast kvaliteedikontrolli, saadame e-kirja uuesti, teeme tagasimakse või kustutame faile, kirjutab paneel kande meie halduslogisse: mida tehti, millal, millise tellimuse numbri kohta ja kuidas see lõppes. Halduslogi ei sisalda pilte, e-posti aadresse ega linke. Õiguslik alus: meie õigustatud huvi käsitleda tellimusi turvaliselt ja jälgitavalt (IKÜMi artikli 6 lõike 1 punkt f). See kustutatakse automaatselt 24 kuu pärast; tellimust puudutavad kanded säilitatakse ka selle tellimuse kirje juures seni, kuni kirjet säilitatakse (vt [Kui kaua me teie andmeid säilitame](#retention)).',
  signin: 'Meie halduspaneel on ainult meie jaoks. Et keegi ei saaks selle võtit ära arvata, salvestab ebaõnnestunud sisselogimine salajase võtmega tehtud räsi IP-aadressist, kust see tuli, mitte kunagi aadressi ennast, ja see kustutatakse automaatselt 2 päeva pärast. Õiguslik alus: meie õigustatud huvi hoida oma süsteemid turvalisena (IKÜMi artikli 6 lõike 1 punkt f).',
};

// The admin panel's usage statistics and its admin log, as OPS.en
const OPS_ET = {
  events:
    'Et näha, kas teenus töötab, kui kiire see on ja mis see maksab, salvestab meie server väikesi tehnilisi sündmusi meie privaatsesse salvestusruumi Supabase’is ELis. Näiteks: et fotot kontrolliti (koos tulemusega, näiteks „silma ei leitud“, seadme liigiga, näiteks iPhone, Android või arvuti, sellega, kas foto tuli kaamerast või galeriist, ja lehe keelega), et peegeldused eemaldati, et valmistati eelvaade või tellitud fail ja kui kaua see aega võttis, või et päring ebaõnnestus (koos veakoodiga). Kui testime hindu, näitavad sündmused ka seda, millist hinnakirja (lühike kood) näidati, millega tehti eelvaade, millega avati makseleht või millega maksti, koos makstud tellimuse summaga. Meie halduspaneel näitab neid meile, enamasti päevade kaupa loendatuna.',
  counter:
    'Et näha, kui paljud inimesed jõuavad veebilehe iga sammuni, loendab meie server ka samme, milleni leht jõuab: et avati esimene leht, et avati fotoleht, et foto valiti või tehti, et näidati eelvaadet (koos sekunditega, mis selleks fotost alates kulus), et fotoleht näitas, et tellimine ei ole veel avatud, et vajutati ostunuppu ja et avati tellimuse leht. Iga loendus on väike kirje numbritest ja lühikestest koodidest: samm, lehe keel, turg (valuuta), seadme liik (iPhone, Android või arvuti), brauseri liik (näiteks Chrome, Safari või Facebooki või Instagrami rakenduse sisseehitatud brauser) ja riik (kaks tähte, mille Vercel tuletab teie IP-aadressist). Seadme ja brauseri kindlakstegemiseks loeb meie server hetkeks teie brauseri tunnust (user agent) ning selleks, et pidurdada klienti, kes saadab liiga palju loendusi, hoiab ta alla minuti oma mälus teie IP-aadressi räsi, mis on tehtud võtmega, mis läheb serveri taaskäivitamisel kaotsi; kumbagi ta ei salvesta. Need loendused ei kasuta küpsist ega külastajanumbrit ning ei sisalda IP-aadressi, brauseri tunnust, lehe aadressi ega linki, kust te tulite, seega ei saa neid teieni tagasi viia. Meie halduspaneelis näeme neid päevade kaupa kokku liidetuna.',
  campaign:
    'Kui jõuate meieni reklaami või meie lingi kaudu, millel on kampaaniakood, või mõnelt teiselt veebilehelt, hoiab teie brauser seda koodi teie külastuse ajal (vt [Küpsised ja kohalik salvestusruum](#storage)) ning ülaltoodud loendused, teie tehtud fotokontrollid ja eelvaated, makseleht ja teie tellimus kannavad seda, et saaksime näha, milline reklaam millise sammuni viis, mis see sammu kohta maksis ja millise tellimuse see tõi. Kood on sama kõigile, kes selle reklaami kaudu tulid, ja seda ei tuletata teie andmetest.',
  feedback:
    'Tulemuse kuval ja kaardil, mis palub teist fotot, pakub väike tagasisidekast kuut vastust (näiteks „Mulle väga meeldib“ või „Värvid tunduvad valed“) ja soovi korral kuni 300 tähemärgi pikkust teksti. Midagi ei saadeta enne, kui vajutate nuppu „Saada“. Kastis ei ole välja teie nime ega e-posti aadressi jaoks: palun ärge neid kirjutage, samuti mitte telefoninumbreid ega linke. Kui vajutate nuppu „Saada“, salvestab meie server teie vastuse veel ühe väikese koodidest koosneva sündmusena (vastus, ekraanil olnud stiil või foto tagasilükkamise põhjus, silmade arv, kas vastusega tuli kaasa tekst, ja samad andmed nagu ülaltoodud sammuloendustes: kampaaniakood, lehe keel, turg, seadme ja brauseri liik ning riik). Tekst salvestatakse eraldi, koos nende koodidega ja mitte millegi muuga, ning ainult siis, kui see läbib kontrolli: teksti, mis sisaldab ät-märki, telefoninumbrit, linki või midagi rämpsposti moodi, ei säilitata (teie vastus loetakse siiski arvesse). Loeme tekste oma halduspaneelis; vastata me ei saa, sest me ei tea, kes need kirjutas. Iga tekst kustutatakse automaatselt 90 päeva pärast ja me võime selle varem kustutada. Kuna miski kastis teid ei tuvasta, saame teie teksti hiljem leida ainult siis, kui ütlete meile, mida see sisaldas. Kast ei kirjuta teie brauserisse midagi.',
  content:
    '**Need sündmused ei sisalda pilti, teie sisestatud teksti (tagasisidekasti kirjutatud tekst salvestatakse neist eraldi, nagu eespool kirjeldatud), nime, e-posti aadressi, IP-aadressi, brauseri tunnust (user agent) ega linki.** Tasuta eelvaate sündmusi ei saa teieni tagasi viia. Ainult makstud tellimuse faili valmistamist puudutavad sündmused sisaldavad ka selle tellimuse numbrit, et saaksime leida aeglase või ebaõnnestunud valmistamise; meie tellimuste kirjete kaudu on see number seotud teie tellimusega.',
  basis:
    'Õiguslik alus: meie õigustatud huvi osutada teenust usaldusväärselt, leida vigu, hoida selle kulud kontrolli all ja saada teada, mis külastajaid eemale peletab (IKÜMi artikli 6 lõike 1 punkt f). Sündmused ja neist tehtud päevased loendused kustutatakse automaatselt 12 kuu pärast; tagasisidekasti tekstid 90 päeva pärast. Võite igal ajal esitada vastuväite (vt [Teie õigused](#rights)).',
  admin: ADMIN_LOG_ET.log,
  signin: ADMIN_LOG_ET.signin,
  previewcap: 'Et tasuta eelvaade jääks kõigile tasuta, saab ühest internetiühendusest teha päevas piiratud arvu eelvaateid. Iga eelvaate kohta salvestab meie server salajase võtmega tehtud räsi IP-aadressist, kust see tuli, ja päevast, mitte kunagi aadressi ennast: aadressi ei saa sellest tagasi lugeda ja järgmisel päeval annab sama aadress teise räsi. Need kanded kustutatakse automaatselt 2 päeva pärast. Õiguslik alus: meie õigustatud huvi hoida tasuta eelvaade kättesaadavana ja selle kulud kontrolli all (IKÜMi artikli 6 lõike 1 punkt f).',
};

const repEt = SELLER.representative ? ` Seda esindab ${SELLER.representative}.` : '';
const senderEt = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: teie tellimust puudutavate e-kirjade saatmine (teie tellimuse lehe link, tellimuse kinnitus ja taganemise korral kättesaamise kinnitus). Selle serverid võivad asuda väljaspool ELi.`];
const hostingerEt = ORDER_EMAIL_SENDER === 'Hostinger'
  ? 'Hostinger: meie e-post, postkast info@snapeyes.com, sealhulgas teie tellimust puudutavad e-kirjad.'
  : 'Hostinger: meie postkast info@snapeyes.com.';

export const et: LegalDoc = {
  title: 'Privaatsuspoliitika',
  description:
    'Kuidas SnapEyes käsitleb teie silmafotot, teie eelvaadet ja tellimise korral teie tellimuse andmeid: mida me töötleme, miks, milliste teenustega, kui kaua ja millised on teie õigused.',
  lead:
    'See poliitika selgitab, mis juhtub teie andmetega, kui kasutate veebilehte snapeyes.com: tasuta eelvaadet ja tellimise korral teie digitaalset kunstiteost. Lühidalt: teie fotot kasutatakse teie kunstiteose valmistamiseks ja selle kvaliteedi kontrollimiseks, mitte kunagi kellegi tuvastamiseks ega tehisintellekti treenimiseks. Tasuta eelvaateid säilitame 30 päeva, et nende kvaliteeti kontrollida ja parandada, ning seejärel kustutame need. Makstud tellimuste faile säilitatakse 12 kuud, et saaksite need uuesti alla laadida, ja seejärel need kustutatakse.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'controller',
      title: 'Kes vastutab teie andmete eest',
      blocks: [
        `Teie andmete vastutav töötleja on ${companyEt} (registrikood ${SELLER.code}), ${addressEt}. SnapEyes on selle kaubamärk.${repEt}`,
        `Kõigi privaatsusküsimustega ja oma õiguste kasutamiseks kirjutage aadressile ${MAIL}. Me ei ole andmekaitsespetsialisti määranud.`,
      ],
    },
    {
      id: 'website',
      title: 'Kui külastate veebilehte',
      blocks: [
        'Kui avate veebilehe snapeyes.com mõne lehe, saadab teie brauser meie majutusteenuse pakkujale Vercel tehnilisi andmeid, näiteks teie IP-aadressi, kuupäeva ja kellaaja, soovitud lehe ja teie brauseri tüübi (user agent). Vercel vajab neid andmeid lehe edastamiseks ja teenuse kaitsmiseks rünnakute eest. Neid hoitakse lühikest aega serveri logides ja seejärel kustutatakse.',
        'Et saaksime pakkuda hindu teie oma valuutas, võib meie server lugeda ka riiki, mille Vercel teie IP-aadressist tuletab (näiteks „AU“). Seda kasutatakse selle ettepaneku jaoks ja see ei muuda kunagi hindu, mida te näete. Seda ei salvestata koos millegagi, mis võiks teid tuvastada: selle ainus jälg on riigi kaks tähte meie anonüümsetes loendustes (vt [Teenuse statistika ja meie halduslogi](#operations)).',
        'Õiguslik alus: meie õigustatud huvi turvalise ja toimiva veebilehe vastu (isikuandmete kaitse üldmääruse (IKÜM) artikli 6 lõike 1 punkt f).',
        'Meie fonte edastatakse meie oma serverist, seega ei liigu andmeid teenusesse Google Fonts ega ühessegi teise fonditeenusesse. Meie enda anonüümset teenusestatistikat on kirjeldatud jaotises [Teenuse statistika ja meie halduslogi](#operations). Teiste ettevõtete vahenditest kasutame sellel veebilehel üht, Meta pikslit meie reklaamide jaoks: vt [Meta piksel ja meie reklaamid](#meta).',
      ],
    },
    {
      id: 'preview',
      title: 'Teie tasuta eelvaade',
      blocks: [
        'Eelvaate valmistamiseks saadate oma brauserist ühe või mitu silmafotot meie serverifunktsioonidele. Seal töödeldakse fotot mälus: leiame iirise, lõikame selle välja, kontrollime, kas see on piisavalt terav ja hele, eemaldame peegeldused, taastame peened kiud Google’i Gemini API abil ja kujundame iirise stiilides, mida te näete. Tulemus saadetakse tagasi teie brauserisse. Iga edastus on krüpteeritud (HTTPS).',
        '**Teie tasuta eelvaate koopiat säilitame 30 päeva.** Meie server salvestab meie privaatsesse Supabase’i salvestusruumi ELis: fotod, mille saadate (vähendatud, pikemalt küljelt kuni 1280 pikslit), iirise ümbert välja lõigatud ruudu, selle taastamise, teile näidatud eelvaated ja anonüümsed koodid: mida meie kontrollid leidsid (näiteks kas fotot sai kasutada ja kui mitte, siis miks), stiili, aja ning sama anonüümse konteksti nagu meie teenusestatistikas (kampaaniakood, seadme ja brauseri liik, keel ja riik). Säilitame neid, et kontrollida ja parandada oma eelvaadete kvaliteeti ning välja selgitada, miks fotod ei õnnestu. Neid näeme ainult meie, oma halduspaneelis. Neid ei seota teie nime, e-posti aadressi ega IP-aadressiga ning nagu kõike muud, ei kasutata neid kunagi kellegi tuvastamiseks, ei müüda ega kasutata tehisintellekti treenimiseks. 30 päeva pärast kustutab meie igapäevane puhastus need automaatselt. Eelvaade jääb ka teie brauserisse, kuni sulgete lehe (makselehel viibimise ajal teie brauseri vahekaardi seansisalvestusruumi: vt [Küpsised ja kohalik salvestusruum](#storage)), kui te seda ise ei salvesta. Kui alustate tellimust, säilitame iirise väljalõike ja eelvaate, mille heaks kiitsite, ka koos tellimusega: vt [Kui tellite](#orders).',
        'Google töötleb pilti taastamise tegemiseks. Kasutame Google’i tasulist API-teenust, mille tingimuste kohaselt ei kasuta Google pilte oma toodete täiustamiseks ega mudelite treenimiseks. Google võib päringuid piiratud aja säilitada üksnes kuritarvituste avastamiseks ja seadusega nõutud avaldamiste jaoks.',
        'Õiguslik alus: te palute meil oma eelvaate valmistada ja selleks on vaja fotot (IKÜMi artikli 6 lõike 1 punkt b, teie taotlusel võetavad meetmed).',
        `Selle koopia õiguslik alus: meie õigustatud huvi kontrollida ja parandada oma eelvaadete kvaliteeti ning välja selgitada, miks fotod ei õnnestu (IKÜMi artikli 6 lõike 1 punkt f). Võite igal ajal esitada vastuväite või paluda koopia kustutada: kirjutage aadressile ${MAIL} ja märkige oma külastuse ligikaudne kuupäev ja kellaaeg, et saaksime selle leida.`,
        'Meie tarkvara otsustab automaatselt, kas fotot saab kasutada (näiteks kui see on liiga udune või liiga tume). Sellel otsusel ei ole teile õiguslikku ega muud samaväärselt olulist mõju: võite lihtsalt teha uue foto.',
      ],
    },
    {
      id: 'iris',
      title: 'Teie iirist ei kasutata kunagi kellegi tuvastamiseks',
      blocks: [
        'Iirist saab põhimõtteliselt kasutada inimese äratundmiseks. Meie seda ei tee. Me ei loo, võrdle ega salvesta kunagi iirisemalli ega muud biomeetrilist tunnust, me ei kasuta teie pilte kunagi kellegi tuvastamiseks ega isikusamasuse kontrollimiseks, me ei müü neid kunagi ega kasuta neid kunagi tehisintellekti treenimiseks, ei enda ega kellegi teise oma.',
        'Palun kasutage ainult oma silma või sellise inimese silma, kes on sellega nõustunud. Lapse puhul peab nõustuma vanem või eestkostja.',
        'Kui lisate teiste inimeste silmi (näiteks paari jaoks), töötleme nende pilte ainult selle kunstiteose valmistamiseks, millega nad nõustusid. Õiguslik alus: teie ja meie õigustatud huvi selle kunstiteose valmistamise vastu (IKÜMi artikli 6 lõike 1 punkt f). Palun näidake neile seda poliitikat.',
      ],
    },
    {
      id: 'measurements',
      title: 'Tehnilised mõõtmised (ilma piltideta)',
      blocks: [
        'Iga foto kohta kirjutab meie server oma logidesse ühe rea, et saaksime parandada pildistamisjuhendit ja teenuse kvaliteeti. See sisaldab foto mõõtmistulemusi (näiteks iirise suurus pikslites, teravus, heledus, valguse värvitoon ja see, kas fotot sai kasutada), tehnilisi andmeid teie seadme kohta (brauseri tüüp ja versioon, ekraani suurus, kas foto tuli kaamerast või galeriist) ning kui vastate meie vabatahtlikele küsimustele võtte kohta, siis teie vastuseid. See ei sisalda pilti, nime ega kontaktandmeid.',
        'Neid logiridu hoiab meie majutusteenuse pakkuja lühikest aega ja seejärel need kustutatakse. Õiguslik alus: meie õigustatud huvi teenust parandada (IKÜMi artikli 6 lõike 1 punkt f). Võite igal ajal esitada vastuväite (vt [Teie õigused](#rights)).',
      ],
    },
    {
      id: 'operations',
      title: 'Teenuse statistika ja meie halduslogi',
      blocks: [OPS_ET.events, OPS_ET.counter, OPS_ET.campaign, OPS_ET.feedback, OPS_ET.content, OPS_ET.basis, OPS_ET.admin, OPS_ET.signin, OPS_ET.previewcap],
    },
    {
      id: 'meta',
      title: 'Meta piksel ja meie reklaamid',
      blocks: [
        'Reklaamime Facebookis ja Instagramis. Et teada saada, millised meie reklaamid toovad külastajaid ja tellimusi, ning et Meta saaks neid näidata inimestele, keda need tõenäoliselt huvitavad, kasutavad meie lehed Meta pikslit, mis on ettevõtte Meta Platforms Ireland Limited (Merrion Road, Dublin 4, D04 X2K5, Iirimaa; „Meta“) tööriist. See töötab meie lehtedel iga külastaja puhul; me ei küsi teilt selle kohta eelnevalt.',
        'Piksel teatab Metale, kui leht avatakse, kui fotoleht avatakse, kui teile näidatakse tasuta eelvaadet, kui liigute edasi makselehele ja kui tehakse makse, koos makse summa ja valuutaga ning teabega, kas maksti kunstiteose, kinkekaardi või trükitud pildi eest. Iga sellise teatega saadab teie brauser Metale, nagu iga päringuga, teie IP-aadressi ja brauseri tunnuse (user agent), lehe ja selle lehe aadressi, kust tulite, ning allpool kirjeldatud Meta küpsised. Meie tellimuse lehelt ja kinkekaardi lehelt saadetakse ainult lehe tee („/order“, „/gift“), mitte kunagi selle täielikku aadressi, mis sisaldab teie tellimuse võtit või teie makse numbrit. Kui kasutate Facebooki või Instagrami, võib Meta need teated teie kontoga siduda.',
        '**Me ei saada Metale kunagi teie fotot, iirist, silmade värvi, valitud stiili, teie lisatud nimesid ega kuupäeva, teie kunstiteost ega ühtki muud pilti.** Piksli automaatsed funktsioonid, mis loeksid lehe nuppe ja vormiväljasid, on välja lülitatud.',
        'Meta skript, mille teie brauser laadib aadressilt connect.facebook.net alles pärast meie lehe laadimist, salvestab snapeyes.com-i kaks küpsist: „_fbp“, juhuslik number, mille järgi Meta tunneb teie brauseri hilisematel külastustel ära ja mida hoitakse 90 päeva teie viimasest külastusest, ning ainult siis, kui tulite lingi kaudu, millel on Meta klikinumber („fbclid“, näiteks reklaamist), „_fbc“, mis sisaldab seda numbrit, samuti 90 päeva. Kui tulite sellise lingi kaudu ja teie brauseris ei ole küpsist „_fbc“, hoiab meie leht klikinumbrit teie brauseri vahekaardi seansisalvestusruumis võtme „snapeyes.fbc“ all, kuni vahekaardi sulgete. Teated lähevad aadressile www.facebook.com. Meie tellimuse leht ja kinkekaardi leht ei laadi Meta skripti: nad saadavad oma teated üksikute päringutena aadressile www.facebook.com.',
        'Kui maksate kunstiteose, kinkekaardi või trükitud pildi eest, teatab meie server maksest ka otse Metale (Meta Conversions API kaudu), et see loetaks ka siis, kui teie brauseri teade kohale ei jõua. See teade sisaldab: et makse tehti, millal, selle summat ja valuutat, kas maksti kunstiteose, kinkekaardi või trükitud pildi eest, lehe teed („/order“ või „/gift“), selle e-posti aadressi räsi, millega maksite (SHA-256: aadressi ei saa sellest tagasi lugeda, kuid Meta saab seda võrrelda oma kasutajate aadresside räsidega), teie riiki (teie makseandmetest või valitud hindadest) ning küpsiste „_fbp“ ja „_fbc“ väärtusi, IP-aadressi ja brauseri tunnust, mis teie brauseril makselehe avamisel olid. Ühe makse mõlemal teatel on sama number, et Meta loeks selle üks kord. Et meie serveril oleksid need makse ajal olemas, liiguvad need neli väärtust koos makselehega Stripe’i, makse metaandmetes, ja jäävad Stripe’i maksekirje juurde (vt [Kui tellite](#orders)); mujal me neid ei salvesta.',
        'Kasutame neid teateid, et mõõta, millised meie reklaamid toimivad, ja näidata neid inimestele, keda need tõenäoliselt huvitavad. Õiguslik alus: meie õigustatud huvi mõõta ja suunata oma reklaami (IKÜMi artikli 6 lõike 1 punkt f). Nende andmete kogumise eest meie veebilehel ja nende edastamise eest Metale vastutame meie ja Meta ühiselt (IKÜMi artikkel 26) Meta ärivahendite tingimuste alusel ning oma õigusi võite kasutada kummagi meie suhtes. Seda, mida Meta andmetega edasi teeb, otsustab Meta iseseisva vastutava töötlejana oma privaatsuspoliitika järgi; Meta võib neid töödelda USA-s ELi ja USA andmekaitseraamistiku alusel.',
        'Võite igal ajal esitada vastuväite: kirjutage meile (vt [Teie õigused](#rights)). Meta küpsiseid ja seansisalvestusruumi võite kustutada või blokeerida ka oma brauseri seadetes või kasutada brauserit või laiendust, mis selliseid vahendeid blokeerib; meie veebileht töötab ka ilma nendeta samamoodi. Oma Facebooki või Instagrami kontol (kontokeskus, reklaamieelistused) saate valida, kas Meta tohib kasutada teistelt veebilehtedelt saadud teavet, et teile reklaame näidata.',
      ],
    },
    {
      id: 'orders',
      title: 'Kui tellite',
      blocks: [
        'Kui alustate tellimust, laaditakse meie privaatsesse salvestusruumi üles kaks pilti igast silmast, et teie fail valmistataks täpselt sellest, mida nägite: teie fotost välja lõigatud ruut iirise ümber (peegeldused eemaldatud) ja eelvaade, mille heaks kiitsite. Koos nendega säilitame lühikese kirje sellest eelvaatest tehtud mõõtmistest (värvid teie iirise ümber, värviklass, pupilli kuju, kaks kvaliteedinäitajat ja kood, mis eelvaadet tuvastab). See ei sisalda pilti ja kustutatakse koos piltidega. **Teie tellimus ei sisalda teie täielikku telefonifotot;** tasuta eelvaate jaoks saadetud fotode koopiat säilitatakse sellest eraldi 30 päeva (vt [Teie tasuta eelvaade](#preview)). Tellimuse eest, mille eest ei maksta 24 tunni jooksul, ei saa enam maksta. Kord päevas käivituv automaatne puhastus kustutab seejärel selle pildid ja kirjed, tavaliselt kahe päeva jooksul alates tellimusest ja hiljemalt 30 päeva jooksul.',
        'Et hoida üleslaadimised piirides, kirjutab meie server iga üleslaadimise kohta ka väikese märke (selle suurus, päev ja tellimuse number, ilma pildita). Need märked kustutatakse automaatselt mõne päeva pärast.',
        'Teie kunstiteose müümiseks ja üleandmiseks töötleme: tellimust (tellimuse number, kuupäev, silmad, stiil, paigutus, silmade järjestus, teie lisatud nimed, kuupäev või tekst, keel, hind), teie e-posti aadressi (sisestate selle makselehel), makse olekut, mille saame Stripe’ilt, teie nõusolekut kohe alustada (vt [Taganemisõigus](doc:withdrawal)) ja teie tellimuse faile: eespool nimetatud kaks pilti igast silmast, iga silma 4096 px renderdus ja valmis kunstiteos koos tehniliste kvaliteedikirjetega.',
        'Säilitame neid faile privaatses salvestusruumis Supabase’is, mis asub ELis. Nendeni jõuate oma tellimuse lehe kaudu, mille lingi saadame teile e-kirjaga; see sisaldab privaatset võtit, seega saab igaüks, kellel on link, teie kunstiteose alla laadida. Iga allalaadimislink, mille leht loob, aegub 7 päeva pärast.',
        'Võime teie tellimuse faile vaadata, et kontrollida nende kvaliteeti, näiteks kui meie automaatne kontroll teatab erinevusest võrreldes eelvaatega, mille heaks kiitsite.',
        'Õiguslik alus: teiega sõlmitud leping (IKÜMi artikli 6 lõike 1 punkt b); raamatupidamisdokumentide puhul meie juriidilised kohustused (IKÜMi artikli 6 lõike 1 punkt c).',
        'Kui jätkate makselehele, edastame Stripe’ile koos teie maksega tellimuse andmed: tellimuse number, hind (ja kui kehtis hinnatest, siis selle nimi, teie hinnakirja kood ja selle hinnakirja hinnad), silmade arv, stiil (ja selle variant), paigutus, silmade järjestus, keel, teie lisatud nimed, kuupäev või tekst, lühike kood, mis tuvastab kunstiteose plaani ja selle valmistava tarkvara versiooni, teie nõusoleku versioon ja aeg ning kui tulite reklaami kaudu, siis selle kampaaniakood. Stripe säilitab neid koos maksekirjega ja me loeme need sealt tagasi, et valmistada täpselt see kunstiteos, mille eest maksite. Seni kuni teatame maksetest Metale, kannab makse ka Meta küpsiste „_fbp“ ja „_fbc“ väärtusi, kui teie brauseris need on, ning IP-aadressi ja brauseri tunnust, mis teie brauseril sel hetkel olid (vt [Meta piksel ja meie reklaamid](#meta)).',
        'Maksmine: teie makset töötleb Stripe. Me ei näe kunagi teie täielikku kaardinumbrit. Stripe töötleb makseandmeid ka oma privaatsuspoliitika alusel, pettuste ennetamiseks ja oma juriidiliste kohustuste täitmiseks.',
        'Vajame teie e-posti aadressi, et saata teile teie tellimuse lehe link ja tellimuse kinnitus. Ilma selleta võite kaotada juurdepääsu oma failile.',
      ],
    },
    {
      id: 'email',
      title: 'Kui kirjutate meile',
      blocks: [
        'Kui saadate meile e-kirja, kasutame teie aadressi ja sõnumit teile vastamiseks ning kui see puudutab tellimust, siis selle tellimuse käsitlemiseks. Õiguslik alus: tellimuste puhul IKÜMi artikli 6 lõike 1 punkt b, muul juhul meie õigustatud huvi teile vastata (IKÜMi artikli 6 lõike 1 punkt f). Kui saadate meile fotosid, näiteks oma silmast, et saaksime teile parema võtte tegemiseks nõu anda, kasutame neid ainult teie päringu jaoks. Säilitame teie e-kirju koos fotodega seni, kuni vajame neid teie päringu ja selle järeltegevuste jaoks.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Kui taganete tellimusest veebis',
      blocks: [
        WITHDRAW_PRIVACY_ET,
        'Õiguslik alus: meie juriidiline kohustus teie taganemine vastu võtta ja seda teile kinnitada (IKÜMi artikli 6 lõike 1 punkt c) ning teiega sõlmitud leping (IKÜMi artikli 6 lõike 1 punkt b). Säilitame avaldust tõendina teie tellimuse kirje juures seni, kuni seda kirjet säilitatakse (vt [Kui kaua me teie andmeid säilitame](#retention)).',
      ],
    },
    {
      id: 'services',
      title: 'Teenused, mida kasutame',
      blocks: [
        'SnapEyesi käitamiseks kasutame neid teenuseid:',
        {
          ul: [
            'Vercel: veebilehe ning nende serverifunktsioonide majutus, mis valmistavad teie eelvaate ja teie faili. Verceli andmekeskused võivad asuda väljaspool ELi, näiteks USAs.',
            'Google (Gemini API): iirise taastamine tehisintellekti abil ja teie foto kontrollid. Google’i serverid võivad asuda väljaspool ELi.',
            'Supabase: tellimuste failide ja tasuta eelvaadete 30-päevaste koopiate privaatne salvestusruum ELi piirkonnas.',
            'Stripe: maksete töötlemine koos tellimuse andmetega, mida on nimetatud jaotises [Kui tellite](#orders).',
            hostingerEt,
            ...senderEt,
            'Meta (Meta Platforms Ireland Limited): Meta piksel ja teated maksetest, vt [Meta piksel ja meie reklaamid](#meta). Meta võib andmeid töödelda USA-s.',
          ],
        },
        `Need teenusepakkujad töötlevad teie andmeid meie nimel ja meie juhiste alusel (Stripe osaliselt iseseisva vastutava töötlejana, vt [Kui tellite](#orders); Meta nii, nagu on kirjeldatud jaotises [Meta piksel ja meie reklaamid](#meta)). Kui andmeid edastatakse väljapoole ELi või EMPd, toimub see teenusepakkujate pakutavate kaitsemeetmete alusel, näiteks Euroopa Komisjoni lepingu tüüptingimuste või ELi ja USA andmekaitseraamistiku alusel. Nende kaitsemeetmete koopiat võite meilt küsida aadressil ${MAIL}.`,
        'Me ei müü teie andmeid ega edasta neid kellelegi teisele, välja arvatud juhul, kui seadus meid selleks kohustab.',
      ],
    },
    {
      id: 'retention',
      title: 'Kui kaua me teie andmeid säilitame',
      blocks: [
        {
          dl: [
            ['Tasuta eelvaated', 'Saadetud fotode, iirise väljalõike, taastamise, eelvaadete ja nende anonüümsete koodide koopia: kustutatakse automaatselt 30 päeva pärast või taotluse korral varem.'],
            ['Maksmata tellimused', 'Tellimuse eest, mille eest ei maksta 24 tunni jooksul, ei saa enam maksta. Meie igapäevane automaatne puhastus kustutab selle pildid ja kirjed, tavaliselt kahe päeva jooksul alates tellimusest ja hiljemalt 30 päeva jooksul.'],
            ['Üleslaadimiste ja avalduste märked', 'Väikesed loendurid ilma piltide, nimede ja e-posti aadressideta (kättesaamise kinnituste loendur sisaldab ainult e-posti aadressi lühikest räsi), kustutatakse automaatselt mõne päeva pärast; kinnituste igakuised loendurid umbes 40 päeva pärast oma kuu lõppu.'],
            ['Makstud tellimused', 'Teie tellimuse faile säilitatakse 12 kuud alates maksest, et saaksite need oma tellimuse lehelt uuesti alla laadida, ja seejärel kustutab need meie igapäevane automaatne puhastus. Taotluse korral kustutame need varem; pärast seda ei saa teie tellimuse leht faili enam väljastada.'],
            ['Tellimused, millest on taganetud', 'Kui taganemine jõustub, kustutab meie igapäevane puhastus tellimuse pildid, kui taganemisest on möödunud 14 päeva (kui makse oli veel töötlemisel, siis pärast makse laekumist).'],
            ['Taganemisavaldused, mis ei vasta ühelegi tellimusele', 'Säilitatakse eraldi, kontrollitakse käsitsi ja kustutatakse automaatselt umbes 13 kuud pärast selle kuu lõppu, mil need meieni jõudsid.'],
            ['Tellimuste kirjed', 'Kui failid kustutatakse (12 kuu pärast, pärast taganemist või taotluse korral), säilitame makstud tellimuse kirje: tellimuse number, kuupäev, hind, makse ja võimalik tagasimakse, teie e-posti aadress, selle reklaami kampaaniakood, mille kaudu tulite (kui see on olemas), tellitud kunstiteose andmed (mis võivad sisaldada teie lisatud nimesid, kuupäeva või teksti ning lühikokkuvõtet teie eelvaadetest tehtud mõõtmistest: iga silma värviklass, rõnga keskmine värv ja pupilli kuju), teie nõusolek kohe alustada, taganemise korral teie taganemisavaldus ja meie halduslogi kanded teie tellimuse kohta. Ilma piltideta. Säilitame seda lepingu tõendina ja raamatupidamise jaoks nii kaua, kui Leedu raamatupidamis- ja maksuõigus nõuab.'],
            ['Serveri logid ja mõõtmised', 'Neid hoiab meie majutusteenuse pakkuja lühikest aega, seejärel need kustutatakse.'],
            ['Teenuse statistika', 'Tehnilised sündmused ja nende päevased loendused (vt [Teenuse statistika ja meie halduslogi](#operations)): kustutatakse automaatselt 12 kuu pärast.'],
            ['Tagasiside tekstid', 'Tagasisidekasti vabatahtlikud tekstid (vt [Teenuse statistika ja meie halduslogi](#operations)): kustutatakse automaatselt 90 päeva pärast või meie poolt varem. Vastused ise on ainult koodid ja osa tehnilistest sündmustest, mida säilitatakse eespool kirjeldatud viisil.'],
            ['Halduslogi', 'Mida me tellimusega oma halduspaneelis tegime: kustutatakse automaatselt 24 kuu pärast; tellimust puudutavad kanded jäävad selle tellimuse kirje juurde.'],
            ['Ebaõnnestunud sisselogimised meie halduspaneeli', 'Salajase võtmega tehtud IP-aadressi räsi, kustutatakse automaatselt 2 päeva pärast.'],
            ['Tasuta eelvaated ühenduse kohta', 'Salajase võtmega tehtud IP-aadressi ja päeva räsi, kustutatakse automaatselt 2 päeva pärast.'],
            ['Meta küpsised ja teated', '„_fbp“ ja „_fbc“ teie brauseris: 90 päeva teie viimasest külastusest, kui te neid varem ei kustuta; „snapeyes.fbc“: kuni vahekaardi sulgemiseni. Maksega edastatud küpsiste väärtused, IP-aadress ja brauseri tunnus: Stripe’i maksekirje juures. Kui kaua Meta oma teateid säilitab, otsustab Meta (vt tema privaatsuspoliitikat).'],
            ['E-kirjad', 'Nii kaua, kui vajame neid teie päringu ja selle järeltegevuste jaoks.'],
          ],
        },
      ],
    },
    {
      id: 'rights',
      title: 'Teie õigused',
      blocks: [
        'Teil on igal ajal järgmised õigused:',
        {
          ul: [
            'Juurdepääs: saada teada, milliseid andmeid me teie kohta hoiame, ja saada neist koopia (IKÜMi artikkel 15).',
            'Parandamine: lasta ebaõiged andmed parandada (IKÜMi artikkel 16).',
            'Kustutamine: lasta oma andmed kustutada, näiteks oma tellimuse failid enne 12 kuu möödumist (IKÜMi artikkel 17).',
            'Töötlemise piiramine: lasta töötlemist piirata seni, kuni mõnda küsimust selgitatakse (IKÜMi artikkel 18).',
            'Andmete ülekandmine: saada meile antud andmed üldkasutatavas masinloetavas vormingus (IKÜMi artikkel 20).',
            'Vastuväide: esitada igal ajal oma konkreetsest olukorrast lähtudes vastuväide töötlemisele, mis põhineb meie õigustatud huvidel (IKÜMi artikkel 21).',
          ],
        },
        `Nende õiguste kasutamiseks kirjutage aadressile ${MAIL}. Vastame ühe kuu jooksul.`,
        'Teil on ka õigus esitada kaebus järelevalveasutusele. Meie järelevalveasutus on Leedu riiklik andmekaitseinspektsioon (Valstybinė duomenų apsaugos inspekcija, VDAI) Vilniuses, [vdai.lrv.lt](https://vdai.lrv.lt). Võite pöörduda ka selle ELi riigi järelevalveasutuse poole, kus te elate või töötate; Eestis on see Andmekaitse Inspektsioon, [www.aki.ee](https://www.aki.ee).',
      ],
    },
    {
      id: 'storage',
      title: 'Küpsised ja kohalik salvestusruum',
      blocks: [
        'Meie oma lehed ei salvesta teie seadmesse küpsiseid. Meta piksel salvestab kaks Meta küpsist, „_fbp“ ja „_fbc“, ning meie leht võib hoida võtit „snapeyes.fbc“: vt [Meta piksel ja meie reklaamid](#meta). Peale selle ei kasuta veebileht teiste ettevõtete analüütika-, reklaami- ega jälgimisvahendeid.',
        'Kui valite keelelülitiga keele, jätab teie brauser selle valiku meelde oma kohalikus salvestusruumis võtme „snapeyes.lang“ all (väärtus on keelekood, näiteks „et“). Seda ei saadeta meile kunagi ja saate selle igal ajal oma brauseri seadetes kustutada. See on teie soovitud funktsiooni jaoks hädavajalik, seega ei vaja see nõusolekut (direktiivi 2002/58/EÜ ehk e-privaatsuse direktiivi artikli 5 lõige 3).',
        'Kui tulete meie juurde lingi kaudu, millel on hinnad teises valuutas (näiteks Austraalia dollarites), või valite valuuta meie valuutalülitiga või meie pakkumises näha hindu teie oma valuutas, jätab teie brauser ka selle valiku meelde oma kohalikus salvestusruumis võtme „snapeyes.market“ all (näiteks „au“ või „eu“, kui olete sellest pakkumisest keeldunud), et veebileht näitaks teile jätkuvalt samu hindu. Meie lehed kannavad seda oma linkides (m=au) ja saadavad selle koos tellimusega, et teilt võetaks need hinnad, mida nägite. Saate selle igal ajal oma brauseri seadetes kustutada; see on teie soovitud funktsiooni jaoks hädavajalik, seega ei vaja ka see nõusolekut (e-privaatsuse direktiivi artikli 5 lõige 3).',
        'Kui testime hindu (ainult aeg-ajalt ja piiratud aja jooksul), võib teie brauser hoida oma kohalikus salvestusruumis võtme „snapeyes.vid“ all juhuslikku anonüümset külastajanumbrit. See luuakse ainult siis, kui teie vaadatava turu (valuuta) jaoks on hinnatest käimas, ja kustutatakse uuesti niipea, kui ühtki testi ei käi; hiljemalt asendatakse see 90 päeva pärast. See koosneb 32 juhuslikust märgist ja loomise päevast: seda ei tuletata teie andmetest, see ei sisalda nime, e-posti aadressi ega seadme andmeid ning seda ei seota kunagi tellimusega. Teie brauser saadab selle meie serverile päringu päises (mitte kunagi lehe aadressis), kui küsib hindu; meie rakendus kasutab seda ainult selleks, et iga kord samal viisil välja arvutada, millist testi hinnakirja te näete, ega salvesta seda: me ei pea külastajanumbrite nimekirja. Server vastab teie hinnakirja allkirjastatud märkega, mille teie brauser saadab tagasi, kui lähete makselehele, et teilt võetaks täpselt need hinnad, mida teile näidati (brauseri saadetud hinda või hinnakirja ei kasutata kunagi). Statistika jaoks salvestab meie server anonüümseid loendusi hinnakirja kohta: et hinnakirja näidati, et tehti eelvaade, et avati makseleht ja et tellimuse eest maksti (vt [Teenuse statistika ja meie halduslogi](#operations)); need loendused ei sisalda külastajanumbrit. Teie brauser jätab kohalikus salvestusruumis meelde ka selle, millised neist loendustest ta on juba saatnud („snapeyes.expseen“), ja teie viimase hinnakirja („snapeyes.pricing“), et samad hinnad ilmuksid kohe. See, millist hinnakirja te näete, ei sõltu kunagi teie elukohast, vaid ainult teie valitud turust (valuutast), ja hind, mille maksate, on alati see, mida teile enne maksmist näidati; teie tellimuse kinnituses on nimetatud hinnakiri, mis kehtis. Kasutame neid kandeid ainult selle hinnatesti jaoks, mitte kunagi reklaamiks ega teie jälgimiseks teistel veebilehtedel. Kui te pigem ei sooviks osaleda, [avage see link](/?pricetest=off&lang=et): teie brauser hoiab siis ainult märget „snapeyes.notest“, kustutab külastajanumbri ja teised siin nimetatud kanded ning näitab ja võtab standardhindu; [see link](/?pricetest=on&lang=et) lülitab osalemise uuesti sisse. Kui teie brauser saadab signaali „Global Privacy Control“, loetakse ka seda selliseks valikuks. Samuti saate kõik need kanded igal ajal oma brauseri seadetes kustutada (siis saate uue juhusliku loosi). Õiguslik alus: meie õigustatud huvi kehtestada õiglased hinnad (IKÜMi artikli 6 lõike 1 punkt f). Võite igal ajal esitada vastuväite (vt [Teie õigused](#rights)).',
        'Kui jõuate meieni reklaami või meie lingi kaudu, millel on kampaaniakood, või mõnelt teiselt veebilehelt, hoiab teie brauser lühikest koodi teie brauseri vahekaardi seansisalvestusruumis võtme „snapeyes.c“ all: aadressi parameetrid, mis nimetavad reklaami nii, nagu selle tegija need sisestas (utm_source, utm_medium, utm_campaign, utm_term ja utm_content: platvorm, liik, kampaania, rühm ja reklaam; näiteks „utm_source=fb&utm_medium=tasuline&utm_campaign=kevad“), või kui neid ei ole, siis ainult selle veebilehe liik, kust tulite (näiteks „ref=facebook“: Facebook, Instagram, TikTok, Google, otsetulek või muu leht). Seansisalvestusruum kuulub ainult sellele ühele vahekaardile ja kustutatakse, kui selle sulgete. Kood on sama kõigile, kes sama reklaami kaudu tulid: seda ei tuletata teie andmetest ja see ei sisalda nime, e-posti aadressi, seadme andmeid ega klikinumbrit (aadressis olev klikinumber „fbclid“ ei ole kunagi selle osa; mis selle numbriga juhtub, on kirjeldatud jaotises [Meta piksel ja meie reklaamid](#meta)). Meie lehed saadavad selle koos oma anonüümsete lehe loenduste ja päringutega (fotokontroll, eelvaade, makseleht); tellimuse kirje säilitab selle ja Stripe’i makseleht saab selle makse metaandmetes, et saaksime näha, milline reklaam millise sammuni ja tellimuseni viis (vt [Teenuse statistika ja meie halduslogi](#operations) ja [Kui tellite](#orders)). Kasutame seda ainult selleks, mitte kunagi reklaamiks, profiilianalüüsiks ega teie jälgimiseks teistel veebilehtedel. Veebilehe kasutamiseks ei ole seda vaja: kui kustutate selle või teie brauser blokeerib seansisalvestusruumi, toimib kõik samamoodi ja puudu jääb ainult see loendus. Õiguslik alus: meie õigustatud huvi teada, kas meie enda reklaam toimib (IKÜMi artikli 6 lõike 1 punkt f). Võite igal ajal esitada vastuväite (vt [Teie õigused](#rights)).',
        'Kui tellite, hoiab leht teie brauseri vahekaardi seansisalvestusruumis ka kahte kannet. Seansisalvestusruum kuulub ainult sellele ühele vahekaardile ja kustutatakse, kui selle sulgete:',
        {
          ul: [
            '„snapeyes.order“: koostatava tellimuse number ja selle privaatne võti, et leht saaks teie tellimust jätkata, näiteks kui tulete makselehelt tagasi. See eemaldatakse, kui teie makstud tellimuse leht selles vahekaardis avaneb, ja asendatakse, kui alustate uut tellimust.',
            '„snapeyes.checkout“: ainult makselehel viibimise ajal teie kunstiteos sellisena, nagu te selle jätsite (iirise väljalõiked teie fotodest, eelvaated, mõned neist mõõdetud arvud, stiil ja selle variant, paigutus, silmade järjestus ning nimed ja kuupäev), et makselehelt tagasi minnes näidataks seda uuesti. See eemaldatakse niipea, kui tagasi tulete, või kui teie makstud tellimuse leht selles vahekaardis avaneb.',
          ],
        },
        'Leht kasutab neid ainult teie tellimuse jaoks ja need on selleks hädavajalikud, seega ei vaja ka need nõusolekut (e-privaatsuse direktiivi artikli 5 lõige 3).',
        'Kui maksate, võib Stripe’i makseleht kasutada oma küpsiseid, mida on vaja turvaliseks maksmiseks ja pettuste ennetamiseks; seal kehtivad Stripe’i enda privaatsus- ja küpsisepoliitika.',
      ],
    },
    {
      id: 'required',
      title: 'Kas peate meile andmeid andma?',
      blocks: ['Ei. Kuid ilma fotota ei saa me eelvaadet valmistada ning ilma e-posti aadressi ja makseta ei saa me tellimust üle anda.'],
    },
    {
      id: 'changes',
      title: 'Selle poliitika muutmine',
      blocks: ['Uuendame seda poliitikat, kui meie teenus või seadus muutub. Kuupäev lehe ülaosas näitab kehtivat versiooni.'],
    },
  ],
};
