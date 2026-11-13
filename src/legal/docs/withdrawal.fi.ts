// Peruuttamisoikeus: the Finnish twin of `en` in src/legal/docs/withdrawal.ts, same section ids and blocks in the same
// order (the model form's box has the eight lines of the English one). Every rule of the English header (when the right
// ends, as api/_lib/withdraw.py decides it; the online function; the receipts and their limits) holds here word for word
// in meaning.
//
// The statutory parts are the official Finnish text of Annex I of Directive 2011/83/EU as amended by Directives (EU)
// 2019/2161 and 2023/2673 (the consolidated Finnish version, checked 2026-11-13), kept word for word, with its formal
// "te" (the Finnish model addresses one reader as "te": "olette valinnut"); our own sentences use the same "te":
//  - "right": Annex I(A) "Peruuttamisoikeus", the period sentence with option (a) of instruction 1 ("sopimuksen
//    tekemisestä.": digital content not supplied on a tangible medium), and the sentence on how to withdraw, with the
//    seller's details inserted after "meille" as instruction 2 asks (contactLineFi: name, address, email, and the phone
//    once the owner shows one; the owner decided to show none, PHONE_OMITTED_BY_OWNER). Then instruction 3's sentence for
//    an obligatory online function, with the address and the button inserted where it says "[lisätään internet-osoite
//    ...]". The last paragraph is the model's deadline sentence.
//  - "effects": Annex I(A) "Peruuttamisen vaikutukset", unchanged. Delivery costs do not exist here, but the clause
//    stays: it is the unchanged model.
//  - "form": Annex I(B) "Malliperuuttamislomake", word for word, its "Vastaanottaja" line filled with formLineFi. The
//    model marks its alternatives with a footnote ("Tarpeeton yliviivataan."); here the footnote is the "(*)" of the
//    English text, on the same alternatives.
// The model says "peruuttamisen määräaika" for the withdrawal period; our own sentences say "peruuttamisaika", the word
// of kuluttajansuojalaki (38/1978) 6 luku, which the checkbox and the emails use too. The online function's labels are
// the Directive's (Art. 11a(1) and (3): "Peruuta sopimus tästä", "Vahvista peruuttaminen"), held in src/shared/legal.ts
// WITHDRAWAL_ONLINE.fi; the acknowledgement of receipt is "vastaanottoilmoitus" (Art. 11a(4)). The early end for digital
// content is Art. 16(m) of the Directive (Finland transposes it in kuluttajansuojalaki 6 luku; the text names the EU act
// only, as the English one does).
// Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { CONTACT_EMAIL, contactLine, formLine } from '../facts';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE, withdrawFunctionAddress, withdrawFunctionHref } from '../../shared/legal';

const formLineFi = formLine('fi');
const contactLineFi = contactLine('fi');
const WITHDRAWAL_ONLINE_FI = WITHDRAWAL_ONLINE.fi;
const CHECKOUT_LEGAL_FI = CHECKOUT_LEGAL.fi;
const withdrawFunctionHrefFi = () => withdrawFunctionHref('fi');
const withdrawFunctionAddressFi = () => withdrawFunctionAddress('fi');

const W = WITHDRAWAL_ONLINE_FI;

export const fi: LegalDoc = {
  title: 'Peruuttamisoikeus',
  description:
    'Tiedot SnapEyesin digitaalisten tiedostojen peruuttamisoikeudesta: 14 päivän peruuttamisoikeus, milloin se päättyy aikaisemmin, ja malliperuuttamislomake.',
  lead:
    'EU:n kuluttajilla on peruuttamisoikeus verkossa tehdyissä ostoksissa. Meidän tiedostomme kaltaisessa digitaalisessa tiedostossa se päättyy aikaisemmin, kun alamme suostumuksellanne tehdä tiedostoanne. Tässä ovat kaikki tiedot.',
  sections: [
    {
      id: 'right',
      title: 'Peruuttamisoikeus',
      blocks: [
        'Teillä on oikeus peruuttaa tämä sopimus 14 päivän kuluessa syytä ilmoittamatta.',
        'Peruuttamisen määräaika päättyy 14 päivän kuluttua sopimuksen tekemisestä.',
        `Peruuttamisoikeuden käyttämiseksi teidän on ilmoitettava meille (${contactLineFi}) päätöksestänne peruuttaa sopimus yksiselitteisellä ilmoituksella (esimerkiksi kirjeellä postitse tai sähköpostilla). Voitte käyttää liitteenä olevaa malliperuuttamislomaketta, mutta mallilomakkeen käyttö ei ole pakollista. Voitte käyttää peruuttamisoikeuttanne myös verkossa osoitteessa [${withdrawFunctionAddressFi()}](${withdrawFunctionHrefFi()}) (painike ”${W.button}”). Jos käytätte tätä verkkotoimintoa, lähetämme teille ilman aiheetonta viivytystä pysyvällä välineellä (esim. sähköpostitse) peruuttamisen vastaanottamista koskevan ilmoituksen, jossa mainitaan peruutuksen sisältö ja sen toimituspäivä ja -aika.`,
        'Peruuttamisen määräajan noudattamiseksi riittää, että lähetätte ilmoituksenne peruuttamisoikeuden käytöstä ennen peruuttamisen määräajan päättymistä.',
      ],
    },
    {
      id: 'effects',
      title: 'Peruuttamisen vaikutukset',
      blocks: [
        'Jos peruutatte tämän sopimuksen, palautamme teille kaikki teiltä saamamme maksut, myös toimituskustannukset (paitsi lisäkustannuksia siitä, että olette valinnut tarjoamastamme edullisimmasta vakiotoimitustavasta poikkeavan toimitustavan), ilman aiheetonta viivytystä ja joka tapauksessa viimeistään 14 päivän kuluttua päivästä, jona saamme tietää päätöksestänne peruuttaa sopimus. Suoritamme palautuksen sillä maksuvälineellä, jota olette käyttänyt alkuperäisessä liiketoimessa, ellette ole nimenomaisesti suostunut muuhun, ja joka tapauksessa siten, että teille ei aiheudu palautuksesta kustannuksia.',
      ],
    },
    {
      id: 'expiry',
      title: 'Milloin peruuttamisoikeus päättyy aikaisemmin',
      blocks: [
        '**Peruuttamisoikeutenne päättyy aikaisemmin**, kun olemme aloittaneet sopimuksen täyttämisen eli alkaneet tehdä tiedostoanne, jos (1) olette antanut nimenomaisen suostumuksenne siihen, että aloitamme sopimuksen täyttämisen ennen peruuttamisajan päättymistä, (2) olette ilmoittanut tietävänne, että menetätte näin peruuttamisoikeutenne, kun olemme aloittaneet, ja (3) olemme vahvistaneet tämän teille pysyvällä välineellä (teemme sen tilausvahvistuksessa, joka lähtee sähköpostitse ennen kuin aloitamme). Tämä perustuu direktiivin 2011/83/EU 16 artiklan m alakohtaan.',
        'Ennen maksamista annatte tämän suostumuksen rastittamalla tämän ruudun:',
        { box: [CHECKOUT_LEGAL_FI.withdrawalConsent], label: 'Tilausvaiheen valintaruutu' },
        'Käytännössä peruuttamisoikeutenne päättyy siis sillä hetkellä, kun alamme tehdä tiedostoanne. Aloitamme vasta, kun tilausvahvistus on lähtenyt sähköpostiinne, yleensä minuutin kuluessa maksustanne, kun tilaussivunne on auki: maksusivu vie teidät suoraan sinne. Jos ette ole silloin tilaussivullanne, aloitamme, kun avaatte sen uudelleen kyseisessä sähköpostissa olevalla tilaussivun linkillä. Saman sähköpostin peruutuslinkki avaa tilauksenne verkossa toimivan peruuttamistoiminnon käynnistämättä mitään. Siitä hetkestä, kun aloitamme, peruuttamisoikeutenne on päättynyt, vaikka tiedostoanne vielä tehtäisiin tai se odottaisi laaduntarkastustamme. Jos emme ole alkaneet tehdä tiedostoanne, peruuttamisoikeutenne päättyy, kun 14 päivän peruuttamisaika on kulunut: maksupäiväänne ei lasketa mukaan, ja jos ajan viimeinen päivä on lauantai, sunnuntai tai yleinen vapaapäivä, aika päättyy seuraavan työpäivän päättyessä. Tämä ei vaikuta lakisääteisiin oikeuksiinne, jos tiedostossa on virhe: katsokaa myyntiehtojemme kohta [Reklamaatiot ja virheet](doc:terms#defects).',
      ],
    },
    {
      id: 'online',
      title: 'Peruuttaminen verkossa',
      blocks: [
        `Niin kauan kuin peruuttamisoikeutenne on voimassa, voitte peruuttaa sopimuksen verkossa milloin tahansa toiminnolla [”${W.button}”](${withdrawFunctionHrefFi()}). Löydätte sen etusivumme ja oikeudellisten sivujemme alaosasta, tilaussivultanne ja tilausvahvistuksenne peruutuslinkin takaa. Tuo linkki avaa toiminnon tilaustanne varten käynnistämättä mitään. Tilaussivunne avaaminen sen sijaan käynnistää tiedostonne tekemisen, kun tilausvahvistus on lähtenyt sähköpostiinne, ja se päättää peruuttamisoikeutenne (katsokaa [Milloin peruuttamisoikeus päättyy aikaisemmin](#expiry)).`,
        `Näin se toimii: kirjoittakaa nimenne, tilausnumeronne (se on valmiiksi täytetty, kun tulette tilaussivultanne tai peruutuslinkin kautta) ja sähköpostiosoite vastaanottoilmoitusta varten ja lähettäkää sitten peruuttamisilmoituksenne painikkeella ”${W.confirm}”. Jos tulette ilman kumpaakaan näistä linkeistä, antakaa sähköpostiosoite, jolla maksoitte, jotta voimme yhdistää ilmoituksen tilaukseenne. Jos tiedot eivät vastaa yhtäkään tilaustamme, sivu kertoo sen teille; säilytämme ilmoituksenne silti, tarkistamme sen käsin ja lähetämme teille sähköpostitse vastaanottoilmoituksen. Sähköpostiemme väärinkäytön estämiseksi vastaanottoilmoitusten määrää on rajoitettu: ilmoituksista, jotka eivät vastaa yhtäkään tilaustamme, niitä lähetetään samaan osoitteeseen enintään kaksi päivässä ja neljä kuukaudessa; yhdestä tilauksesta yhteensä enintään kolme muihin osoitteisiin kuin siihen, jolla tilaus maksettiin (seuraavat lähetetään osoitteeseen, jolla maksoitte); ja toistuvasta ilmoituksesta, joka koskee tilausta, johon olemme jo vastanneet, enintään yksi päivässä kyseisestä tilauksesta ja viisi päivässä kaikista tilauksista yhteensä. Jos sivu ei voi ottaa ilmoitustanne vastaan, esimerkiksi teknisen vian vuoksi tai siksi, että ilmoituksia saapuu poikkeuksellisen paljon, se kertoo sen teille: lähettäkää silloin peruuttamisilmoituksenne meille sähköpostitse; sähköposti on yhtä pätevä.`,
        'Mitä sitten tapahtuu: kirjaamme ilmoituksenne sekä päivämäärän ja kellonajan, jolloin se saapui meille. Jos tilauksenne on maksettu, emme ole alkaneet tehdä tiedostoanne eikä 14 päivän peruuttamisaika ole kulunut, peruutuksenne tulee voimaan: pysäytämme tilauksenne, jolloin mitään ei tehdä, ja palautamme maksunne kohdassa [Peruuttamisen vaikutukset](#effects) kuvatulla tavalla. Jos maksuanne käsiteltiin vielä, kun peruutitte sopimuksen, mitään ei myöskään tehdä, ja jos maksu saapuu meille, palautamme sen kokonaan. Lähetämme teille viipymättä sähköpostitse vastaanottoilmoituksen, jossa on peruutuksenne sisältö sekä sen päivämäärä ja kellonaika.',
        'Jos olimme suostumuksellanne jo alkaneet tehdä tiedostoanne tai 14 päivän peruuttamisaika oli kulunut, peruuttamisoikeutenne oli jo päättynyt (katsokaa [Milloin peruuttamisoikeus päättyy aikaisemmin](#expiry)): sivu ja vastaanottoilmoitus kertovat sen teille, ja katsomme ilmoituksenne silti henkilökohtaisesti. Jos tilaustanne ei koskaan maksettu, peruutettavaa sopimusta ei ole: sivu kertoo sen teille, eikä mitään veloitettu. Tämä ei vaikuta oikeuksiinne, jos tiedostossa on virhe.',
      ],
    },
    {
      id: 'form',
      title: 'Malliperuuttamislomake',
      blocks: [
        '(Täyttäkää ja palauttakaa tämä lomake vain siinä tapauksessa, että haluatte peruuttaa sopimuksen.)',
        {
          box: [
            `Vastaanottaja: ${formLineFi}`,
            'Ilmoitan/Ilmoitamme (*), että haluan/haluamme (*) peruuttaa tekemäni/tekemämme (*) sopimuksen, joka koskee seuraavien tavaroiden toimittamista (*) / seuraavan palvelun suorittamista (*):',
            'Tilauspäivä (*) / Vastaanottopäivä (*):',
            'Kuluttajan nimi / Kuluttajien nimet:',
            'Kuluttajan osoite / Kuluttajien osoitteet:',
            'Kuluttajan allekirjoitus / Kuluttajien allekirjoitukset (vain jos lomake täytetään paperimuodossa):',
            'Päiväys:',
            '(*) Tarpeeton yliviivataan.',
          ],
        },
        `Sähköpostitse voitte lähettää täytetyn lomakkeen tai oman ilmoituksenne osoitteeseen [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Sopimuksen%20peruuttaminen). Lisätkää tilausnumeronne, jos teillä on se. Verkossa voitte käyttää edellä kuvattua toimintoa [”${W.button}”](${withdrawFunctionHrefFi()}).`,
      ],
    },
  ],
};
