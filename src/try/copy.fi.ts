// Finnish ("fi") copy for /try: every key of src/try/copy.ts `en`, in the same structure. Informal singular "sinä"
// (the plural "te" only where two people are addressed), as Finnish consumer shops write, and the landing page's words
// (src/landing/copy/fi.json): takakamera, etukamera, 2x-zoomi, otos (shot), kuva (photo), esikatselu, taideteos,
// entisöidä (restore), säikeet (fibres), tekoäly (only where English says AI), näyte (the AI sample). Decimal comma (3,7).
// Finnish grammar the English helpers do not need (src/shared/fi.ts):
//  - a noun after a number is singular: 1 silmä, 2 silmää; 1 otos, 3 otosta (fiForm()); as the object of a statement
//    "1 otoksen", "3 otosta" (the "Acc" helpers);
//  - in the other cases one form serves every number, so those are written by hand: "tilaa vielä 3 silmälle";
//  - "Eye 3" and "shot 2" are "silmä 3" and "otos 2", and a list of them shares one noun: "Silmät 1 ja 3".
// The server's own sentences (quality.message, tips) come from api/analyze.py in the request's language
// (api/_lib/analyze_fi.py TEXT_FI, the twin of TEXT_HR).
// The buy button is "Siirry maksamaan" with the price, as in English ("Continue to payment"): it only opens Stripe's
// page and places no order. The click that binds is Stripe's pay button, so "next" below and api/_lib/pay_fi.py
// SUBMIT_NOTE_FI (right above that button) carry the words of Art. 8(2) Directive 2011/83/EU in its official Finnish
// text, "tilaukseen liittyy maksuvelvollisuus".
import type { BlockCopy, BlockReason, TryCopy } from './copy';
import type { LightAnswer } from './multi';
import { CONTACT_EMAIL } from '../landing/config';
import { CHECKOUT_LEGAL } from '../shared/legal';
import { TRANSPARENCY_FI } from '../landing/copy.fi';
import { dec1Fi, fiForm, kirjaimet, kuvatAcc, merkit, otoksetAcc, silmat } from '../shared/fi';

/** "1", "1 ja 3", "1, 2 ja 4": numbers in a list; the noun stands once in front ("Silmät 1 ja 3"). */
const andList = (xs: number[]) => (xs.length < 2 ? String(xs[0] ?? '') : `${xs.slice(0, -1).join(', ')} ja ${xs[xs.length - 1]}`);

// the capture guide's steps, word for word the same on the capture screen and in the retake cards (src/try/copy.ts)
const LIGHT = 'Päivänvalo ikkunasta tai taskulamppu, sivulta. Ei huoneen lamppua, ei salamaa.';
const CAMERA = 'Takakamera ja 2x-zoomi, noin 10 cm silmästä.';
const FOCUS = 'Napauta iiristä näytöllä, niin kamera tarkentaa siihen.';
const STEADY = 'Pidä puhelin vakaana (tue kyynärpäät johonkin) ja ota 3-5 otosta.';
// the first retake step for a dark iris: the same light, only closer to the window
const DARK_LIGHT = 'Lisävalo tuo tumman iiriksen kuvion esiin: seiso päivänvalossa lähellä valoisaa ikkunaa niin, että ikkuna on sivullasi (ei suorassa auringossa), tai pyydä jotakuta pitämään taskulamppua sivulla. Ei huoneen lamppua eikä salamaa.';

export const fi: TryCopy = {
  lang: 'fi',
  meta: {
    title: 'SnapEyes Studio: iiristaidetta silmäsi kuvasta',
    description: 'Ota puhelimella kuva silmästäsi ja näe noin minuutissa oma iiriksesi entisöitynä ja valitsemassasi tyylissä.',
  },
  switchLabel: 'Kieli',
  /** One decimal, as Finnish writes it (3,7). */
  dec1: (v: number) => dec1Fi(v),

  header: {
    study: 'Perhetesti',
  },

  errors: {
    tooLarge: 'Tämä kuva on liian suuri. Yritä uudelleen tavallisella kameralla otetulla kuvalla.',
    timeout: 'Tässä kesti meillä liian kauan. Yritä uudelleen.',
    notResponding: 'Studio ei vastaa juuri nyt. Yritä hetken kuluttua uudelleen.',
    requestFailed: (status: number) => `Pyyntö epäonnistui (${status})`,
    unreadable: 'Emme saaneet tätä kuvaa auki. Jos se on iPhonen HEIC-tiedosto, tämä selain ei osaa lukea sitä: valitse JPEG- tai PNG-kuva tai avaa snapeyes.com puhelimellasi ja ota kuva siellä.',
    noEyeAny: 'Emme löytäneet silmää yhdestäkään näistä kuvista.',
    noEyeShot: 'Emme löytäneet silmää tästä otoksesta.',
    noEye: 'Silmää ei löytynyt',
    keepFailed: 'Otostesi tallentamisessa meni jokin vikaan. Ota kuva uudelleen.',
  },

  capture: {
    // the first screen's heading: the second part is set in gold
    titleA: 'SILMÄSI, ',
    titleB: 'TAITEENA.',
    lead: 'Kuvaa yksi silmä ja näe se entisöitynä noin minuutissa.',
    addTitle: (n: number) => `Lisää silmä ${n}`,
    addLead: 'Kumppanisi, lapsesi tai toinen silmäsi. Samat vaiheet kuin äsken: ota muutama otos, niin säilytämme parhaan.',
    takeTurns: 'Kuvaatteko toisianne? Vuorotelkaa: toinen pitää puhelinta, toinen katsoo suoraan eteenpäin. Vaihtakaa sitten.',
    helper: 'Helpointa kahdestaan, kyynärpäät pöydällä: toinen pitää puhelinta lähellä silmää, toinen nojaa leukansa käteen, katsoo suoraan eteenpäin ja pitää taskulamppua sivulla.',
    retakeTitle: (n: number) => `Kuvaa silmä ${n} uudelleen`,
    retakeLead: 'Samat vaiheet kuin äsken. Uusi otoksesi korvaa tämän silmän taideteoksessa; siihen asti se pysyy ennallaan.',
    back: (n: number) => `Takaisin taideteokseesi (${silmat(n)})`,
    sampleButton: 'Näytesilmä',
    sampleLoadFailed: 'Näytesilmää ei voitu ladata.',
    thumbLabel: (i: number) => `Silmä ${i}`,
    sampleThumb: 'Tekoälyn luoma näyte',
    // the guide video's button and the four steps under it, one line each (copy.ts says why)
    videoPlay: 'Toista ohjevideo',
    videoPause: 'Keskeytä ohjevideo',
    steps: ['Takakamera, 2x-zoomi', 'Noin 10 cm silmästä', 'Ikkunan tai taskulampun valo, sivulta', 'Tarkenna napauttamalla iiristä, pysy paikallasi'],
    moreTips: 'Lisää vinkkejä',
    stepsOpen: 'Silmä aivan auki. ',
    stepsOpenMore: 'Katso suoraan eteenpäin ja nosta yläluomea varovasti sormenpäällä, jotta luomi tai ripset eivät peitä iiristä.',
    stepsShots: 'Ota 3-5 otosta ja lähetä ne kaikki.',
    stepsShotsMore: ' Käänny hieman otosten välillä. Mittaamme jokaisen ja käytämme terävintä; oikeassa testissä parhaassa otoksessa oli 3,7 kertaa niin paljon yksityiskohtia kuin heikoimmassa.',
    cameraFirst: 'Kuvaa silmä puhelimesi omalla kameralla (2x, ikkunan ääressä) ja valitse kuva sitten tästä: niin siitä tulee terävin.',
    takePhoto: 'Ota kuva',
    pickShots: 'Valitse 3-5 otosta',
    consent: 'Tallenna silmäni kuva ja tulos SnapEyesin koulutusmuistiin, jotta entisöinnit paranevat ajan myötä. Nimetön, ei nimeä eikä kasvoja. Voit pyytää meitä poistamaan sen milloin tahansa.',
  },

  working: {
    finding: 'Etsimme iiristäsi…',
    locating: 'Paikannamme iiriksen ja pupillin',
    measuringSize: 'Mittaamme koon ja terävyyden',
    checking: (n: number, done: number) => `Tarkistamme kuvia: ${done}/${n} valmiina`,
    measuringShot: (k: number, max: number) => `Mittaamme otosta ${k}/${max}`,
    restoring: 'Entisöimme iiristäsi…',
    restoringEye: (n: number) => `Entisöimme silmää ${n}…`,
    cut: 'Rajaamme iiriksesi',
    reflections: 'Poistamme heijastuksia',
    macro: 'Studion makroentisöinti (noin 30 s)',
    composing: (n: number) => (n > 1 ? `Koostamme taideteostasi (${silmat(n)})` : 'Koostamme taideteostasi'),
    sampleCaption: 'Tekoälyn luoma näyte',
    yourIris: 'Iiriksesi',
    elapsed: (s: number) => `${s} s`,
  },

  quality: {
    retake: 'Ota uusi kuva',
    notCentred: 'Iiris ei ole tämän kuvan keskellä, joten sitä ei voi entisöidä. Ota kuva uudelleen niin, että yksi silmä täyttää kuvan.',
    blocks: {
      too_blurry: {
        title: 'Liian epätarkka oman iiriksesi entisöintiin',
        reason: 'Tässä kuvassa ei näy tarpeeksi oman iiriksesi kuviota, jotta voisimme entisöidä sen, joten emme käytä kuvaa.',
        error: 'Tämä kuva on liian epätarkka oman iiriksesi entisöintiin. Ota se uudelleen alla olevien vaiheiden mukaan.',
        retakeLine: 'Tämä otos on liian epätarkka oman iiriksesi entisöintiin. Ota se uudelleen päivänvalossa ikkunan luona tai taskulampun kanssa, valo sivulta, takakameralla ja 2x-zoomilla: tarkenna napauttamalla iiristä ja pidä puhelin vakaana.',
        thumb: 'epätarkka',
        steps: [LIGHT, CAMERA, FOCUS, STEADY],
      },
      too_dark: {
        title: 'Liian tumma, jotta iiriksesi oma kuvio näkyisi',
        reason: 'Iiriksesi on tumma, ja valoa oli liian vähän sen oman kuvion näkemiseen, joten emme käytä tätä kuvaa.',
        error: 'Tämä kuva on liian tumma, jotta iiriksesi oma kuvio näkyisi. Ota se uudelleen alla olevien vaiheiden mukaan.',
        retakeLine: 'Tämä otos on liian tumma, jotta iiriksesi oma kuvio näkyisi. Ota se uudelleen päivänvalossa lähellä valoisaa ikkunaa niin, että ikkuna on sivullasi, tai taskulampun kanssa sivulta. Ei huoneen lamppua eikä salamaa.',
        thumb: 'tumma',
        steps: [DARK_LIGHT, CAMERA, FOCUS, STEADY],
      },
      pupil_too_large: {
        title: 'Pupillisi on liian laaja iiriksesi entisöintiin',
        reason: 'Pupillisi on tässä kuvassa niin laaja, että iiristä näkyy sen ympärillä liian vähän, joten emme käytä kuvaa.',
        error: 'Pupillisi on tässä kuvassa liian laaja oman iiriksesi entisöintiin. Ota kuva uudelleen alla olevien vaiheiden mukaan.',
        retakeLine: 'Pupillisi on tässä otoksessa liian laaja. Lisävalo pienentää sitä: ota kuva uudelleen päivänvalossa lähellä valoisaa ikkunaa tai taskulampun kanssa sivulta, älä salamalla.',
        thumb: 'pupilli',
        steps: [
          'Lisävalo pienentää pupillia: seiso päivänvalossa lähellä valoisaa ikkunaa niin, että ikkuna on sivullasi (ei suorassa auringossa), tai pyydä jotakuta pitämään taskulamppua sivulla. Ei salamaa.',
          'Anna silmäsi olla siinä valossa minuutti ennen kuvaamista, jotta pupilli ehtii supistua. Pimeän tultua sytytä kaikki kattovalot ja pyydä jotakuta pitämään taskulamppua sivulla.',
          CAMERA,
          'Tarkenna napauttamalla iiristä näytöllä, pidä puhelin vakaana ja ota 3-5 otosta.',
        ],
      },
      too_small: {
        title: 'Iiriksesi on tässä kuvassa liian pieni',
        reason: 'Iiriksesi on tässä kuvassa niin pieni, että sen omaa kuviota näkyy liian vähän, joten emme käytä kuvaa.',
        error: 'Iiriksesi on tässä kuvassa liian pieni entisöitäväksi. Ota kuva uudelleen lähempää alla olevien vaiheiden mukaan.',
        retakeLine: 'Iiriksesi on tässä otoksessa liian pieni. Tule lähemmäs: takakamera ja 2x-zoomi, noin 10 cm silmästäsi, niin että iiris täyttää noin kolmasosan kuvasta.',
        thumb: 'pieni',
        steps: [
          'Tule lähemmäs: takakamera ja 2x-zoomi, noin 10 cm silmästä, niin että iiris täyttää noin kolmasosan kuvasta.',
          LIGHT,
          FOCUS,
          STEADY,
        ],
      },
      // a lid over part of the iris (api/analyze.py EYELID_BLOCK_PCT): the studio would have to paint iris over it. The words
      // of the capture guide's open-eye step (stepsOpen, stepsOpenMore) and of api/_lib/analyze_fi.py TEXT_FI["eyelid"]
      eyelid: {
        title: 'Silmäluomesi peittää osan iiriksestäsi',
        reason: 'Osa iiriksestäsi on tässä kuvassa piilossa silmäluomen tai ripsien takana, joten emme käytä kuvaa.',
        error: 'Silmäluomesi peittää tässä kuvassa osan iiriksestäsi. Ota kuva uudelleen alla olevien vaiheiden mukaan.',
        retakeLine: 'Silmäluomesi peittää tässä otoksessa osan iiriksestäsi. Katso suoraan linssiin, avaa silmä aivan auki ja nosta yläluomea varovasti sormenpäällä.',
        thumb: 'luomi',
        steps: [
          'Katso suoraan linssiin, älä vinosti: kun katse kääntyy sivulle, yläluomi liukuu iiriksen päälle.',
          'Avaa silmä aivan auki ja nosta yläluomea varovasti sormenpäällä, jotta iho, ripset tai ripsiväri eivät peitä iiristä.',
          CAMERA,
          'Tarkenna napauttamalla iiristä näytöllä, pidä puhelin vakaana ja ota 3-5 otosta.',
        ],
      },
    } satisfies Record<BlockReason, BlockCopy>,
    // a reason this page does not know yet: neutral on purpose, it names no cause the server did not name
    blockedOther: {
      title: 'Liian vähän yksityiskohtia oman iiriksesi entisöintiin',
      reason: 'Tässä kuvassa ei näy tarpeeksi oman iiriksesi kuviota, jotta voisimme entisöidä sen, joten emme käytä kuvaa.',
      error: 'Tässä kuvassa ei näy tarpeeksi omaa iiristäsi, jotta voisimme entisöidä sen. Ota kuva uudelleen alla olevien vaiheiden mukaan.',
      retakeLine: 'Tässä otoksessa ei näy tarpeeksi omaa iiristäsi, jotta voisimme entisöidä sen. Ota uusi otos kuvausohjeen mukaan.',
      thumb: 'uusi kuva',
      steps: [LIGHT, CAMERA, FOCUS, STEADY],
    } satisfies BlockCopy,
    guideTitle: 'Uutta kuvaa varten',
    noneUsable: (n: number) => (n === 1
      ? 'Tarkistimme kuvan, mutta sitä ei voi käyttää.'
      : n === 2
        ? 'Tarkistimme molemmat kuvat, eikä kumpaakaan voi käyttää.'
        : `Tarkistimme kaikki ${kuvatAcc(n)}, eikä yhtäkään niistä voi käyttää.`),
    shotUnusable: 'Tätä otosta ei voi käyttää. Ota uusi yllä olevien neuvojen avulla.',
    shotsUnusable: 'Yhtäkään näistä otoksista ei voi vielä käyttää. Ota uusi yllä olevien neuvojen avulla.',
    fullUnusable: (max: number) => `${max === 1 ? 'Tätä otosta' : `Yhtäkään näistä ${max} otoksesta`} ei voi käyttää. Ota uusi otos, niin aloitat uuden sarjan.`,
    detectedIris: 'Tunnistettu iiris',
    pupilNote: 'Heijastus pupillissa ei haittaa: rakennamme pupillin uudelleen puhtaana pimeytenä.',
    lampFallback: 'Lampun valo sävyttää silmänvalkuaistasi, joten värit voivat näyttää lämpimämmiltä kuin ne oikeasti ovat.',
    closer: 'Mene lähemmäs tai zoomaa, jotta iiris täyttää suuremman osan kuvasta.',
  },

  // the camera shot collector
  collector: {
    header: (n: number, max: number) => `Otos ${n}/${max}`,
    shotAlt: (n: number) => `Otos ${n}`,
    // best is printed after a colon or as a predicate ("Käytämme parasta: otos 2")
    bestLabel: (k: number, d?: number) => `otos ${k}${d !== undefined ? ` (yksityiskohdat ${d})` : ''}`,
    full: (max: number, best: string) => `Otoksia on nyt ${max}. Käytämme parasta: ${best}.`,
    more: (left: number) => `Voit ottaa vielä enintään ${otoksetAcc(left)}. Mittaamme jokaisen otoksen ja säilytämme parhaan.`,
    sharpEnough: 'Tämä otos on tarpeeksi terävä käytettäväksi.',
    bestSoFar: 'Tämä on tähän asti paras otoksesi.',
    lampSkipped: (n: number, best: string) => `Lampun valo sävytti otoksen ${n}, joten käytämme parasta oikeanväristä otostasi: ${best}.`,
    bestIs: (best: string) => `Tähän asti paras: ${best}. Käytämme sitä.`,
    lastFailed: (note: string) => `Viimeisintä otosta ei voitu käyttää: ${note} Tähän asti paras otoksesi on tallessa.`,
    takeAnother: 'Ota vielä yksi',
    useBest: 'Käytä parasta otosta',
    useThis: 'Käytä tätä otosta',
    startOver: 'Aloita alusta',
  },

  result: {
    beforeAfter: 'Ennen / jälkeen',
    eyes: 'Tämän taideteoksen silmät',
    eyeLabel: (i: number) => `Silmä ${i}`,
    sampleLabel: 'Tekoälyn luoma näyte',
    yourPhoto: 'Sinun kuvasi',
    samplePhoto: 'Tekoälyn luoma näyte',
    after: 'Studiomakro',
    sliderBefore: 'Sinun kuvasi',
    sliderAfter: 'Entisöity',
    sliderLabel: 'Vertaa kuvaasi ja entisöityä iiristä',
    sliderValue: 'kuvaa {n} prosenttia',
    // announced once, by a polite live region, when the studio has made the preview (release review, perf-a11y M3)
    previewReady: 'Esikatselusi on valmis. Valitse tyyli alta.',
    // src/landing/copy.fi.ts TRANSPARENCY_FI, word for word. Shown for a real eye only.
    transparency: TRANSPARENCY_FI,
    // src/shared/aiMaterial.ts AI_MATERIAL_PAGE.fi (the page's "sinä" wording), word for word as the landing's FAQ answer (src/landing/copy/fi.json)
    aiMaterial: 'Joissakin tyyleissä iiristäsi ympäröivä jauhe, neste, liekki tai pöly on tekoälyn tekemää materiaalia yhteisestä kirjastosta, joten toisen asiakkaan taideteoksessa voi olla sama pala. Iiriksesi säilyttää valokuvasi värit, kuvion ja asettelun; hienoimmat säikeet entisöidään tekoälyllä, kuten edellä on kuvattu.',
    sampleNote: 'Tämä silmä on tekoälyn luoma näyte, ei oikea valokuva. Kun käytät omaa kuvaasi, väri tulee siitä.',
    colourOff: 'Värit voivat poiketa hieman silmästäsi. Aidoimman värin antaa päivänvalo tai taskulamppu sivulta, ilman salamaa; jos pidät tuloksesta, jatka vain.',
    pupilWide: 'Lisävalo pienentää pupillia ja näyttää enemmän iiristäsi.',
    pupilLarge: 'Pupillisi on suuri: ikkunan ääressä se supistuu ja iiriksen kuviota näkyy enemmän.',
    how: 'Näin se toimii',
    did: {
      title: 'Mitä teimme',
      glare: 'Poistimme heijastukset.',
      sharp: 'Terävöitimme tarkennusta ja hienoja säikeitä.',
      colour: 'Tasapainotimme valon.',
      lid: 'Jatkoimme omaa iiristäsi silmäluomen peittämään kohtaan.',
      nothing: 'Emme maalanneet mitään päälle: emme uusia värejä emmekä toisen silmän kuviota.',
      quality: (crop: number) => `Puhelimesi oma kamera ottaa kuvan täydellä laadulla. Rajaamme siitä tiukan kuvan silmästäsi (enintään ${crop} px) ja entisöimme sen; täysikokoinen 4096 px:n tiedosto piirrettäisiin tästä entisöinnistä, ei venytettäisi valokuvastasi.`,
    },
    retakeEye: (i: number) => `Kuvaa silmä ${i} uudelleen`,
    retakeOnly: 'Kuvaa tämä silmä uudelleen',
    replaceSample: 'Käytä sen sijaan omaa silmääsi',
    removed: (i: number) => `Silmä ${i} poistettu.`,
    undo: 'Kumoa',
    sampleArtwork: 'Näytetaideteos',
    sampleBadge: 'Tekoälyn luoma näyte',
    // baked into the preview image itself (the engine's caption title, at most 40 characters: this is 20)
    sampleTitle: 'Tekoälyn luoma näyte',
    sampleArtworkNote: 'Tehty vain tekoälyn luomasta näytesilmästä, ei oikeasta valokuvasta.',
    mixedArtworkNote: 'Tässä taideteoksessa on tekoälyn luoma näytesilmä, joka ei ole oikea valokuva.',
    upscaled: 'Pieni kuva: suurennettu ennen entisöintiä.',
    badgeMacro: 'Studiomakro',
    badgeFallback: 'Vain uskollinen suurennos',
    artwork: 'Taideteoksesi',
    composing: 'Koostamme…',
    composeFailed: 'Emme saaneet tätä esikatselua koostettua.',
    previewReduced: 'Esikatselu on pienennetty ja vesileimattu.',
    previewFile: (square: boolean): string => (square
      ? 'Tiedostosi: 4096 px, tarpeeksi terävä tulostettavaksi kokoon 60 x 60 cm asti.'
      : 'Tiedostosi: 4096 px pisimmältä sivulta, tarpeeksi terävä tulostettavaksi niin, että se sivu on enintään 60 cm.'),
    retry: 'Yritä uudelleen',
    layout: 'Asettelu',
    style: 'Tyyli',
    save: 'Tallenna esikatselu',
    // the saved preview's file name (ASCII, as the English and German ones); a sample preview says so in its name too
    fileName: (style: string, n: number, sample: boolean) => `snapeyes-esikatselu-${style}-${n}-${fiForm(n, 'silma', 'silmaa')}${sample ? '-tekoalyn-nayte' : ''}.jpg`,
    addSecond: 'Lisää toinen silmä',
    addAnother: 'Lisää vielä silmä',
    addHint: (left: number) => `Kumppani, lapsi tai toinen silmäsi. Tässä taideteoksessa on tilaa vielä ${left} silmälle.`,
    full: (max: number) => `Silmiä on nyt ${max}, eikä yhteen taideteokseen mahdu enempää.`,
    quota: (left: number, max: number) => `Ilmaisia esikatseluja tänään jäljellä: ${left}/${max}.`,
    remove: (i: number) => `Poista silmä ${i}`,
    startOver: 'Aloita alusta',
    confirmStartOver: (n: number) => `Hylätäänkö ${n === 1 ? 'silmä' : `kaikki ${silmat(n)}`} ja aloitetaan alusta?`,
    stored: 'Tallennettu koulutusmuistiin',

    reveal: {
      photo: 'Sinun kuvasi',
      iris: 'Iiriksesi',
      slider: 'Vertaa kuvaasi entisöityyn iirikseesi',
      valueText: 'kuvaa {n} prosenttia',
      promise: 'Entisöity, ei koskaan uudelleen maalattu: emme koskaan väritä iiristäsi uudelleen emmekä vaihda sitä toiseen silmään.',
      softTip: 'Kuvasi on pieni, joten sen puolikas näyttää pehmeältä. Mene lähemmäs tai käytä 2x-zoomia, niin vertailusta tulee terävämpi.',
    },
  },

  // the style picker (src/try/picker.ts)
  picker: {
    groups: { one: 'Vain sinä', two: 'Te kaksi', family: 'Perhe' },
    groupIntro: {
      one: 'Yksi iiris, yksin mustalla tai omassa universumissaan.',
      two: 'Kumppanille: kaksi iiristä, jotka kohtaavat.',
      family: 'Perheelle: jokainen iiris säilyttää oman värinsä.',
    },
    groupSoon: 'Ilmainen esikatselu jo nyt. Tämän ryhmän tilaukset avautuvat pian.',
    countSoon: (n: number) => `Tilaukset ${n} silmälle avautuvat pian.`,
    soonBuy: 'Tämä tyyli avautuu pian. Valitse toinen, jos haluat tilata nyt.',
    retakeBuy: (total: number): string => (total === 1
      ? 'Tällä kuvalla ei voi vielä tilata mitään. Jos haluat tilata, kuvaa silmäsi uudelleen.'
      : 'Näillä kuvilla ei voi vielä tilata mitään. Jos haluat tilata, kuvaa alla olevat silmät uudelleen.'),
    soonNote: 'Tämä tyyli avautuu pian.',
    soonLookBuy: (look: string) => `Ilme ${look} avautuu pian. Valitse toinen ilme tai tyyli, jos haluat tilata nyt.`,
    soonLookNote: (look: string) => `Ilme ${look} avautuu pian.`,
    listLabel: 'Tyylit silmillesi',
    soon: 'Pian',
    recommended: 'Suositeltu',
    reasons: {
      'reason.solo_powder.own': 'Omat värisi, jauheeksi muuttuneina',
      'reason.solo_gold.dark_brown': 'Kulta saa tummanruskeat silmät hehkumaan',
      'reason.solo_radiance.grey': 'Hopeista valoa harmaille silmille',
      'reason.duo_collision_infinity.own': 'Kaksi iiristä, yksi äärettömyys',
      'reason.duo_kiss_collision.own': 'Kaksi maailmaa, yksi purkaus',
      'reason.duo_kiss_collision.dark_brown': 'Kaksi maailmaa, yksi purkaus',
      'reason.duo_kiss_collision.grey': 'Kaksi maailmaa, yksi purkaus',
      'reason.grp_collision.own': 'Jokainen omassa värissään',
      'reason.grp_collision.dark_brown': 'Jokainen omassa värissään',
      'reason.grp_collision.grey': 'Jokainen omassa värissään',
    },
    lines: {
      'line.solo_clean': 'Entisöity iiriksesi yksin puhtaalla mustalla.',
      'line.solo_powder': 'Reuna hajoaa rakeiksi silmäsi omissa väreissä.',
      'line.solo_universe': 'Oma iiriksesi täyttää suurennettuna koko kankaan.',
      'line.solo_splash': 'Reuna nousee nestekruunuksi.',
      'line.solo_gold': 'Hieno kultarengas ja sädekehä iiriksen ympärillä.',
      'line.solo_radiance': 'Hienoja valonsäteitä oman iiriksesi väreissä.',
      'line.solo_supernova': 'Tähtipöly purkautuu reunasta silmäsi omissa väreissä.',
      'line.solo_nebula': 'Iiriksesi hehkuu tähtisumun sydämessä.',
      'line.solo_sparks': 'Kipinät nousevat reunasta silmäsi omissa väreissä.',
      'line.solo_halo': 'Iiriksesi, takaa valaistuna omalla värillään.',
      'line.solo_aurora': 'Revontulten verhot iiriksesi ympärillä.',
      'line.solo_echo': 'Iiriksesi oman kaikunsa sisällä, säikeet kurottavat ulospäin kuin tunneli.',
      'line.solo_galaxy': 'Tähtien spiraalihaarat kiertyvät iiriksestäsi ulos sen omissa väreissä.',
      'line.duo_galaxy': 'Kaksi iiristä yhden spiraaligalaksin sydämessä, kumpikin haara omissa väreissään.',
      'line.grp_galaxy': 'Yksi galaksi koko perheelle, yksi haara kunkin ihmisen väreissä.',
      'line.grp_powder': 'Jokainen iiris muuttuu pölyksi omissa väreissään, ja pölyt sekoittuvat keskellä.',
    },
    tileAlt: (name: string) => `${name} sinun silmilläsi: pienennetty esikatselu vesileimalla`,
    tileMaking: (name: string) => `${name}: esikatselua tehdään`,
    tileFailed: 'Esikatselua ei tehty',
    changed: {
      eyes: (from: string, to: string, n: number) => `${from} ei ole saatavilla ${n} silmälle, joten valitsimme tyylin ${to}.`,
      gate: (from: string, to: string, i: number) => `${from} tarvitsee puhtaamman iiriksen, joten valitsimme toistaiseksi tyylin ${to}. Kuvaa silmä ${i} uudelleen, jos haluat käyttää tyyliä ${from}.`,
      reseal: (from: string, to: string, i: number) => `Jos haluat käyttää tyyliä ${from}, tee silmän ${i} esikatselu uudelleen. Toistaiseksi valitsimme tyylin ${to}.`,
      pupil: (from: string, to: string) => `${from} ei sovi tähän pupillin muotoon, joten valitsimme tyylin ${to}.`,
    },
    chipRetake: 'Uusi kuva',
    chipLabel: (i: number) => `Silmä ${i}: tarvitaan uusi kuva`,
    advisory: (list: number[], total: number) => (total === 1
      ? 'Iiriksesi renkaassa on vielä silmäluomi tai ripsi. Ota uusi kuva, niin tulos on puhtaampi.'
      : `${list.length === 1 ? `Silmä ${list[0]}` : `Silmät ${andList(list)}`}: renkaassa on vielä silmäluomi tai ripsi. Ota uusi kuva, niin tulos on puhtaampi.`),
    retake: {
      calm: 'Jotta voimme näyttää tyylit, tarvitsemme vielä yhden kuvan.',
      manual: 'Etkö vieläkään onnistu? Lähetä parhaat kuvasi osoitteeseen {link}, niin katsomme niitä.',
      noStyles: 'Tälle silmämäärälle ei voi vielä näyttää yhtään tyyliä. Poista yksi silmä tai kirjoita meille.',
    },
    stack: 'Kaksi iiristäsi eroavat väriltään paljon, joten toinen on toisen edessä.',
    widePupil: 'Pupillisi ovat laajat, joten iirikset koskettavat toisiaan eivätkä limity.',
    options: {
      swap: 'Vaihda paikkoja',
      rotate: 'Kierrä paikkoja',
      earlier: 'Siirrä aiemmaksi',
      later: 'Siirrä myöhemmäksi',
      earlierLabel: (i: number) => `Siirrä silmä ${i} aiemmaksi taideteoksessa`,
      laterLabel: (i: number) => `Siirrä silmä ${i} myöhemmäksi taideteoksessa`,
      centre: 'Aseta keskelle',
      centreLabel: (i: number) => `Aseta silmä ${i} taideteoksen keskelle`,
      centreNote: 'Ensimmäinen silmä on keskellä, muut kiertävät sen ympärillä. Valitse silmä yltä ja aseta se keskelle.',
      look: 'Ilme',
    },
    names: {
      title: 'Teksti taideteoksessa (valinnainen)',
      nameFor: (i: number, total: number) => (total === 1 ? 'Nimi (valinnainen)' : `Nimi silmälle ${i}`),
      date: 'Päivämäärä (valinnainen)',
      datePlaceholder: 'Esimerkiksi 14.6.2026',
      family: 'Sukunimi (valinnainen)',
      problem: {
        nameLong: (i: number, max: number) => `Silmän ${i} nimi on liian pitkä: enintään ${kirjaimet(max)}.`,
        namesLong: (max: number) => `Nimet ovat yhteensä liian pitkät: enintään ${kirjaimet(max)}.`,
        glyph: (chars: string) => `Taideteoksen fontilla ei voi piirtää merkkiä ${chars}. Käytä toista kirjainta.`,
        dateLong: (max: number) => `Päivämäärä on liian pitkä: enintään ${merkit(max)}.`,
        familyLong: (max: number) => `Sukunimi on liian pitkä: enintään ${kirjaimet(max)}.`,
      },
    },
  },

  price: {
    title: 'Tämän taideteoksen hinta',
    eyes: (n: number, style: string) => `${silmat(n)} · ${style}`,
    black: (name: string, black: string, art: string) => `1 silmä: ${black} tyylillä ${name}, ${art} kaikilla muilla tyyleillä.`,
    duoOffer: (two: string) => `Lisää toinen silmä: ${two} molemmista yhteensä.`,
    extra: (two: string, further: string, max: number) => `Kaksi silmää ${two}, sen jälkeen +${further} jokaisesta lisäsilmästä, enintään ${silmat(max)}.`,
    // the words of src/landing/copy/fi.json pricing.notice, then the free preview
    notice: 'Tilaaminen avautuu pian: esikatselusi on tänään ilmainen.',
    footnote: 'Saisit yhden digitaalisen tiedoston, 4096 px pisimmältä sivulta, ilman vesileimaa. Hinnat euroina.',
    footnoteAud: 'Saisit yhden digitaalisen tiedoston, 4096 px pisimmältä sivulta, ilman vesileimaa. Hinnat Australian dollareina (A$).',
    footnoteHuf: 'Saisit yhden digitaalisen tiedoston, 4096 px pisimmältä sivulta, ilman vesileimaa. Hinnat Unkarin forintteina (Ft).',
    footnoteUsd: 'Saisit yhden digitaalisen tiedoston, 4096 px pisimmältä sivulta, ilman vesileimaa. Hinnat Yhdysvaltain dollareina (US$).',
    demo: 'Tämä on esittely tekoälyn luomalla näytesilmällä. Kokeile omalla silmälläsi, niin näet oman hintasi.',
    sampleNotCounted: (k: number) => (k === 1
      ? 'Tekoälyn luoma näytesilmä ei kuulu tilaukseen, joten sitä ei lasketa mukaan.'
      : `Tekoälyn luomat näytesilmät (${k}) eivät kuulu tilaukseen, joten niitä ei lasketa mukaan.`),
  },

  // ordering from the result screen. The waiver and the links under it are src/shared/legal.ts CHECKOUT_LEGAL.fi, word
  // for word the text the server records (api/_lib/pay.py CONSENT_TEXT["fi"]).
  buy: {
    // the label and the price, as in English (see the header)
    button: (price: string) => `${CHECKOUT_LEGAL.fi.continueButton} · ${price}`,
    waitPreview: 'Tämän valinnan esikatselua tehdään vielä. Voit tilata heti, kun näet sen.',
    previewFailed: 'Lataa ensin tämän valinnan esikatselu (yllä: ”Yritä uudelleen”), jotta näet, mitä tilaat.',
    steps: {
      sync: 'Tarkistamme tilaustasi…',
      upload: (i: number, n: number) => (n > 1 ? `Lähetämme silmää ${i}/${n}…` : 'Lähetämme silmääsi…'),
      arrange: 'Asettelemme silmiäsi…',
      checkout: 'Avaamme turvallista maksusivua…',
    },
    // the card shows its own replace button(s) right under this line, so the line names none
    sample: (k: number): string => (k === 1
      ? 'Tekoälyn luomaa näytesilmää ei voi tilata. Vaihda sen tilalle oma silmäsi, niin voit tilata tämän taideteoksen.'
      : 'Tekoälyn luomia näytesilmiä ei voi tilata. Vaihda niiden tilalle omat silmäsi, niin voit tilata tämän taideteoksen.'),
    replaceSampleEye: (i: number) => `Vaihda silmän ${i} tilalle omasi`,
    // api/order.py draft: an eye is accepted with its photo's work ticket (15 minutes) or its sealed preview (api/_lib/preview.py SEAL_TTL, 48 hours)
    stale: (list: number[], total: number) => (total === 1
      ? 'Kuvasi on otettu yli 2 päivää sitten. Kuvan voi tilata 2 päivän kuluessa sen ottamisesta, joten ota se uudelleen, jos haluat tilata.'
      : `${list.length === 1 ? `Silmä ${list[0]}` : `Silmät ${andList(list)}`} on kuvattu yli 2 päivää sitten. Kuvan voi tilata 2 päivän kuluessa sen ottamisesta, joten kuvaa ${list.length === 1 ? 'se' : 'ne'} uudelleen, jos haluat tilata.${list.length < total ? ' Muut silmäsi pysyvät ennallaan.' : ''}`),
    cancelled: 'Maksu peruttiin. Mitään ei veloitettu. Taideteoksesi on yhä täällä: voit muuttaa sitä tai tilata uudelleen.',
    cancelledLost: 'Maksu peruttiin. Mitään ei veloitettu. Tämä sivu ei voinut säilyttää esikatseluasi, joten ota kuvasi uudelleen.',
    close: 'Sulje',
    errors: {
      network: 'Emme saaneet yhteyttä SnapEyesiin. Tarkista verkkoyhteytesi ja yritä uudelleen.',
      busy: 'Maksupalvelu ei vastannut. Yritä hetken kuluttua uudelleen.',
      payments: `Emme saaneet maksusivua auki. Yritä myöhemmin uudelleen tai kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
      too_large: 'Yhden silmäsi kuva on liian suuri lähetettäväksi. Kuvaa se silmä uudelleen.',
      // api/order.py draft: 503 uploads_paused and 429 too_many_uploads, both until the next day (UTC)
      paused: `Uudet tilaukset on tältä päivältä keskeytetty: päivittäinen lähetysraja on täynnä. Mitään ei veloitettu. Yritä huomenna uudelleen tai kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
      too_many: `Tämän tilauksen lähetysraja on tältä päivältä täynnä (30 lähetystä, uudet kuvat mukaan lukien). Mitään ei veloitettu. Yritä huomenna uudelleen tai kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
      failed: `Tilauksesi valmistelussa meni jokin vikaan. Yritä uudelleen tai kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
      closed: 'Tilaaminen ei ole vielä auki.',
      plan_changed: 'Taideteoksesi muuttui juuri äsken, joten teimme esikatselun uudelleen. Tarkista se ja paina sitten painiketta uudelleen.',
      unavailable: 'Tätä tyyliä ei voi juuri nyt tilata silmillesi. Valitse toinen tai kuvaa silmä uudelleen.',
      print_unavailable: 'Tulosteita ei voi tilata juuri nyt. Voit tilata pelkän digitaalisen tiedoston.',
      print_changed: 'Tulosteen hinta muuttui juuri äsken. Tarkista se uudelleen ja paina sitten painiketta.',
      voucher: 'Lahjakorttiasi ei voitu käyttää: se on ehkä jo käytetty tai vanhentunut. Tarkista se uudelleen.',
    },
    namesBlocked: 'Korjaa ensin taideteoksen teksti (katso yllä).',
    footnote: 'Digitaalinen tiedosto, 4096 px, ilman vesileimaa.',
  },

  gift: {
    open: 'Minulla on lahjakortti',
    label: 'Lahjakortin koodi',
    apply: 'Käytä',
    checking: 'Tarkistamme koodia',
    applied: (value: string) => `Lahjakortti: −${value}`,
    remove: 'Poista',
    toPay: (value: string) => `Maksettavaa: ${value}`,
    note: 'Lahjakortti käytetään, kun viet maksun loppuun. Jos taideteos maksaa vähemmän kuin lahjakortin arvo, loppuosaa ei makseta takaisin.',
    errors: {
      format: 'Tämä ei ole lahjakortin koodi. Koodissa on 12 kirjainta ja numeroa, esimerkiksi ABCD-EFGH-JKLM.',
      unknown: 'Emme tunne tätä koodia. Tarkista se.',
      used: 'Tämä lahjakortti on jo käytetty.',
      expired: 'Tämä lahjakortti on vanhentunut.',
      currency: 'Tätä lahjakorttia voi käyttää vain euromääräisiin tilauksiin.',
      failed: 'Emme voineet tarkistaa koodia juuri nyt. Yritä uudelleen.',
    },
  },

  // the anonymous feedback box (src/try/Feedback.tsx, api/_lib/feedback.py)
  feedback: {
    title: { result: 'Miltä se näyttää sinusta?', retake: 'Auttoiko tämä?' },
    hint: { result: 'Yksi napautus ja halutessasi muutama sana. Viesti menee ihmiselle, joka tekee näitä.', retake: 'Kerro yhdellä napautuksella, mikä tuli tiellesi.' },
    chips: {
      result: { love: 'Ihana', likeness: 'Se ei näytä minun silmältäni', colour: 'Värit näyttävät vääriltä', style: 'Halusin toisen tyylin', price: 'Hinta on liian korkea', other: 'Jokin muu' },
      retake: { unclear: 'En ymmärrä, mikä on vialla', fine: 'Minusta kuvani on hyvä', device: 'Puhelimeni ei pysty parempaan', only: 'Se on ainoa kuvani', effort: 'Tämä on liian työlästä', other: 'Jokin muu' },
    },
    textLabel: 'Haluatko lisätä jotain? (valinnainen)',
    textHint: 'Älä kirjoita nimiä, sähköpostiosoitteita tai puhelinnumeroita.',
    count: (n: number, max: number) => `${n}/${max}`,
    send: 'Lähetä',
    sending: 'Lähetetään',
    thanks: 'Kiitos. Viestisi meni perille ihmiselle, joka tekee näitä.',
    textDropped: 'Kiitos. Laskimme vastauksesi mukaan, mutta emme säilyttäneet tekstiä, koska siinä näytti olevan yhteystietoja tai linkki.',
    textLost: 'Kiitos. Vastauksesi tuli perille, mutta tekstiä ei voitu tallentaa.',
    failed: 'Lähetys ei onnistunut. Yritä hetken kuluttua uudelleen.',
    privacy: 'Nimetön: ei nimeä, ei sähköpostia. Teksti poistetaan 90 päivän kuluttua.',
  },

  study: {
    title: (shot: number, photos: number) => (photos > 1 ? `Perhetesti · kuvat ${shot - photos + 1}-${shot}` : `Perhetesti · otos ${shot}`),
    light: 'Tämän otoksen valo',
    lights: {
      window_daylight: 'Päivänvalo ikkunasta', room_lamp: 'Huoneen lamppu', phone_torch: 'Puhelimen taskulamppu', someone_helped: 'Joku auttoi',
    } satisfies Record<LightAnswer, string>,
    comfort: 'Kuinka helppoa se oli? 1 vaikeaa, 5 helppoa',
    skip: 'Ohita',
    // the engine logs the answers only with an analyze request, so they wait for the next photo
    thanks: 'Kiitos. Nämä vastaukset lähetetään seuraavan kuvasi mukana.',
    pending: (shots: number[]) => `Perhetesti: vastauksiasi ${shots.length === 1 ? `otoksesta ${shots[0]}` : `otoksista ${shots.join(', ')}`} ei ole vielä lähetetty. Ne lähtevät seuraavan kuvasi mukana, esimerkiksi kun lisäät toisen silmän. Jos suljet sivun nyt, ne häviävät.`,
  },
};
