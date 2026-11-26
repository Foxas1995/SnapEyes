// Tietosuojaseloste (yleisen tietosuoja-asetuksen 13 artikla): the Finnish twin of `en` in src/legal/docs/privacy.ts,
// same section ids and blocks in the same order. Written from the same facts as the English file (see its header: what
// the code really does on 2026-09-29) and to be kept in step with it. Formal "te", as every Finnish legal text of the
// site. The GDPR is "yleinen tietosuoja-asetus" in Finnish, cited the Finnish way ("tietosuoja-asetuksen 6 artiklan 1
// kohdan f alakohta"); the controller is "rekisterinpitäjä", a hash is "tiiviste", local and session storage are
// "paikallinen tallennustila" and "istuntotallennus" (with the English term once in brackets). "rights" keeps the lead
// authority of the English text (the controller is established in Lithuania: the State Data Protection Inspectorate,
// VDAI) and names the Finnish authority a reader in Finland may also turn to (Art. 77 GDPR): Tietosuojavaltuutetun
// toimisto (tietosuoja.fi), as plain text, so the links stay exactly the English ones.
// Not reviewed by a lawyer. Keep every sentence true when the code or a service changes.
import type { LegalDoc } from '../types';
import { ORDER_EMAIL_SENDER, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';

const companyFi = company('fi');
const addressFi = address('fi');
const WITHDRAWAL_ONLINE_FI = WITHDRAWAL_ONLINE.fi;

// What the online withdrawal function keeps (the "withdrawal" section), as WITHDRAW_PRIVACY.en
const WITHDRAW_PRIVACY_FI = `Jos peruutatte tilauksen verkkotoiminnollamme (painike ”${WITHDRAWAL_ONLINE_FI.button}”, katsokaa [Peruuttamisoikeus](doc:withdrawal#online)), tallennamme peruuttamisilmoituksenne tilauksenne yhteyteen: nimenne, sähköpostiosoitteenne, tilausnumeron, ilmoituksen sanamuodon sekä päivämäärän ja kellonajan, jolloin se saapui meille. Käytämme sitä pysäyttääksemme tiedostonne tekemisen, jos emme ole vielä aloittaneet, lähettääksemme teille sähköpostitse vastaanottoilmoituksen, jossa on ilmoituksen sisältö, päivämäärä ja kellonaika, ja palauttaaksemme maksunne. Saamme jokaisen ilmoituksen myös sähköpostitse: yksitellen tai, kun ilmoitus ei vastaa yhtäkään tilaustamme tai koskee tilausta, jota ei koskaan maksettu, yhtenä koosteena päivässä. Jos peruutuksenne tulee voimaan, päivittäinen automaattinen siivouksemme poistaa tilauksenne kuvat, kun peruutuksesta on kulunut 14 päivää (jos maksuanne käsiteltiin vielä, vasta kun sen käsittely on päättynyt); tilaustietue ja ilmoituksenne säilyvät (katsokaa [Kuinka kauan säilytämme tietojanne](#retention)). Jos antamanne tiedot eivät vastaa yhtäkään tilaustamme (ilman tilaussivunne linkkiä tai tilausvahvistuksenne peruutuslinkkiä sähköpostiosoitteen on oltava se, jolla maksoitte), säilytämme ilmoituksen erillään, tarkistamme sen käsin, lähetämme teille silti sähköpostitse vastaanottoilmoituksen (kohdassa [Peruuttaminen verkossa](doc:withdrawal#online) kerrottujen väärinkäytön estävien rajojen puitteissa) ja poistamme sen automaattisesti noin 13 kuukautta sen kuukauden päättymisen jälkeen, jona se saapui meille.`;

// The admin log and the admin sign-in guard, as ADMIN_LOG.en
const ADMIN_LOG_FI = {
  log: 'Kun käsittelemme tilausta hallintapaneelissamme, esimerkiksi luovutamme tiedoston laaduntarkastuksen jälkeen, lähetämme sähköpostin uudelleen, teemme maksunpalautuksen tai poistamme tiedostoja, paneeli kirjoittaa merkinnän hallintalokiimme: mitä tehtiin, milloin, mille tilausnumerolle ja miten se päättyi. Hallintalokissa ei ole kuvia, sähköpostiosoitteita eikä linkkejä. Oikeusperuste: oikeutettu etumme käsitellä tilauksia turvallisesti ja jäljitettävästi (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Loki poistetaan automaattisesti 24 kuukauden kuluttua; tilausta koskevat merkinnät säilytetään myös kyseisen tilauksen tietueen yhteydessä niin kauan kuin tietuetta säilytetään (katsokaa [Kuinka kauan säilytämme tietojanne](#retention)).',
  signin: 'Hallintapaneelimme on vain meitä varten. Jotta kukaan ei voisi arvata sen avainta, epäonnistunut kirjautuminen tallentaa salaisella avaimella tehdyn tiivisteen IP-osoitteesta, josta se tuli, ei koskaan itse osoitetta, ja tiiviste poistetaan automaattisesti 2 päivän kuluttua. Oikeusperuste: oikeutettu etumme pitää järjestelmämme turvallisina (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta).',
};

// The admin panel's usage statistics and its admin log, as OPS.en
const OPS_FI = {
  events:
    'Jotta näemme, toimiiko palvelu, kuinka nopea se on ja mitä se maksaa, palvelimemme kirjaa pieniä teknisiä tapahtumia yksityiseen tallennustilaamme Supabasessa EU:ssa. Esimerkiksi: että valokuva tarkistettiin (ja tulos, kuten ”silmää ei löytynyt”, laitteen tyyppi, kuten iPhone, Android tai tietokone, se, tuliko kuva kamerasta vai galleriasta, ja sivun kieli), että heijastukset poistettiin, että esikatselu tai tilattu tiedosto tehtiin ja kuinka kauan se kesti, tai että pyyntö epäonnistui (ja sen virhekoodi). Kun testaamme hintoja, tapahtumat kertovat myös, mikä hinnasto (lyhyt koodi) näytettiin, esikatseltiin, avattiin maksamista varten tai maksettiin, sekä maksetun tilauksen summan. Hallintapaneelimme näyttää ne meille enimmäkseen päiväkohtaisina lukumäärinä.',
  counter:
    'Jotta näemme, kuinka moni pääsee sivuston kuhunkin vaiheeseen, palvelimemme laskee myös vaiheet, joihin sivu etenee: että ensimmäinen sivu avattiin, että kuvaussivu avattiin, että valokuva valittiin tai otettiin, että esikatselu näytettiin (ja montako sekuntia siihen kului valokuvasta), että ostokortti näytti, ettei tilaaminen ole vielä auki, että ostopainiketta painettiin ja että tilaussivu avattiin. Jokainen laskenta on pieni tietue numeroita ja lyhyitä koodeja: vaihe, sivun kieli, markkina (valuutta), laitteen tyyppi (iPhone, Android tai tietokone), selaimen tyyppi (esimerkiksi Chrome, Safari tai Facebook- tai Instagram-sovelluksen sisäinen selain) ja maa (kaksi kirjainta, jotka Vercel päättelee IP-osoitteestanne). Laitteen ja selaimen selvittämiseksi palvelimemme lukee hetken ajan selaimenne tunnisteen (user agent), ja pysäyttääkseen asiakasohjelman, joka lähettää aivan liian monta laskentaa, se pitää muistissaan vähemmän kuin minuutin ajan tiivistettä IP-osoitteestanne, tehtynä avaimella, joka katoaa, kun palvelin käynnistyy uudelleen; se ei tallenna kumpaakaan. Nämä laskennat eivät käytä evästettä eivätkä kävijänumeroa, eikä niissä ole IP-osoitetta, selaimen tunnistetta, sivun osoitetta eikä linkkiä, josta tulitte, joten niitä ei voi jäljittää teihin. Hallintapaneelissamme näemme ne päiväkohtaisina summina.',
  campaign:
    'Jos tulette meille mainoksen tai kampanjakoodin sisältävän linkkimme kautta tai toiselta verkkosivustolta, selaimenne säilyttää tuon koodin käyntinne ajan (katsokaa [Evästeet ja paikallinen tallennustila](#storage)), ja edellä mainitut laskennat, tekemänne kuvatarkistukset ja esikatselut, maksusivu ja tilauksenne kuljettavat sitä mukanaan, jotta näemme, mikä mainos johti mihinkin vaiheeseen, mitä se maksoi vaihetta kohden ja minkä tilauksen se toi. Koodi on sama kaikille, jotka seurasivat kyseistä mainosta, eikä sitä ole johdettu teistä.',
  feedback:
    'Tulosnäkymässä ja kortissa, joka pyytää toista valokuvaa, pieni palauteruutu tarjoaa kuusi vastausta (esimerkiksi ”Ihana” tai ”Värit näyttävät vääriltä”) ja halutessanne enintään 300 merkin tekstin. Mitään ei lähetetä ennen kuin painatte Lähetä-painiketta. Ruudussa ei ole kenttää nimellenne eikä sähköpostiosoitteellenne: älkää kirjoittako niitä, älkääkä puhelinnumeroita tai linkkejä. Kun painatte Lähetä-painiketta, palvelimemme kirjaa vastauksenne yhtenä uutena pienenä koodeista koostuvana tapahtumana (vastaus, näytöllä ollut tyyli tai syy, jonka vuoksi valokuva hylättiin, silmien määrä, se, tuliko mukana tekstiä, ja samat tiedot kuin edellä kuvatuissa vaihelaskennoissa: kampanjakoodi, sivun kieli, markkina, laitteen ja selaimen tyyppi sekä maa). Teksti tallennetaan erikseen, näiden koodien kanssa eikä minkään muun, ja vain jos se läpäisee tarkistuksen: tekstiä, jossa on @-merkki, puhelinnumero, linkki tai jotain roskapostilta näyttävää, ei säilytetä (vastauksenne lasketaan silti). Luemme tekstit hallintapaneelissamme; emme voi vastata, koska emme tiedä, kuka ne on kirjoittanut. Jokainen teksti poistetaan automaattisesti 90 päivän kuluttua, ja voimme poistaa tekstin aikaisemminkin. Koska mikään ruudussa ei tunnista teitä, voimme löytää tekstinne myöhemmin vain, jos kerrotte meille, mitä siinä luki. Ruutu ei kirjoita mitään selaimeenne.',
  content:
    '**Näissä tapahtumissa ei ole kuvaa, kirjoittamaanne tekstiä (palauteruutuun kirjoitettu teksti tallennetaan niistä erilleen edellä kuvatulla tavalla), nimeä, sähköpostiosoitetta, IP-osoitetta, selaimen tunnistetta (user agent) eikä linkkiä.** Ilmaisen esikatselun tapahtumia ei voi jäljittää teihin. Vain maksetun tilauksen tiedoston tekemistä koskevissa tapahtumissa on myös sen tilausnumero, jotta voimme löytää hitaan tai epäonnistuneen tekemisen; tilaustietueidemme kautta tuo numero liittyy tilaukseenne.',
  basis:
    'Oikeusperuste: oikeutettu etumme ylläpitää palvelua luotettavasti, löytää viat, pitää sen kustannukset hallinnassa ja saada tietää, mikä karkottaa kävijöitä (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Tapahtumat ja niistä tehdyt päiväkohtaiset lukumäärät poistetaan automaattisesti 12 kuukauden kuluttua, palauteruudun tekstit 90 päivän kuluttua. Voitte vastustaa käsittelyä milloin tahansa (katsokaa [Oikeutenne](#rights)).',
  admin: ADMIN_LOG_FI.log,
  signin: ADMIN_LOG_FI.signin,
  previewcap: 'Jotta ilmainen esikatselu pysyy ilmaisena kaikille, yhdeltä internetyhteydeltä voi tehdä rajoitetun määrän esikatseluja päivässä. Jokaisesta esikatselusta palvelimemme tallentaa salaisella avaimella tehdyn tiivisteen IP-osoitteesta, josta esikatselu tehtiin, ja päivästä, ei koskaan itse osoitetta: osoitetta ei voi lukea siitä takaisin, ja seuraavana päivänä sama osoite antaa toisen tiivisteen. Nämä merkinnät poistetaan automaattisesti 2 päivän kuluttua. Oikeusperuste: oikeutettu etumme pitää ilmainen esikatselu saatavilla ja sen kustannukset hallinnassa (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta).',
};

const repFi = SELLER.representative ? ` Yhtiötä edustaa ${SELLER.representative}.` : '';
const senderFi = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: tilaustanne koskevien sähköpostien lähettäminen (tilaussivunne linkki, tilausvahvistus ja, jos peruutatte sopimuksen, vastaanottoilmoitus). Palvelun palvelimet voivat sijaita EU:n ulkopuolella.`];
const hostingerFi = ORDER_EMAIL_SENDER === 'Hostinger'
  ? 'Hostinger: sähköpostimme, postilaatikko info@snapeyes.com, mukaan lukien tilaustanne koskevat sähköpostit.'
  : 'Hostinger: postilaatikkomme info@snapeyes.com.';

export const fi: LegalDoc = {
  title: 'Tietosuojaseloste',
  description:
    'Miten SnapEyes käsittelee silmänne valokuvaa, esikatseluanne ja, jos tilaatte, tilauksenne tietoja: mitä käsittelemme, miksi, millä palveluilla, kuinka kauan ja mitkä ovat oikeutenne.',
  lead:
    'Tämä seloste kertoo, mitä tiedoillenne tapahtuu, kun käytätte sivustoa snapeyes.com: ilmaista esikatselua ja, jos tilaatte, digitaalista taideteostanne. Lyhyesti: valokuvaanne käytetään taideteoksenne tekemiseen ja sen laadun tarkistamiseen, ei koskaan kenenkään tunnistamiseen eikä koskaan tekoälyn kouluttamiseen. Säilytämme ilmaisia esikatseluja 30 päivää niiden laadun tarkistamiseksi ja parantamiseksi, ja poistamme ne sen jälkeen. Maksettujen tilausten tiedostoja säilytetään 12 kuukautta, jotta voitte ladata ne uudelleen, ja sen jälkeen ne poistetaan.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'controller',
      title: 'Kuka vastaa tiedoistanne',
      blocks: [
        `Tietojenne rekisterinpitäjä on ${companyFi} (yritystunnus ${SELLER.code}), ${addressFi}. SnapEyes on sen tuotemerkki.${repFi}`,
        `Kaikissa tietosuojaa koskevissa kysymyksissä ja käyttääksenne mitä tahansa oikeuttanne kirjoittakaa osoitteeseen ${MAIL}. Emme ole nimittäneet tietosuojavastaavaa.`,
      ],
    },
    {
      id: 'website',
      title: 'Kun käytte verkkosivustolla',
      blocks: [
        'Kun avaatte sivuston snapeyes.com sivun, selaimenne lähettää teknisiä tietoja palvelintilan tarjoajallemme Vercelille, kuten IP-osoitteenne, päivämäärän ja kellonajan, pyydetyn sivun ja selaimenne tyypin (user agent). Vercel tarvitsee näitä tietoja toimittaakseen sivun ja suojatakseen palvelua hyökkäyksiltä. Niitä säilytetään palvelinlokeissa lyhyen aikaa, ja sen jälkeen ne poistetaan.',
        'Voidaksemme ehdottaa hintoja omassa valuutassanne palvelimemme voi myös lukea maan, jonka Vercel päättelee IP-osoitteestanne (esimerkiksi ”AU”). Sitä käytetään tuohon ehdotukseen, eikä se koskaan muuta näkemiänne hintoja. Sitä ei tallenneta minkään sellaisen yhteyteen, mikä voisi tunnistaa teidät: sen ainoa jälki on maan kaksi kirjainta nimettömissä laskennoissamme (katsokaa [Palvelun tilastot ja hallintalokimme](#operations)).',
        'Oikeusperuste: oikeutettu etumme turvalliseen ja toimivaan verkkosivustoon (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta).',
        'Fonttimme tarjoillaan omalta palvelimeltamme, joten mitään tietoja ei mene Google Fonts -palveluun eikä muuhunkaan fonttipalveluun. Omat nimettömät palvelutilastomme kuvataan kohdassa [Palvelun tilastot ja hallintalokimme](#operations). Muiden yritysten työkaluista käytämme tällä verkkosivustolla yhtä, Meta-pikseliä mainoksiamme varten: katsokaa [Meta-pikseli ja mainoksemme](#meta).',
      ],
    },
    {
      id: 'preview',
      title: 'Ilmainen esikatselunne',
      blocks: [
        'Esikatselunne tekemiseksi lähetätte selaimestanne yhden tai useamman silmän valokuvan palvelintoiminnoillemme. Siellä valokuva käsitellään muistissa: etsimme iiriksen, rajaamme sen, tarkistamme, onko se tarpeeksi terävä ja valoisa, poistamme heijastukset, entisöimme hienot säikeet Googlen Gemini API:lla ja asetamme iiriksen näkemiinne tyyleihin. Tulos palaa selaimeenne. Jokainen siirto on salattu (HTTPS).',
        '**Säilytämme kopion ilmaisesta esikatselustanne 30 päivää.** Palvelimemme tallentaa yksityiseen Supabase-tallennustilaamme EU:ssa: lähettämänne valokuvat (pienennettyinä, pidemmältä sivultaan enintään 1280 pikseliä), iiriksen ympäriltä rajatun neliön, sen entisöinnin, teille näytetyt esikatselut sekä nimettömät koodit: mitä tarkistuksemme havaitsivat (esimerkiksi voiko valokuvaa käyttää ja jos ei, miksi), tyylin, ajan sekä saman nimettömän taustatiedon kuin palvelutilastoissamme (kampanjakoodi, laitteen ja selaimen tyyppi, kieli ja maa). Säilytämme ne tarkistaaksemme ja parantaaksemme esikatselujemme laatua ja selvittääksemme, miksi valokuvat epäonnistuvat. Vain me näemme ne, hallintapaneelissamme. Niitä ei yhdistetä nimeenne, sähköpostiosoitteeseenne eikä IP-osoitteeseenne, eikä niitä, kuten ei mitään muutakaan, koskaan käytetä kenenkään tunnistamiseen, myydä tai käytetä tekoälyn kouluttamiseen. Päivittäinen siivouksemme poistaa ne automaattisesti 30 päivän kuluttua. Esikatselu pysyy myös selaimessanne, kunnes suljette sivun (kun olette maksusivulla, selaimenne välilehden istuntotallennuksessa: katsokaa [Evästeet ja paikallinen tallennustila](#storage)), ellette tallenna sitä itse. Kun aloitatte tilauksen, säilytämme iiriksen rajauksen ja hyväksymänne esikatselun lisäksi tilauksen yhteydessä: katsokaa [Kun tilaatte](#orders).',
        'Google käsittelee kuvan entisöinnin tekemiseksi. Käytämme Googlen maksullista API-palvelua, jonka ehtojen mukaan Google ei käytä kuvia tuotteidensa parantamiseen eikä malliensa kouluttamiseen. Google voi säilyttää pyyntöjä rajoitetun ajan ainoastaan väärinkäytön havaitsemiseksi ja lain edellyttämiä luovutuksia varten.',
        'Oikeusperuste: pyydätte meitä tekemään esikatselunne, ja valokuva tarvitaan sitä varten (tietosuoja-asetuksen 6 artiklan 1 kohdan b alakohta, pyynnöstänne tehtävät toimenpiteet).',
        `Tämän kopion oikeusperuste: oikeutettu etumme tarkistaa ja parantaa esikatselujemme laatua ja selvittää, miksi valokuvat epäonnistuvat (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Voitte milloin tahansa vastustaa sitä tai pyytää sen poistamista: kirjoittakaa osoitteeseen ${MAIL} ja kertokaa käyntinne likimääräinen päivä ja kellonaika, jotta löydämme sen.`,
        'Ohjelmistomme päättää automaattisesti, voiko valokuvaa käyttää (esimerkiksi kun se on liian epätarkka tai liian tumma). Tällä päätöksellä ei ole teihin kohdistuvia oikeusvaikutuksia eikä muita vastaavia merkittäviä vaikutuksia: voitte yksinkertaisesti ottaa toisen kuvan.',
      ],
    },
    {
      id: 'iris',
      title: 'Iiristänne ei koskaan käytetä tunnistamiseen',
      blocks: [
        'Iiristä voidaan periaatteessa käyttää ihmisen tunnistamiseen. Me emme tee niin. Emme koskaan luo, vertaa emmekä tallenna iirismallia tai muuta biometristä tunnistetta, emme koskaan käytä kuvianne kenenkään tunnistamiseen tai todentamiseen, emme koskaan myy niitä emmekä koskaan käytä niitä tekoälyn kouluttamiseen, emme omamme emmekä kenenkään muun.',
        'Käyttäkää vain omaa silmäänne tai sellaisen henkilön silmää, joka on antanut siihen suostumuksensa. Lapsen puolesta suostumuksen antaa vanhempi tai huoltaja.',
        'Jos lisäätte muiden ihmisten silmiä (esimerkiksi paria varten), käsittelemme heidän kuviaan vain sen taideteoksen tekemiseksi, johon he ovat suostuneet. Oikeusperuste: teidän ja meidän oikeutettu etumme tuon taideteoksen tekemiseen (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Näyttäkää heille tämä seloste.',
      ],
    },
    {
      id: 'measurements',
      title: 'Tekniset mittaukset (ei kuvia)',
      blocks: [
        'Jokaisen valokuvan yhteydessä palvelimemme kirjoittaa lokeihinsa yhden rivin, jotta voimme parantaa kuvausohjetta ja palvelun laatua. Rivillä on valokuvan mittaustuloksia (esimerkiksi iiriksen koko pikseleinä, terävyys, kirkkaus, valon värivirhe ja se, voitiinko valokuvaa käyttää), teknisiä tietoja laitteestanne (selaimen tyyppi ja versio, näytön koko, se, tuliko kuva kamerasta vai galleriasta) ja, jos vastaatte otosta koskeviin vapaaehtoisiin kysymyksiimme, vastauksenne. Siinä ei ole kuvaa, nimeä eikä yhteystietoja.',
        'Palvelintilan tarjoajamme säilyttää näitä lokirivejä lyhyen aikaa, ja sen jälkeen ne poistetaan. Oikeusperuste: oikeutettu etumme parantaa palvelua (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Voitte vastustaa käsittelyä milloin tahansa (katsokaa [Oikeutenne](#rights)).',
      ],
    },
    {
      id: 'operations',
      title: 'Palvelun tilastot ja hallintalokimme',
      blocks: [OPS_FI.events, OPS_FI.counter, OPS_FI.campaign, OPS_FI.feedback, OPS_FI.content, OPS_FI.basis, OPS_FI.admin, OPS_FI.signin, OPS_FI.previewcap],
    },
    {
      id: 'meta',
      title: 'Meta-pikseli ja mainoksemme',
      blocks: [
        'Mainostamme Facebookissa ja Instagramissa. Jotta tietäisimme, mitkä mainoksistamme tuovat kävijöitä ja tilauksia, ja jotta Meta voisi näyttää niitä ihmisille, joita ne todennäköisesti kiinnostavat, sivumme käyttävät Meta-pikseliä, joka on Meta Platforms Ireland Limitedin (Merrion Road, Dublin 4, D04 X2K5, Irlanti; ”Meta”) työkalu. Se toimii sivuillamme jokaisella kävijällä; emme kysy teiltä sitä etukäteen.',
        'Pikseli kertoo Metalle, kun sivu avataan, kun kuvasivu avataan, kun teille näytetään ilmainen esikatselu, kun siirrytte maksusivulle ja kun maksu tehdään, maksun summan ja valuutan sekä tiedon siitä, maksettiinko taideteoksesta, lahjakortista vai tulosteesta. Jokaisen tällaisen ilmoituksen mukana selaimenne lähettää Metalle, kuten minkä tahansa pyynnön mukana, IP-osoitteenne ja selaimen tunnisteen (user agent), sivun ja sen sivun osoitteen, jolta tulitte, sekä alla kuvatut Metan evästeet. Tilaussivultamme ja lahjakorttisivultamme lähetetään vain sivun polku (”/order”, ”/gift”), ei koskaan sen koko osoitetta, jossa on tilauksenne avain tai maksunne numero. Jos käytätte Facebookia tai Instagramia, Meta voi yhdistää nämä ilmoitukset tiliinne.',
        '**Emme koskaan lähetä Metalle valokuvaanne, iiristänne, silmienne väriä, valitsemaanne tyyliä, lisäämiänne nimiä tai päivämäärää, taideteostanne emmekä mitään muuta kuvaa.** Pikselin automaattiset toiminnot, jotka lukisivat sivun painikkeita ja lomakekenttiä, on kytketty pois päältä.',
        'Metan skripti, jonka selaimenne lataa osoitteesta connect.facebook.net vasta sivumme latauduttua, asettaa snapeyes.comiin kaksi evästettä: ”_fbp”, satunnaisluku, josta Meta tunnistaa selaimenne myöhemmillä käynneillä ja joka säilyy 90 päivää viimeisestä käynnistänne, sekä vain silloin, kun tulitte Metan napsautusnumeron (”fbclid”, esimerkiksi mainoksesta) sisältävän linkin kautta, ”_fbc”, joka sisältää tuon numeron, samoin 90 päivää. Jos tulitte tällaisen linkin kautta eikä selaimessanne ole ”_fbc”-evästettä, sivumme säilyttää napsautusnumeron selaimenne välilehden istuntotallennuksessa avaimella ”snapeyes.fbc”, kunnes suljette välilehden. Ilmoitukset menevät osoitteeseen www.facebook.com. Tilaussivumme ja lahjakorttisivumme eivät lataa Metan skriptiä: ne lähettävät ilmoituksensa yksittäisinä pyyntöinä osoitteeseen www.facebook.com.',
        'Kun maksatte taideteoksesta, lahjakortista tai tulosteesta, palvelimemme ilmoittaa maksusta myös suoraan Metalle (Metan Conversions API), jotta se lasketaan silloinkin, kun selaimenne ilmoitus ei mene perille. Tässä ilmoituksessa on: että maksu tehtiin, milloin, sen summa ja valuutta, maksettiinko taideteoksesta, lahjakortista vai tulosteesta, sivun polku (”/order” tai ”/gift”), tiiviste sähköpostiosoitteesta, jolla maksoitte (SHA-256: osoitetta ei voi lukea siitä takaisin, mutta Meta voi verrata sitä omien käyttäjiensä osoitteiden tiivisteisiin), maanne (maksutiedoistanne tai valitsemistanne hinnoista) sekä ”_fbp”- ja ”_fbc”-evästeiden arvot, IP-osoite ja selaimen tunniste, jotka selaimellanne oli, kun avasitte maksusivun. Saman maksun molemmissa ilmoituksissa on sama numero, jotta Meta laskee sen kerran. Jotta palvelimellamme olisi ne maksun hetkellä, nämä neljä arvoa kulkevat maksusivun mukana Stripelle maksun metatiedoissa ja jäävät Stripen maksutietueeseen (katsokaa [Kun tilaatte](#orders)); muualle emme niitä tallenna.',
        'Käytämme näitä ilmoituksia mitataksemme, mitkä mainoksistamme toimivat, ja näyttääksemme niitä ihmisille, joita ne todennäköisesti kiinnostavat. Oikeusperuste: oikeutettu etumme mitata ja kohdentaa omaa mainontaamme (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Näiden tietojen keräämisestä verkkosivustollamme ja niiden välittämisestä Metalle vastaamme yhdessä Metan kanssa yhteisinä rekisterinpitäjinä (tietosuoja-asetuksen 26 artikla) Metan liiketoimintatyökalujen ehtojen mukaisesti, ja voitte käyttää oikeuksianne kumpaa tahansa meistä kohtaan. Sen, mitä Meta tekee tiedoilla tämän jälkeen, Meta päättää itsenäisenä rekisterinpitäjänä oman tietosuojakäytäntönsä mukaisesti; Meta voi käsitellä niitä Yhdysvalloissa EU:n ja Yhdysvaltojen välisen tietosuojakehyksen perusteella.',
        'Voitte vastustaa käsittelyä milloin tahansa: kirjoittakaa meille (katsokaa [Oikeutenne](#rights)). Voitte myös poistaa tai estää Metan evästeet ja istuntotallennuksen selaimenne asetuksista tai käyttää selainta tai laajennusta, joka estää tällaiset työkalut; sivustomme toimii ilman niitä samoin. Facebook- tai Instagram-tilillänne (Tilikeskus, mainosasetukset) voitte valita, saako Meta käyttää muilta verkkosivustoilta saatuja tietoja näyttääkseen teille mainoksia.',
      ],
    },
    {
      id: 'orders',
      title: 'Kun tilaatte',
      blocks: [
        'Kun aloitatte tilauksen, yksityiseen tallennustilaamme lähetetään kaksi kuvaa jokaisesta silmästä, jotta tiedostonne tehdään täsmälleen siitä, mitä näitte: valokuvastanne rajattu neliö iiriksenne ympäriltä (heijastukset poistettuina) ja hyväksymänne esikatselu. Niiden yhteydessä säilytämme lyhyen tietueen kyseisestä esikatselusta tehdyistä mittauksista (iiristänne ympäröivät värit, väriluokka, pupillin muoto, kaksi laatuarvoa ja koodi, joka yksilöi esikatselun). Siinä ei ole kuvaa, ja se poistetaan yhdessä kuvien kanssa. **Tilaukseenne ei tallenneta koko puhelinkuvaanne;** ilmaista esikatselua varten lähettämienne valokuvien kopiota säilytetään siitä erillään 30 päivää (katsokaa [Ilmainen esikatselunne](#preview)). Tilausta, jota ei makseta 24 tunnin kuluessa, ei voi enää maksaa. Kerran päivässä käynnistyvä automaattinen siivous poistaa silloin sen kuvat ja tietueet, yleensä kahden päivän kuluessa tilauksesta ja viimeistään 30 päivän kuluessa.',
        'Lähetysten pitämiseksi rajoissa palvelimemme kirjoittaa jokaisesta lähetyksestä myös pienen merkinnän (sen koko, päivä ja tilausnumero, ei kuvaa). Nämä merkinnät poistetaan automaattisesti muutaman päivän kuluttua.',
        'Myydäksemme ja toimittaaksemme taideteoksenne käsittelemme: tilauksen (tilausnumero, päivämäärä, silmät, tyyli, asettelu, silmien järjestys, lisäämänne nimet, päivämäärä tai teksti, kieli, hinta), sähköpostiosoitteenne (annatte sen maksusivulla), Stripeltä saamamme maksun tilan, suostumuksenne välittömään aloittamiseen (katsokaa [Peruuttamisoikeus](doc:withdrawal)) ja tilauksenne tiedostot: edellä mainitut kaksi kuvaa jokaisesta silmästä, jokaisen silmän 4096 px:n renderöinti ja valmis taideteos sekä tekniset laatutietueet.',
        'Säilytämme näitä tiedostoja yksityisessä tallennustilassa Supabasessa, joka sijaitsee EU:ssa. Pääsette niihin tilaussivunne kautta, jonka linkin lähetämme sähköpostiinne; linkki sisältää yksityisen avaimen, joten kuka tahansa, jolla linkki on, voi ladata taideteoksenne. Jokainen sivun luoma latauslinkki vanhenee 7 päivän kuluttua.',
        'Voimme katsoa tilauksenne tiedostoja tarkistaaksemme niiden laadun, esimerkiksi kun automaattinen tarkistuksemme ilmoittaa erosta hyväksymäänne esikatseluun.',
        'Oikeusperuste: sopimus kanssanne (tietosuoja-asetuksen 6 artiklan 1 kohdan b alakohta); kirjanpitoaineiston osalta lakisääteiset velvoitteemme (tietosuoja-asetuksen 6 artiklan 1 kohdan c alakohta).',
        'Kun siirrytte maksusivulle, välitämme tilauksen tiedot Stripelle maksunne mukana: tilausnumeron, hinnan (ja kun hintatestiä sovellettiin, sen nimen, hinnastonne koodin ja kyseisen hinnaston hinnat), silmien määrän, tyylin (ja sen ilmeen), asettelun, silmien järjestyksen, kielen, lisäämänne nimet, päivämäärän tai tekstin, lyhyen koodin, joka yksilöi taideteoksen suunnitelman ja sen tekevän ohjelmistomme version, suostumuksenne version ja ajankohdan sekä, jos tulitte mainoksen kautta, sen kampanjakoodin. Stripe säilyttää ne maksutietueen yhteydessä, ja luemme ne sieltä takaisin tehdäksemme täsmälleen sen taideteoksen, josta maksoitte. Niin kauan kuin ilmoitamme maksuista Metalle, maksun mukana kulkevat myös Metan evästeiden ”_fbp” ja ”_fbc” arvot, jos selaimessanne niitä on, sekä IP-osoite ja selaimen tunniste, jotka selaimellanne oli sillä hetkellä (katsokaa [Meta-pikseli ja mainoksemme](#meta)).',
        'Maksaminen: Stripe käsittelee maksunne. Emme koskaan näe koko korttinumeroanne. Stripe käsittelee maksutietoja myös oman tietosuojaselosteensa mukaisesti petosten torjumiseksi ja omien lakisääteisten velvoitteidensa täyttämiseksi.',
        'Tarvitsemme sähköpostiosoitteenne lähettääksemme teille tilaussivunne linkin ja tilausvahvistuksen. Ilman sitä voisitte menettää pääsyn tiedostoonne.',
      ],
    },
    {
      id: 'email',
      title: 'Kun kirjoitatte meille',
      blocks: [
        'Jos lähetätte meille sähköpostia, käytämme osoitettanne ja viestiänne vastataksemme teille ja, jos viesti koskee tilausta, käsitelläksemme kyseisen tilauksen. Oikeusperuste: tilausten osalta tietosuoja-asetuksen 6 artiklan 1 kohdan b alakohta, muutoin oikeutettu etumme vastata teille (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Jos lähetätte meille valokuvia, esimerkiksi silmästänne, jotta voimme neuvoa teitä paremman otoksen ottamisessa, käytämme niitä vain pyyntöänne varten. Säilytämme sähköpostejanne mahdollisine valokuvineen niin kauan kuin tarvitsemme niitä pyyntöänne ja sen jatkokäsittelyä varten.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Kun peruutatte tilauksen verkossa',
      blocks: [
        WITHDRAW_PRIVACY_FI,
        'Oikeusperuste: lakisääteinen velvoitteemme ottaa peruutuksenne vastaan ja vahvistaa se teille (tietosuoja-asetuksen 6 artiklan 1 kohdan c alakohta) sekä sopimus kanssanne (tietosuoja-asetuksen 6 artiklan 1 kohdan b alakohta). Säilytämme ilmoituksen tilaustietueenne yhteydessä todisteena niin kauan kuin tuota tietuetta säilytetään (katsokaa [Kuinka kauan säilytämme tietojanne](#retention)).',
      ],
    },
    {
      id: 'services',
      title: 'Käyttämämme palvelut',
      blocks: [
        'Käytämme näitä palveluja SnapEyesin ylläpitämiseen:',
        {
          ul: [
            'Vercel: verkkosivuston ja niiden palvelintoimintojen isännöinti, jotka tekevät esikatselunne ja tiedostonne. Vercelin datakeskukset voivat sijaita EU:n ulkopuolella, esimerkiksi Yhdysvalloissa.',
            'Google (Gemini API): iiriksen tekoälyentisöinti ja valokuvanne tarkistukset. Googlen palvelimet voivat sijaita EU:n ulkopuolella.',
            'Supabase: tilausten tiedostojen ja ilmaisten esikatselujen 30 päivän kopioiden yksityinen tallennus EU-alueella.',
            'Stripe: maksujen käsittely kohdassa [Kun tilaatte](#orders) mainituin tilaustiedoin.',
            hostingerFi,
            ...senderFi,
            'Meta (Meta Platforms Ireland Limited): Meta-pikseli ja ilmoitukset maksuista, katsokaa [Meta-pikseli ja mainoksemme](#meta). Meta voi käsitellä tietoja Yhdysvalloissa.',
          ],
        },
        `Nämä palveluntarjoajat käsittelevät tietojanne meidän lukuumme ja ohjeidemme mukaisesti (Stripe osittain itsenäisenä rekisterinpitäjänä, katsokaa [Kun tilaatte](#orders); Meta kohdassa [Meta-pikseli ja mainoksemme](#meta) kuvatulla tavalla). Kun tietoja siirretään EU:n tai ETA:n ulkopuolelle, se tapahtuu palveluntarjoajien tarjoamin suojatoimin, kuten Euroopan komission vakiosopimuslausekkeilla tai EU:n ja Yhdysvaltojen välisellä tietosuojakehyksellä. Voitte pyytää meiltä kopion näistä suojatoimista osoitteesta ${MAIL}.`,
        'Emme myy tietojanne emmekä luovuta niitä kenellekään muulle, ellei laki velvoita meitä siihen.',
      ],
    },
    {
      id: 'retention',
      title: 'Kuinka kauan säilytämme tietojanne',
      blocks: [
        {
          dl: [
            ['Ilmaiset esikatselut', 'Lähetettyjen valokuvien, iiriksen rajauksen, entisöinnin, esikatselujen ja niiden nimettömien koodien kopio: poistetaan automaattisesti 30 päivän kuluttua tai pyynnöstä aiemmin.'],
            ['Maksamattomat tilaukset', 'Tilausta, jota ei makseta 24 tunnin kuluessa, ei voi enää maksaa. Päivittäinen automaattinen siivouksemme poistaa sen kuvat ja tietueet, yleensä kahden päivän kuluessa tilauksesta ja viimeistään 30 päivän kuluessa.'],
            ['Lähetysten ja ilmoitusten merkinnät', 'Pieniä laskureita ilman kuvia, nimiä tai sähköpostiosoitteita (vastaanottoilmoitusten laskurissa on vain lyhyt tiiviste sähköpostiosoitteesta), poistetaan automaattisesti muutaman päivän kuluttua; vastaanottoilmoitusten kuukausilaskurit noin 40 päivää kuukautensa päättymisen jälkeen.'],
            ['Maksetut tilaukset', 'Tilauksenne tiedostoja säilytetään 12 kuukautta maksustanne, jotta voitte ladata ne uudelleen tilaussivultanne, ja sen jälkeen päivittäinen automaattinen siivouksemme poistaa ne. Pyynnöstä poistamme ne aikaisemmin; sen jälkeen tilaussivunne ei voi enää toimittaa tiedostoa.'],
            ['Peruutetut tilaukset', 'Jos peruutus tulee voimaan, päivittäinen siivouksemme poistaa tilauksen kuvat, kun peruutuksesta on kulunut 14 päivää (jos maksua käsiteltiin vielä, kun sen käsittely on päättynyt).'],
            ['Peruuttamisilmoitukset, jotka eivät vastaa yhtäkään tilausta', 'Säilytetään erillään, tarkistetaan käsin ja poistetaan automaattisesti noin 13 kuukautta sen kuukauden päättymisen jälkeen, jona ne saapuivat meille.'],
            ['Tilaustietueet', 'Kun tiedostot poistetaan (12 kuukauden kuluttua, peruutuksen jälkeen tai pyynnöstä), säilytämme maksetun tilauksen tietueen: tilausnumeron, päivämäärän, hinnan, maksun ja mahdollisen maksunpalautuksen, sähköpostiosoitteenne, sen mainoksen kampanjakoodin, jonka kautta tulitte (jos sellainen on), tilaamanne taideteoksen tiedot (joihin voi kuulua lisäämiänne nimiä, päivämäärä tai teksti sekä lyhyt yhteenveto esikatseluistanne tehdyistä mittauksista: kunkin silmän väriluokka, renkaan keskimääräinen väri ja pupillin muoto), suostumuksenne välittömään aloittamiseen, peruuttamisilmoituksenne, jos peruutitte sopimuksen, sekä hallintalokimme merkinnät tilauksestanne. Ei kuvia. Säilytämme sen todisteena sopimuksesta ja kirjanpitoa varten niin kauan kuin Liettuan kirjanpito- ja verolainsäädäntö edellyttää.'],
            ['Palvelinlokit ja mittaukset', 'Palvelintilan tarjoajamme säilyttää niitä lyhyen aikaa, ja sen jälkeen ne poistetaan.'],
            ['Palvelun tilastot', 'Tekniset tapahtumat ja niiden päiväkohtaiset lukumäärät (katsokaa [Palvelun tilastot ja hallintalokimme](#operations)): poistetaan automaattisesti 12 kuukauden kuluttua.'],
            ['Palautetekstit', 'Palauteruudun vapaaehtoiset tekstit (katsokaa [Palvelun tilastot ja hallintalokimme](#operations)): poistetaan automaattisesti 90 päivän kuluttua, tai me poistamme ne aikaisemmin. Itse vastaukset ovat vain koodeja ja osa teknisiä tapahtumia, ja niitä säilytetään edellä kuvatulla tavalla.'],
            ['Hallintaloki', 'Mitä teimme tilaukselle hallintapaneelissamme: poistetaan automaattisesti 24 kuukauden kuluttua; tilausta koskevat merkinnät säilyvät sen tilaustietueen yhteydessä.'],
            ['Epäonnistuneet kirjautumiset hallintapaneeliimme', 'Salaisella avaimella tehty tiiviste IP-osoitteesta, poistetaan automaattisesti 2 päivän kuluttua.'],
            ['Ilmaiset esikatselut yhteyttä kohden', 'Salaisella avaimella tehty tiiviste IP-osoitteesta ja päivästä, poistetaan automaattisesti 2 päivän kuluttua.'],
            ['Metan evästeet ja ilmoitukset', '”_fbp” ja ”_fbc” selaimessanne: 90 päivää viimeisestä käynnistänne, ellette poista niitä aiemmin; ”snapeyes.fbc”: kunnes suljette välilehden. Maksun mukana välitetyt evästearvot, IP-osoite ja selaimen tunniste: Stripen maksutietueessa. Kuinka kauan Meta säilyttää ilmoituksensa, päättää Meta (katsokaa sen tietosuojakäytäntö).'],
            ['Sähköpostit', 'Niin kauan kuin tarvitsemme niitä pyyntöänne ja sen jatkokäsittelyä varten.'],
          ],
        },
      ],
    },
    {
      id: 'rights',
      title: 'Oikeutenne',
      blocks: [
        'Teillä on milloin tahansa nämä oikeudet:',
        {
          ul: [
            'Pääsy tietoihin: saada tietää, mitä tietoja meillä on teistä, ja saada niistä kopio (tietosuoja-asetuksen 15 artikla).',
            'Oikaiseminen: saada virheelliset tiedot korjatuiksi (tietosuoja-asetuksen 16 artikla).',
            'Poistaminen: saada tietonne poistetuiksi, esimerkiksi tilauksenne tiedostot ennen 12 kuukauden päättymistä (tietosuoja-asetuksen 17 artikla).',
            'Käsittelyn rajoittaminen: saada käsittelyä rajoitetuksi siksi aikaa, kun jotakin kysymystä selvitetään (tietosuoja-asetuksen 18 artikla).',
            'Tietojen siirrettävyys: saada meille antamanne tiedot yleisesti käytetyssä, koneellisesti luettavassa muodossa (tietosuoja-asetuksen 20 artikla).',
            'Vastustaminen: vastustaa milloin tahansa henkilökohtaiseen erityiseen tilanteeseenne liittyvällä perusteella käsittelyä, joka perustuu oikeutettuihin etuihimme (tietosuoja-asetuksen 21 artikla).',
          ],
        },
        `Käyttääksenne mitä tahansa näistä oikeuksista kirjoittakaa osoitteeseen ${MAIL}. Vastaamme kuukauden kuluessa.`,
        'Teillä on myös oikeus tehdä valitus valvontaviranomaiselle. Meidän valvontaviranomaisemme on Liettuan valtion tietosuojatarkastusvirasto (Valstybinė duomenų apsaugos inspekcija, VDAI) Vilnassa, [vdai.lrv.lt](https://vdai.lrv.lt). Voitte kääntyä myös sen EU-maan viranomaisen puoleen, jossa asutte tai työskentelette; Suomessa se on Tietosuojavaltuutetun toimisto (tietosuoja.fi).',
      ],
    },
    {
      id: 'storage',
      title: 'Evästeet ja paikallinen tallennustila',
      blocks: [
        'Omat sivumme eivät aseta evästeitä. Meta-pikseli asettaa kaksi Metan evästettä, ”_fbp” ja ”_fbc”, ja sivumme voi säilyttää avaimen ”snapeyes.fbc”: katsokaa [Meta-pikseli ja mainoksemme](#meta). Sen lisäksi sivusto ei käytä muiden yritysten analytiikka-, mainonta- tai seurantatyökaluja.',
        'Kun valitsette kielen kielivalitsimella, selaimenne muistaa valinnan paikallisessa tallennustilassaan (local storage) avaimella ”snapeyes.lang” (arvo on kielikoodi, esimerkiksi ”fi”). Sitä ei koskaan lähetetä meille, ja voitte poistaa sen milloin tahansa selaimenne asetuksista. Se on ehdottoman välttämätön pyytämänne toiminnon kannalta, joten se ei edellytä suostumusta (sähköisen viestinnän tietosuojadirektiivin 5 artiklan 3 kohta).',
        'Jos tulette meille linkistä, jossa hinnat ovat toisessa valuutassa (esimerkiksi Australian dollareina), tai valitsette valuutan valuuttavalitsimellamme tai tarjouksessamme näyttää hinnat omassa valuutassanne, selaimenne muistaa myös tämän valinnan paikallisessa tallennustilassaan avaimella ”snapeyes.market” (esimerkiksi ”au”, tai ”eu”, kun olette kieltäytynyt tuosta tarjouksesta), jotta sivusto näyttää teille edelleen samat hinnat. Sivumme kuljettavat sitä linkeissään (m=au) ja lähettävät sen tilauksen mukana, jotta teiltä veloitetaan näkemänne hinnat. Voitte poistaa sen milloin tahansa selaimenne asetuksista; se on ehdottoman välttämätön pyytämänne toiminnon kannalta, joten sekään ei edellytä suostumusta (sähköisen viestinnän tietosuojadirektiivin 5 artiklan 3 kohta).',
        'Kun testaamme hintoja (vain silloin tällöin ja rajoitetun ajan), selaimenne voi säilyttää satunnaista nimetöntä kävijänumeroa paikallisessa tallennustilassaan avaimella ”snapeyes.vid”. Se luodaan vain silloin, kun katsomallenne markkinalle (valuutalle) on käynnissä hintatesti, ja se poistetaan heti, kun mikään testi ei ole käynnissä; viimeistään se korvataan uudella 90 päivän kuluttua. Se koostuu 32 satunnaisesta merkistä ja luontipäivästään: sitä ei ole johdettu teistä, siinä ei ole nimeä, sähköpostiosoitetta eikä laitetietoja, eikä sitä koskaan yhdistetä tilaukseen. Selaimenne lähettää sen palvelimellemme pyynnön otsakkeessa (ei koskaan sivun osoitteessa), kun se pyytää hintoja; sovelluksemme käyttää sitä vain selvittääkseen joka kerta samalla tavalla, minkä testin hinnastoista näette, eikä tallenna sitä: emme pidä luetteloa kävijänumeroista. Palvelin vastaa hinnastoanne koskevalla allekirjoitetulla merkinnällä, jonka selaimenne lähettää takaisin, kun siirrytte maksusivulle, jotta teiltä veloitetaan täsmälleen teille näytetyt hinnat (selaimen lähettämää hintaa tai hinnastoa ei koskaan käytetä). Tilastoja varten palvelimemme kirjaa nimettömiä hinnastokohtaisia laskentoja: että hinnasto näytettiin, että esikatselu tehtiin, että maksusivu avattiin ja että tilaus maksettiin (katsokaa [Palvelun tilastot ja hallintalokimme](#operations)); näissä laskennoissa ei ole kävijänumeroa. Selaimenne muistaa paikallisessa tallennustilassa myös, mitkä näistä laskennoista se on jo lähettänyt (”snapeyes.expseen”), ja viimeisimmän hinnastonne (”snapeyes.pricing”), jotta samat hinnat näkyvät heti. Se, minkä hinnaston näette, ei koskaan riipu asuinpaikastanne muutoin kuin valitsemanne markkinan (valuutan) osalta, ja maksamanne hinta on aina se, joka teille näytetään ennen maksamista; tilausvahvistuksenne kertoo, mitä hinnastoa sovellettiin. Käytämme näitä merkintöjä vain tähän hintatestiin, emme koskaan mainontaan emmekä koskaan seurataksemme teitä muilla verkkosivustoilla. Jos ette halua osallistua, [avatkaa tämä linkki](/?pricetest=off&lang=fi): selaimenne säilyttää silloin vain merkinnän ”snapeyes.notest”, poistaa kävijänumeron ja muut tässä mainitut merkinnät ja näyttää ja veloittaa vakiohinnat; [tästä linkistä](/?pricetest=on&lang=fi) osallistutte uudelleen. Jos selaimenne lähettää ”Global Privacy Control” -signaalin, sekin katsotaan tällaiseksi valinnaksi. Voitte myös poistaa kaikki nämä merkinnät milloin tahansa selaimenne asetuksista (saatte silloin uuden satunnaisen arvonnan). Oikeusperuste: oikeutettu etumme asettaa oikeudenmukaiset hinnat (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Voitte vastustaa käsittelyä milloin tahansa (katsokaa [Oikeutenne](#rights)).',
        'Jos tulette meille mainoksen tai kampanjakoodin sisältävän linkkimme kautta tai toiselta verkkosivustolta, selaimenne säilyttää lyhyttä koodia selaimenne välilehden istuntotallennuksessa (session storage) avaimella ”snapeyes.c”: osoitteen parametrit, jotka nimeävät mainoksen, sellaisina kuin sen tekijä ne kirjoitti (utm_source, utm_medium, utm_campaign, utm_term ja utm_content: alusta, laji, kampanja, ryhmä ja mainos; esimerkiksi ”utm_source=fb&utm_medium=mainos&utm_campaign=kevat”), tai jos niitä ei ole, vain sen verkkosivuston lajin, jolta tulitte (esimerkiksi ”ref=facebook”: Facebook, Instagram, TikTok, Google, suora käynti tai muu sivusto). Istuntotallennus kuuluu vain kyseiselle välilehdelle ja poistuu, kun suljette sen. Koodi on sama kaikille, jotka seurasivat samaa mainosta: sitä ei ole johdettu teistä, eikä siinä ole nimeä, sähköpostiosoitetta, laitetietoja eikä napsautusnumeroa (osoitteessa oleva ”fbclid”-napsautusnumero ei koskaan ole osa sitä; mitä tuolle numerolle tapahtuu, kuvataan kohdassa [Meta-pikseli ja mainoksemme](#meta)). Sivumme lähettävät sen nimettömien sivulaskentojensa ja pyyntöjensä mukana (kuvan tarkistus, esikatselu, maksusivu); tilaustietue säilyttää sen, ja Stripen maksusivu saa sen maksun metatiedoissa, jotta näemme, mikä mainos johti mihinkin vaiheeseen ja tilaukseen (katsokaa [Palvelun tilastot ja hallintalokimme](#operations) ja [Kun tilaatte](#orders)). Käytämme sitä vain tähän, emme koskaan mainontaan, profilointiin emmekä seurataksemme teitä muilla verkkosivustoilla. Ette tarvitse sitä sivuston käyttämiseen: jos poistatte sen tai selaimenne estää istuntotallennuksen, kaikki toimii samoin ja vain tuo laskenta jää puuttumaan. Oikeusperuste: oikeutettu etumme tietää, toimiiko oma mainontamme (tietosuoja-asetuksen 6 artiklan 1 kohdan f alakohta). Voitte vastustaa käsittelyä milloin tahansa (katsokaa [Oikeutenne](#rights)).',
        'Kun tilaatte, sivu säilyttää selaimenne välilehden istuntotallennuksessa lisäksi kaksi merkintää. Istuntotallennus kuuluu vain kyseiselle välilehdelle ja poistuu, kun suljette sen:',
        {
          ul: [
            '”snapeyes.order”: kokoamanne tilauksen numero ja sen yksityinen avain, jotta sivu voi jatkaa tilaustanne, esimerkiksi kun palaatte maksusivulta. Se poistetaan, kun maksetun tilauksenne sivu avautuu kyseisessä välilehdessä, ja korvataan, kun aloitatte uuden tilauksen.',
            '”snapeyes.checkout”: vain sen ajan, kun olette maksusivulla, taideteoksenne sellaisena kuin jätitte sen (iiristen rajaukset valokuvistanne, esikatselut, muutama niistä mitattu luku, tyyli ja sen ilme, asettelu, silmien järjestys sekä mahdolliset nimet ja päivämäärä), jotta se näkyy jälleen, kun palaatte maksusivulta. Se poistetaan heti, kun palaatte, tai kun maksetun tilauksenne sivu avautuu kyseisessä välilehdessä.',
          ],
        },
        'Sivu käyttää niitä vain tilaustanne varten, ja ne ovat sen kannalta ehdottoman välttämättömiä, joten nekään eivät edellytä suostumusta (sähköisen viestinnän tietosuojadirektiivin 5 artiklan 3 kohta).',
        'Kun maksatte, Stripen maksusivu voi käyttää omia evästeitään, joita tarvitaan turvalliseen maksamiseen ja petosten torjuntaan; siellä sovelletaan Stripen omaa tietosuoja- ja evästekäytäntöä.',
      ],
    },
    {
      id: 'required',
      title: 'Onko teidän annettava meille tietoja?',
      blocks: ['Ei. Ilman valokuvaa emme kuitenkaan voi tehdä esikatselua, emmekä ilman sähköpostiosoitetta ja maksua voi toimittaa tilausta.'],
    },
    {
      id: 'changes',
      title: 'Tämän selosteen muutokset',
      blocks: ['Päivitämme tätä selostetta, kun palvelumme tai laki muuttuu. Sivun yläosassa oleva päivämäärä kertoo voimassa olevan version.'],
    },
  ],
};
