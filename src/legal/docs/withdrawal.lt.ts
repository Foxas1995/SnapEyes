// Teisė atsisakyti sutarties: the Lithuanian twin of `en` in src/legal/docs/withdrawal.ts, same section
// ids and blocks in the same order. Every rule of the English header (when the right ends, as api/_lib/withdraw.py
// decides it; the online function; the receipts and their limits) holds here word for word in meaning.
//
// The statutory parts are the Lithuanian models, kept word for word:
//  - "right" and "effects": Pavyzdinė informacijos apie nuotolinės sutarties ar ne prekybos patalpose sudarytos
//    sutarties atsisakymą forma, approved by teisingumo ministro 2014-04-30 įsakymas Nr. 1R-154 in the wording of
//    įsakymas Nr. 1R-357 of 2021-10-22 (in force since 2022-05-28), the form CK 6.228(10) straipsnio 6 dalies 1 punktas
//    refers to. Its gaps are filled as its own instructions say: [1] "sudaryta sutartis" (instruction [1] a: digital
//    content not supplied on a tangible medium), [2] the seller's details in brackets (contactLineLt: name, address,
//    email, and the phone once the owner shows one; the owner decided to show none, PHONE_OMITTED_BY_OWNER).
//  - [3], the online function: the Lithuanian text of instruction 3 of Annex I(A) Directive 2011/83/EU as replaced by
//    Annex I of Directive (EU) 2023/2673 (OJ L, 2023/2673, 28.11.2023, Lithuanian edition, checked 2026-09-29 against
//    the Publications Office's Formex file), word for word, with the address and the button inserted where the model
//    says "[įrašyti interneto adresą ar kitą tinkamą paaiškinimą, kur galima pasinaudoti sutarties atsisakymo
//    funkcija]". The national form of 2021 still carries only the older sentence for an optional web form; we are
//    obliged to offer the function (CK 6.228(10) straipsnio 11-15 dalys, law Nr. XV-269), so the newer model sentence
//    is the right one. Go-live gate: check e-tar.lt for an amended 1R-154 (the Justice Ministry announced one for the online function) and put its wording in place of this sentence if there is one.
//  - "form": Pavyzdinė nuotolinės sutarties ar ne prekybos patalpose sudarytos sutarties atsisakymo forma (1R-154, same
//    wording), with only its own alternatives and its "Kam" line filled with formLineLt. One typographic change: the
//    model joins "pirkimo" and "pardavimo" with an en dash; here it is a hyphen (owner rule: no en or em dashes anywhere).
// Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { CONTACT_EMAIL, contactLine, formLine } from '../facts';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE, withdrawFunctionAddress, withdrawFunctionHref } from '../../shared/legal';

const formLineLt = formLine('lt');
const contactLineLt = contactLine('lt');
const WITHDRAWAL_ONLINE_LT = WITHDRAWAL_ONLINE.lt;
const CHECKOUT_LEGAL_LT = CHECKOUT_LEGAL.lt;
const withdrawFunctionHrefLt = () => withdrawFunctionHref('lt');
const withdrawFunctionAddressLt = () => withdrawFunctionAddress('lt');

const W = WITHDRAWAL_ONLINE_LT;

export const lt: LegalDoc = {
  title: 'Teisė atsisakyti sutarties',
  description:
    'Informacija apie teisę atsisakyti sutarties dėl SnapEyes skaitmeninio kūrinio: 14 dienų teisė atsisakyti sutarties, kada ji baigiasi anksčiau, ir pavyzdinė sutarties atsisakymo forma.',
  lead:
    'ES vartotojai, pirkdami internetu, turi teisę atsisakyti sutarties. Kai perkamas skaitmeninis failas, toks kaip mūsų, ši teisė baigiasi anksčiau: kai tik, Jums sutikus, pradedame kurti Jūsų failą. Čia pateikiame visą informaciją.',
  sections: [
    {
      id: 'right',
      title: 'Teisė atsisakyti sutarties',
      blocks: [
        'Jūs turite teisę atsisakyti šios sutarties per 14 dienų nenurodydamas jokios priežasties.',
        'Sutarties atsisakymo laikotarpis baigsis praėjus 14 dienų nuo dienos, kurią sudaryta sutartis.',
        `Norėdamas pasinaudoti teise atsisakyti šios sutarties Jūs turite mums (${contactLineLt}) pranešti apie savo sprendimą atsisakyti šios sutarties pateikdamas nedviprasmišką pareiškimą (pvz., paštu ar elektroniniu laišku). Galite pasinaudoti pridedama pavyzdine forma, bet tai nėra privaloma. Be to, galite pasinaudoti savo teise atsisakyti sutarties internetu [${withdrawFunctionAddressLt()}](${withdrawFunctionHrefLt()}) (mygtukas „${W.button}“). Jeigu pasinaudosite šia internetine funkcija, nepagrįstai nedelsdami Jums patvariojoje laikmenoje (pvz., elektroniniu paštu) išsiųsime sutarties atsisakymo gavimo patvirtinimą, įskaitant sutarties atsisakymo turinį ir jo pateikimo datą bei laiką.`,
        'Kad būtų laikomasi atsisakymo termino, pakanka, jog Jūs nusiųstumėte pranešimą apie tai, kad pasinaudojate savo teise atsisakyti šios sutarties prieš pasibaigiant atsisakymo laikotarpiui.',
      ],
    },
    {
      id: 'effects',
      title: 'Sutarties atsisakymo pasekmės',
      blocks: [
        'Jei Jūs atsisakote šios sutarties, mes nedelsdami ir bet kuriuo atveju ne vėliau kaip per 14 dienų nuo tos dienos, kai pranešėte apie savo sprendimą atsisakyti šios sutarties, grąžinsime Jums iš Jūsų gautus pinigus, įskaitant pristatymo išlaidas (išskyrus papildomas išlaidas, patirtas Jums pasirinkus ne mūsų pasiūlytą pigiausią standartinio pristatymo būdą, o kitą pristatymo būdą). Atliksime tokį grąžinimą naudodami tokį patį mokėjimo būdą, kokį Jūs naudojote atlikdamas pradinę mokėjimo operaciją, nebent Jūs aiškiai sutikote su kitu būdu; bet kuriuo atveju Jūs neturėsite mokėti jokių su tokiu grąžinimu susijusių mokesčių.',
      ],
    },
    {
      id: 'expiry',
      title: 'Kada teisė atsisakyti sutarties baigiasi anksčiau',
      blocks: [
        '**Jūsų teisė atsisakyti sutarties baigiasi anksčiau**, kai tik pradedame vykdyti sutartį, tai yra pradedame kurti Jūsų failą, jeigu (1) aiškiai iš anksto sutikote, kad sutartį pradėtume vykdyti nepasibaigus sutarties atsisakymo terminui, (2) pripažinote, kad todėl, kai tik pradėsime, neteksite teisės atsisakyti sutarties, ir (3) mes Jums tai patvirtinome patvariojoje laikmenoje (tai darome užsakymo patvirtinimo el. laiške, kuris išsiunčiamas prieš mums pradedant). Tai numatyta Lietuvos Respublikos civilinio kodekso 6.228(10) straipsnio 2 dalies 13 punkte ir Direktyvos 2011/83/ES 16 straipsnio m punkte.',
        'Prieš mokėjimą šį sutikimą duodate pažymėdami šį langelį:',
        { box: [CHECKOUT_LEGAL_LT.withdrawalConsent], label: 'Langelis užsakymo metu' },
        'Todėl praktiškai Jūsų teisė atsisakyti sutarties baigiasi tą akimirką, kai pradedame kurti Jūsų failą. Pradedame tik po to, kai išsiunčiamas užsakymo patvirtinimo el. laiškas, paprastai per minutę nuo apmokėjimo, kol Jūsų užsakymo puslapis atidarytas: mokėjimo puslapis Jus tiesiai ten nukreipia. Jei tuo metu nesate savo užsakymo puslapyje, pradedame, kai jį vėl atidarote per tame el. laiške esančią užsakymo puslapio nuorodą. Tame pačiame el. laiške esanti sutarties atsisakymo nuoroda atidaro internetinę sutarties atsisakymo funkciją Jūsų užsakymui, nieko nepradėdama. Nuo tos akimirkos, kai pradedame, Jūsų teisė atsisakyti sutarties yra pasibaigusi, net jei Jūsų failas dar kuriamas arba laukia mūsų kokybės patikros. Jei Jūsų failo dar nepradėjome kurti, Jūsų teisė atsisakyti sutarties baigiasi pasibaigus 14 dienų sutarties atsisakymo terminui: Jūsų mokėjimo diena neskaičiuojama, o jei paskutinė termino diena yra šeštadienis, sekmadienis arba oficiali šventės diena, terminas baigiasi kitos darbo dienos pabaigoje. Tai neturi įtakos Jūsų įstatymų numatytoms teisėms, jei failas turi trūkumų: žr. mūsų pardavimo sąlygų skyrių [Pretenzijos ir trūkumai](doc:terms#defects).',
      ],
    },
    {
      id: 'online',
      title: 'Sutarties atsisakymas internetu',
      blocks: [
        `Kol turite teisę atsisakyti sutarties, bet kada galite tai padaryti internetu, funkcija [„${W.button}“](${withdrawFunctionHrefLt()}). Ją rasite mūsų pagrindinio puslapio ir teisinės informacijos puslapių apačioje, savo užsakymo puslapyje ir per sutarties atsisakymo nuorodą užsakymo patvirtinimo el. laiške. Ta nuoroda atidaro funkciją Jūsų užsakymui, nieko nepradėdama. O pats užsakymo puslapio atidarymas pradeda kurti Jūsų failą, kai tik išsiunčiamas užsakymo patvirtinimo el. laiškas, ir tada Jūsų teisė atsisakyti sutarties baigiasi (žr. [Kada teisė atsisakyti sutarties baigiasi anksčiau](#expiry)).`,
        `Kaip tai veikia: įveskite savo vardą ir pavardę, užsakymo numerį (jis jau įrašytas, jei atėjote iš savo užsakymo puslapio ar per sutarties atsisakymo nuorodą) ir el. pašto adresą gavimo patvirtinimui, tada išsiųskite pareiškimą mygtuku „${W.confirm}“. Jei atėjote be šių nuorodų, įveskite el. pašto adresą, kurį nurodėte mokėdami, kad galėtume rasti Jūsų užsakymą. Jei duomenys neatitinka nė vieno mūsų užsakymo, puslapis apie tai praneša; Jūsų pareiškimą vis tiek išsaugome, patikriname rankiniu būdu ir el. paštu atsiunčiame Jums gavimo patvirtinimą. Kad būtų išvengta piktnaudžiavimo mūsų el. laiškais, gavimo patvirtinimų skaičius ribojamas: pareiškimams, neatitinkantiems nė vieno mūsų užsakymo, iki dviejų per dieną ir keturių per mėnesį tuo pačiu adresu; vienam užsakymui iš viso iki trijų kitais adresais nei tas, kurį nurodėte apmokėjimo metu (tolesni siunčiami adresu, kurį nurodėte apmokėjimo metu); o pakartotiniam pareiškimui dėl užsakymo, į kurį jau atsakėme, iki vieno per dieną tam užsakymui ir penkių per dieną visiems užsakymams kartu. Jei puslapis negali priimti Jūsų pareiškimo, pavyzdžiui, dėl techninio gedimo arba todėl, kad gaunama neįprastai daug pareiškimų, jis apie tai praneša: tada atsiųskite mums pareiškimą el. paštu; el. laiškas galioja lygiai taip pat.`,
        'Kas vyksta toliau: Jūsų pareiškimą užregistruojame su data ir laiku, kada jis mus pasiekė. Jei Jūsų užsakymas apmokėtas, Jūsų failo dar nepradėjome kurti ir 14 dienų sutarties atsisakymo terminas nepasibaigęs, Jūsų sutarties atsisakymas įsigalioja: sustabdome Jūsų užsakymą, todėl nieko nekuriama, ir grąžiname pinigus, kaip aprašyta skyriuje [Sutarties atsisakymo pasekmės](#effects). Jei atsisakant sutarties Jūsų mokėjimas dar buvo apdorojamas, taip pat nieko nekuriama, o jei mokėjimas mus pasiekia, grąžiname visą sumą. Nedelsdami el. paštu atsiunčiame Jums gavimo patvirtinimą su Jūsų sutarties atsisakymo turiniu, data ir laiku.',
        'Jei Jums sutikus jau buvome pradėję kurti Jūsų failą arba 14 dienų sutarties atsisakymo terminas buvo pasibaigęs, Jūsų teisė atsisakyti sutarties jau buvo pasibaigusi (žr. [Kada teisė atsisakyti sutarties baigiasi anksčiau](#expiry)): puslapis ir gavimo patvirtinimas Jums tai praneša, o Jūsų pareiškimą vis tiek peržiūrime asmeniškai. Jei Jūsų užsakymas niekada nebuvo apmokėtas, nėra sutarties, kurios būtų galima atsisakyti: puslapis apie tai praneša ir pinigai nenuskaityti. Tai neturi įtakos Jūsų teisėms, jei failas turi trūkumų.',
      ],
    },
    {
      id: 'form',
      title: 'Pavyzdinė sutarties atsisakymo forma',
      blocks: [
        '(Šią formą užpildykite ir grąžinkite tik tuo atveju, jei norite atsisakyti sutarties)',
        {
          box: [
            `Kam: ${formLineLt}`,
            'Aš / Mes* pranešu (-ame), kad atsisakau (-ome) pirkimo-pardavimo sutarties dėl šių prekių* / šių paslaugų teikimo sutarties*:',
            'Užsakytų* / gautų* [data]:',
            'Vartotojo (-ų) vardas, pavardė:',
            'Vartotojo (-ų) adresas:',
            'Vartotojo (-ų) parašas (-ai) (tik jei ši forma pateikiama popierine forma):',
            'Data:',
            '(*) Išbraukti, kas nereikalinga.',
          ],
        },
        `El. paštu tiesiog atsiųskite užpildytą formą arba savo pareiškimą adresu [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Sutarties%20atsisakymas). Jei žinote užsakymo numerį, jį nurodykite. Internetu naudokitės aukščiau aprašyta funkcija [„${W.button}“](${withdrawFunctionHrefLt()}).`,
      ],
    },
  ],
};
