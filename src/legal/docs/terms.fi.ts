// Myyntiehdot: the Finnish twin of `en` in src/legal/docs/terms.ts, same section ids and blocks in the same
// order, the same facts from src/landing/config.ts (through ../facts). Everything the English header says holds here
// too: no ODR link, no VAT number, no promise the code does not keep, the right of withdrawal ends when making the file
// begins (or with the 14-day period, counted as withdraw.py period_end counts it), the seller line has no phone (owner
// decision). Formal "te" (one reader: "olette antanut"), as the Finnish model withdrawal text of the Directive.
// The words behind the wording (Directive 2011/83/EU in its official Finnish text; Finland transposes it in
// kuluttajansuojalaki 38/1978, 6 luku, whose words "peruuttamisoikeus" and "peruuttamisaika" these terms use):
//  - Art. 8(2): the order button says "tilaukseen liittyy maksuvelvollisuus" or an equally unambiguous wording. Our
//    button (CHECKOUT_LEGAL.fi.continueButton, "Siirry maksamaan") places no order; the binding order is Stripe's pay
//    button (Stripe Checkout, locale "fi"), which the terms say ("Teette sitovan tilauksen, johon liittyy
//    maksuvelvollisuus, kun vahvistatte siellä maksun maksupainikkeella."). Whether Stripe's own Finnish label alone is
//    unambiguous enough is a question for a lawyer, as the German "Bezahlen" is.
//  - Art. 9: 14 days from the conclusion of the contract for digital content; Art. 16(m): the digital content exception
//    (express prior consent, acknowledgement of losing the right, the confirmation of Art. 8(7)); Art. 11a: the online
//    function ("Peruuta sopimus tästä", "Vahvista peruuttaminen"); Art. 13: refund within 14 days.
//  - The counting of the period (the day of payment not counted, a last day on a Saturday, Sunday or public holiday
//    moved to the next working day) is Regulation 1182/71 Art. 3, as withdraw.py period_end counts it.
//  - Out of court: the seller is Lithuanian, so the out-of-court body stays the Lithuanian Valstybinė vartotojų teisių
//    apsaugos tarnyba (VVTAT); no ODR link (the platform closed on 20 July 2025). "disputes" names the Finnish Act as the
//    mandatory law a consumer living in Finland keeps (Rome I Art. 6(2)); no Finnish authority is named.
//  - VAT: "Emme ole arvonlisäverovelvollisia, joten arvonlisäveroa ei peritä eikä näytetä.", the English sentence.
//  - The contract languages are named ("Sopimuskielet: suomi, englanti, saksa, liettua, unkari, kroatia, viro ja
//    latvia."): the other languages' terms must name Finnish too (the build checks it, scripts/check_texts.mjs CONTRACT).
//  - The latest delivery time is "N tunnin kuluessa" (tunnit below: the genitive is the same after every number, "1
//    tunnin", "48 tunnin").
// Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { DELIVERY_MAX_HOURS, MAIL, PRICE_CENTS, SELLER, address, company, eur, phoneSuffix, representedSuffix } from '../facts';
import { aiBlocks } from '../../shared/aiMaterial';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE } from '../../shared/legal';

const companyFi = company('fi');
const addressFi = address('fi');
const phoneSuffixFi = phoneSuffix('fi');
const representedSuffixFi = representedSuffix('fi');
const eurFi = (cents: number) => eur(cents, 'fi');
const WITHDRAWAL_ONLINE_FI = WITHDRAWAL_ONLINE.fi;
const CHECKOUT_LEGAL_FI = CHECKOUT_LEGAL.fi;

/** "48 tunnin", "1 tunnin": hours in the genitive, before "kuluessa". */
const tunnit = (n: number) => `${n} tunnin`;

const TRANSPARENCY_FI = 'Väri tulee omasta valokuvastanne. Kohdissa, joissa puhelimenne ei saanut hienoimpia säikeitä talteen, tekoälymme entisöi ne.';
const PX = '4096 px';
const SQUARE = '4096 × 4096 px';

const STANDARD_LIST_NOTE_FI =
  'Yllä oleva taulukko on vakiohinnastomme. Kokeilemme ajoittain rajoitetun ajan muita hinnastoja joillakin satunnaisesti valituilla kävijöillä. Teiltä veloitetaan aina ne hinnat, jotka teille näytetään taideteossivulla ennen maksamista ja maksusivulla, ja tilausvahvistuksenne kertoo, mitä hinnastoa tilaukseenne sovellettiin. Se, minkä hinnaston näette, ei koskaan riipu asuinmaastanne vaan ainoastaan valitsemastanne markkinasta (valuutasta).';
const PAY_FI = 'Maksatte etukäteen maksupalveluntarjoajamme Stripen kautta maksusivulla näkyvillä maksutavoilla.';

export const fi: LegalDoc = {
  title: 'Myyntiehdot',
  description:
    'SnapEyesin digitaalisen iiristaideteoksen tilausehdot: tuote, hinnat, maksaminen, toimitus, lisenssinne, peruuttamisoikeus ja reklamaatiot.',
  lead: 'Näitä ehtoja sovelletaan jokaiseen sivustolla snapeyes.com tehtyyn tilaukseen. Lukekaa ne ennen tilaamista. Ilmainen esikatselu ei sido teitä mihinkään.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'parties',
      title: 'Sopimuskumppaninne',
      blocks: [
        `Sopimuskumppaninne on ${companyFi}, Liettuan lain mukainen pienyhtiö (mažoji bendrija)${representedSuffixFi}, yritystunnus ${SELLER.code}, ${addressFi}, sähköposti ${MAIL}${phoneSuffixFi} (jäljempänä ”me” tai ”SnapEyes”). Kaikki tiedot ovat sivulla [Yritystiedot](doc:imprint).`,
        'Tarjouksemme on tarkoitettu kuluttajille. Jos ette ole täyttänyt 18 vuotta, pyytäkää vanhempaanne tai huoltajaanne tilaamaan puolestanne.',
      ],
    },
    {
      id: 'product',
      title: 'Mitä ostatte',
      blocks: [
        `Personoitu digitaalinen taideteos, joka tehdään omasta silmää (tai useita silmiä) esittävästä valokuvastanne valitsemallanne tyylillä, asettelulla ja tekstillä. Saatte yhden kuvatiedoston (JPEG) ilman vesileimaa: ${SQUARE} yhdelle silmälle, ${PX} pisimmältä sivulta useammalle silmälle. Taideteos toimitetaan vain digitaalisena tiedostona, lataamalla. Emme myy tulosteita, kehyksiä emmekä muita fyysisiä tuotteita.`,
        `${TRANSPARENCY_FI} Taideteos on siis taiteellinen entisöinti, ei lääketieteellinen kuva eikä mikroskooppikuva, eikä se sovellu mihinkään lääketieteelliseen tarkoitukseen eikä henkilön tunnistamiseen.`,
        ...aiBlocks('fi'),
      ],
    },
    {
      id: 'preview',
      title: 'Esikatselunne ja tiedostonne',
      blocks: [
        'Ennen tilaamista näette ilmaisen vesileimatun esikatselun ja hyväksytte sen. Tiedostonne noudattaa hyväksymäänne esikatselua: sama silmä, tyyli, asettelu, silmien järjestys ja teksti, sama väri ja sävy, tehtynä kerran täydellä tarkkuudella. Täydessä koossa tekoälymme lisää hienot säikeiden yksityiskohdat, joita esikatselu ei pienen kokonsa vuoksi pysty näyttämään, joten kaikkein hienoimmat yksityiskohdat voivat poiketa hieman esikatselusta. Esikatselu, jossa on viidestä kahdeksaan silmää, tehdään valokuvienne pienemmistä kopioista, joten se on karkeampi kuin tiedostonne.',
        'Jos tiedostonne poikkeaa selvästi hyväksymästänne esikatselusta (esimerkiksi värin, kirkkauden tai pupillin osalta), se on virhe: katsokaa [Reklamaatiot ja virheet](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'Miten sopimus syntyy',
      blocks: [
        `Verkkosivustomme esikatselut ja hinnat eivät vielä ole sitova tarjous. Ennen maksamista voitte tarkistaa silmänne, tyylin, asettelun ja tekstin ja korjata minkä tahansa tiedon palaamalla takaisin tai ottamalla kuvan uudelleen. Sen jälkeen avaatte painikkeellamme ”${CHECKOUT_LEGAL_FI.continueButton}” maksupalveluntarjoajamme Stripen maksusivun; tämä painike ei vielä tee tilausta. Maksusivulla annatte sähköpostiosoitteenne ja maksutietonne ja voitte korjata niitä. Teette sitovan tilauksen, johon liittyy maksuvelvollisuus, kun vahvistatte siellä maksun maksupainikkeella.`,
        'Sopimus syntyy, kun maksunne on vahvistettu. Silloin tilaussivunne avautuu, ja lähetämme sen linkin sähköpostiinne tilausvahvistuksen mukana. Alamme tehdä tiedostoanne siellä heti, kun tämä sähköposti on lähtenyt.',
        'Sopimuskielet: suomi, englanti, saksa, liettua, unkari, kroatia, viro ja latvia.',
        'Tallennamme tilauksenne ja sopimuksen tiedot: tilaamanne taideteoksen, hinnan, päivämäärän, sähköpostiosoitteenne ja suostumuksenne välittömään aloittamiseen. Tilaussivunne näyttää nämä tiedot niin kauan kuin säilytämme tilaustanne. Emme säilytä näistä ehdoista erillistä kopiota jokaista tilausta varten. Sen sijaan tilausvahvistuksenne sisältää tekstinä tilauksenne tiedot, nämä ehdot ja tiedot peruuttamisoikeudesta sekä malliperuuttamislomakkeen siinä muodossa, joka oli voimassa tilatessanne: säilyttäkää tuo sähköposti. Voitte myös tallentaa tai tulostaa tämän sivun milloin tahansa.',
      ],
    },
    {
      id: 'prices',
      title: 'Hinnat ja maksaminen',
      blocks: [
        {
          dl: [
            ['Yksi silmä, Clean Iris', eurFi(PRICE_CENTS.studioBlack)],
            ['Yksi silmä, mikä tahansa muu tyyli', eurFi(PRICE_CENTS.artBackground)],
            ['Kaksi silmää, mikä tahansa tyyli', eurFi(PRICE_CENTS.coupleDuo)],
            ['Jokainen lisäsilmä', `+${eurFi(PRICE_CENTS.extraEye)}`],
          ],
        },
        'Kaikki hinnat ovat lopullisia hintoja euroina. Emme ole arvonlisäverovelvollisia, joten arvonlisäveroa ei peritä eikä näytetä. Toimituskuluja ei ole.',
        STANDARD_LIST_NOTE_FI,
        PAY_FI,
      ],
    },
    {
      id: 'delivery',
      title: 'Toimitus',
      blocks: [
        `Tilaussivunne tekee tiedostonne heti, kun tilausvahvistus on lähtenyt sähköpostiinne, yleensä minuutin kuluessa maksustanne; tekeminen kestää yleensä muutaman minuutin. Jos suljette sivun ennen kuin tiedostonne on valmis, tekeminen jatkuu, kun avaatte sivun uudelleen sähköpostissa olevasta linkistä. Jos automaattinen laaduntarkastuksemme huomauttaa tiedostosta, katsomme sen itse ennen kuin luovutamme sen, ja lähetämme teille sähköpostia, kun se on valmis. **Tiedostonne on ladattavissa tilaussivultanne viimeistään ${tunnit(DELIVERY_MAX_HOURS)} kuluessa siitä, kun maksunne on vahvistettu.** Voitte ladata tiedostonne tilaussivultanne milloin tahansa niin kauan kuin säilytämme sitä: 12 kuukautta maksustanne (katsokaa [Tietosuojaseloste](doc:privacy)). Jokainen sivun luoma latauslinkki on voimassa 7 päivää; sivu tekee uuden linkin aina, kun avaatte sen. Jos kadotatte sähköpostin, kirjoittakaa meille.`,
        'Tilaussivunne linkki sisältää yksityisen avaimen: kuka tahansa, jolla linkki on, voi ladata taideteoksenne, joten pitäkää se omana tietonanne. Ladatkaa tiedostonne ja säilyttäkää siitä kopio. 12 kuukauden kuluttua se poistetaan, eikä sitä voi palauttaa.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Peruuttamisoikeus',
      blocks: [
        `Kuluttajana teillä on yleensä 14 päivän peruuttamisoikeus. Digitaalisessa tiedostossa se päättyy aikaisemmin: ennen maksamista pyydämme teitä suostumaan siihen, että alamme tehdä tiedostoanne heti, ennen peruuttamisajan päättymistä, ja vahvistamaan, että tiedätte menettävänne peruuttamisoikeutenne, kun olemme aloittaneet. Se päättyy siis heti, kun olemme alkaneet tehdä tiedostoanne (sopimuksen täyttäminen); aloitamme vasta, kun tilausvahvistus on lähtenyt sähköpostiinne, yleensä minuutin kuluessa maksustanne, kun tilaussivunne on auki. Tämä pätee, vaikka tiedostoa vielä tehtäisiin tai se odottaisi laaduntarkastustamme. Jos emme ole aloittaneet, se päättyy, kun 14 päivän peruuttamisaika on kulunut: maksupäiväänne ei lasketa mukaan, ja jos ajan viimeinen päivä on lauantai, sunnuntai tai yleinen vapaapäivä, aika päättyy seuraavan työpäivän päättyessä. Niin kauan kuin peruuttamisoikeutenne on voimassa, voitte peruuttaa sopimuksen sähköpostitse, postitse tai verkossa painikkeella ”${WITHDRAWAL_ONLINE_FI.button}”; tilausvahvistuksenne peruutuslinkki avaa toiminnon tilaustanne varten aloittamatta tiedostonne tekemistä. Kaikki tiedot, verkkotoiminto ja malliperuuttamislomake ovat sivulla [Peruuttamisoikeus](doc:withdrawal).`,
      ],
    },
    {
      id: 'photos',
      title: 'Valokuvanne',
      blocks: [
        'Lähettäkää vain kuvia omasta silmästänne tai sellaisen henkilön silmästä, joka on antanut siihen suostumuksensa (lapsen puolesta: vanhempi tai huoltaja). Lähettämällä kuvan vahvistatte, että saatte käyttää sitä tähän tarkoitukseen.',
        'Oikeudet valokuvaanne säilyvät teillä. Käytämme sitä vain esikatselunne ja taideteoksenne tekemiseen, kuten [tietosuojaselosteessamme](doc:privacy) kuvataan.',
        'Voimme kieltäytyä tilauksesta ja palauttaa mahdollisen maksun kokonaan, jos valokuva selvästi rikkoo näitä sääntöjä.',
      ],
    },
    {
      id: 'licence',
      title: 'Mitä saatte tehdä taideteoksellanne',
      blocks: [
        'Saatte ei-yksinomaisen, pysyvän lisenssin käyttää taideteostanne henkilökohtaisiin, ei-kaupallisiin tarkoituksiin. Voitte esimerkiksi tulostaa sen itsellenne (kotona tai tulostuspalvelussa), kehystää sen, antaa sen lahjaksi, käyttää sitä laitteidenne taustakuvana ja jakaa sen henkilökohtaisissa sosiaalisen median kanavissanne.',
        'Ilman lupaamme (sähköposti riittää) ette saa myydä taideteosta tai siitä tehtyjä tuotteita, antaa muille oikeuksia siihen ettekä käyttää sitä mainontaan tai muihin kaupallisiin tarkoituksiin.',
        'Tyylit, taustat, asettelut ja SnapEyes-ulkoasu pysyvät meidän omaisuutenamme, mukaan lukien niihin liittyvät tekijänoikeudet. Sama koskee vesileimattuja esikatseluja.',
      ],
    },
    {
      id: 'defects',
      title: 'Reklamaatiot ja virheet',
      blocks: [
        `Lakisääteiset oikeutenne, jotka koskevat sopimuksen vastaista digitaalista sisältöä, ovat voimassa täysimääräisinä. Jos tiedostossanne on virhe, esimerkiksi sitä ei voi ladata tai avata, se on vioittunut, se on luvattua pienempi tai se poikkeaa selvästi hyväksymästänne esikatselusta, kirjoittakaa osoitteeseen ${MAIL} ja kertokaa tilausnumeronne. Teemme tiedoston uudelleen maksutta tai, jos se ei korjaa virhettä, palautamme maksunne.`,
      ],
    },
    {
      id: 'liability',
      title: 'Vastuu',
      blocks: [
        'Vastaamme rajoituksetta tahallisuudesta ja törkeästä huolimattomuudesta, hengen, ruumiin tai terveyden vahingoittumisesta sekä aina, kun pakottava laki niin määrää. Muutoin vastaamme lievästä huolimattomuudesta vain, jos olemme rikkoneet olennaisia sopimusvelvoitteita, ja vain vahingosta, joka on tämänkaltaiselle sopimukselle tyypillinen ja ennakoitavissa. Ilmainen esikatselu tarjotaan sellaisenaan, eikä sen saatavuuteen ole oikeutta.',
      ],
    },
    {
      id: 'disputes',
      title: 'Riidat ja sovellettava laki',
      blocks: [
        'Jos jokin on vialla, kirjoittakaa ensin meille: useimmat ongelmat ratkeavat nopeasti sähköpostitse.',
        'Jos emme pääse sopuun, kuluttajat voivat kääntyä Liettuan valtion kuluttajaoikeuksien suojeluviraston (Valstybinė vartotojų teisių apsaugos tarnyba, [vvtat.lt](https://vvtat.lt)) puoleen, joka ratkaisee kuluttajariitoja tuomioistuimen ulkopuolella, tai oman maansa kuluttajaviranomaisten ja tuomioistuinten puoleen.',
        'Sopimukseen sovelletaan Liettuan lakia. Jos olette kuluttaja ja asutte toisessa EU-maassa, teillä säilyy kyseisen maan pakottavan kuluttajansuojalainsäädännön suoja (Suomessa: kuluttajansuojalaki).',
      ],
    },
    {
      id: 'changes',
      title: 'Näiden ehtojen muutokset',
      blocks: ['Tilaukseenne sovelletaan ehtoja, jotka olivat voimassa, kun teitte tilauksen.'],
    },
  ],
};

// No forint edition: the Hungarian edition (the hu market) has no Finnish texts (src/shared/legal.ts EDITION_LANGS), so there
// is no Finnish twin of huHufPrices.
