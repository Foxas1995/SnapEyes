// The sentence /try shows when the price changed between the moment the page showed it and the moment the customer
// pressed the button (api/_lib/abtest.py: a checkout that carries "shown" is answered 409 price_changed when the
// server would charge something else, and nothing is created). Kept apart from copy.ts so the languages another team is
// adding need one more line here, not a change of copy.ts's shape: any language not listed reads English.
const NOTE: Record<string, (price: string) => string> = {
  en: (price) => `The price has changed while you were looking. It is now ${price}. Please check it and press the button again if you would like to continue.`,
  de: (price) => `Der Preis hat sich geändert, während Sie die Seite angesehen haben. Er beträgt jetzt ${price}. Bitte prüfen Sie ihn und drücken Sie den Knopf erneut, wenn Sie fortfahren möchten.`,
  lt: (price) => `Kaina pasikeitė, kol žiūrėjote. Dabar ji yra ${price}. Patikrinkite ją ir, jei norite tęsti, dar kartą paspauskite mygtuką.`,
  hu: (price) => `Az ár megváltozott, amíg nézelődött. Most ${price}. Kérjük, ellenőrizze, és ha folytatni szeretné, nyomja meg újra a gombot.`,
};

export function priceChangedNote(lang: string, price: string): string {
  return (NOTE[lang] ?? NOTE.en)(price);
}
