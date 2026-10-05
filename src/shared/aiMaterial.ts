// The sentence about AI-made material (owner decision 10, review of 2026-10-04): written here once, in the four languages, and NOT yet published.
//
// Why it exists. The plate styles (Powder Burst, Splash, Elements, the Vortex look of Universe) draw their powder, crowns, flames or spirals from a
// finite library of plates, picked by the artwork's seed, so the matter around an iris is not unique to one customer: another artwork can hold the same
// piece. A page or a text that claims an artwork is "unique" would be untrue for those styles (scripts/check_texts.mjs refuses such words in every
// language), and the first draft of this sentence ("your iris itself is never redrawn") was withdrawn because the product restores the iris's finest
// fibres by AI. This is the corrected wording: it says what is shared, what stays the customer's, and that the fibres are restored.
//
// When it is published. In the SAME deploy that makes the first plate style orderable (work package WP18, the catalogue switch), never earlier (before
// that it would describe styles that cannot be bought) and never later. That deploy sets AI_MATERIAL_PUBLISHED to true; until then no page, no legal text
// and no e-mail holds the sentence (aiBlocks and aiSentence answer nothing), and the build's text check (check_texts.mjs) holds the four wordings to the
// same lint as every other string meanwhile, so that the flip is one line and cannot surface an untranslated or dash-bearing sentence.
//
// The wording is the owner's to confirm ("his exact words are needed"), counsel reads it, and the Lithuanian and Hungarian lines wait for a native
// reader: all three are on the review list (README, "Texts and legal wording").
import type { Lang } from './lang';

export const AI_MATERIAL_PUBLISHED = false;

export const AI_MATERIAL: Readonly<Record<Lang, string>> = {
  en:
    "In some styles the powder, liquid, flame or dust around your iris is AI-made material from a shared library, so another customer's artwork can contain the same piece. Your iris keeps the colours, the pattern and the layout of your photo; the finest fibres are restored by AI, as described above.",
  de:
    'Bei einigen Stilen sind das Pulver, die Flüssigkeit, die Flamme oder der Staub um Ihre Iris KI-erzeugtes Material aus einer gemeinsamen Bibliothek, sodass das Kunstwerk einer anderen Person dasselbe Stück enthalten kann. Ihre Iris behält die Farben, das Muster und die Anordnung Ihres Fotos; die feinsten Fasern werden, wie oben beschrieben, durch KI wiederhergestellt.',
  lt:
    'Kai kuriuose stiliuose milteliai, skystis, liepsna ar dulkės aplink Jūsų rainelę yra DI sukurta medžiaga iš bendros bibliotekos, todėl kito kliento kūrinyje gali būti tas pats elementas. Jūsų rainelė išlaiko Jūsų nuotraukos spalvas, raštą ir išdėstymą; smulkiausias skaidulas, kaip aprašyta aukščiau, atkuria DI.',
  hu:
    'Egyes stílusoknál az Ön íriszét körülvevő púder, folyadék, láng vagy por egy közös könyvtárból származó, mesterséges intelligencia által készített anyag, ezért egy másik vásárló alkotásában ugyanaz a darab is szerepelhet. Az Ön íriszének megmaradnak a fotója színei, mintázata és elrendezése; a legfinomabb rostokat, a fent leírtak szerint, a mesterséges intelligencia állítja helyre.',
};

/** The sentence as a block of a legal text: [] until it is published. */
export const aiBlocks = (lang: Lang): string[] => (AI_MATERIAL_PUBLISHED ? [AI_MATERIAL[lang]] : []);

/** The sentence for the end of a line of running text (a space in front of it), '' until it is published. */
export const aiSentence = (lang: Lang): string => (AI_MATERIAL_PUBLISHED ? ` ${AI_MATERIAL[lang]}` : '');
