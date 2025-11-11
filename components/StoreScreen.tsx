import React from 'react';
import { useLocalization } from '../lib/localization';

interface StoreScreenProps {
    credits: number;
    setCredits: React.Dispatch<React.SetStateAction<number>>;
}

const StoreScreen: React.FC<StoreScreenProps> = ({ credits, setCredits }) => {
  const { t } = useLocalization();

  return (
    <div className="p-6 bg-gray-900 min-h-full">
      <h2 className="text-3xl font-bold text-center mb-2">{t('storeTitle')}</h2>
      <p className="text-center text-gray-400 mb-8">{t('storeSub')}</p>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-cyan-400">{t('buyCredits')}</h3>
        <StoreItem
          title={t('credit1')}
          price="$0.99"
          description={t('credit1Sub')}
          onPurchase={() => setCredits(c => c + 1)}
        />
        <StoreItem
          title={t('credit5')}
          price="$3.99"
          description={t('credit5Sub')}
          onPurchase={() => setCredits(c => c + 5)}
        />
         <StoreItem
          title={t('credit20')}
          price="$9.99"
          description={t('credit20Sub')}
          onPurchase={() => setCredits(c => c + 20)}
        />
      </div>

      <div className="mt-12 space-y-4">
        <h3 className="text-lg font-semibold text-cyan-400">{t('subscription')}</h3>
        <StoreItem
          title={t('pro')}
          price="$2.99 / month"
          description={t('proSub')}
          onPurchase={() => {
            setCredits(c => c + 10);
            alert("Subscribed to SnapEyes Pro! (This is a simulation)");
          }}
          isPro
        />
      </div>

      <div className="text-center mt-12">
        <button className="text-gray-400 hover:text-white underline">
          {t('restorePurchases')}
        </button>
      </div>
    </div>
  );
};

interface StoreItemProps {
    title: string;
    price: string;
    description: string;
    onPurchase: () => void;
    isPro?: boolean;
}

const StoreItem: React.FC<StoreItemProps> = ({ title, price, description, onPurchase, isPro }) => (
    <div className={`p-4 rounded-lg flex justify-between items-center ${isPro ? 'bg-cyan-900/50 border-cyan-500 border' : 'bg-gray-800'}`}>
        <div>
            <h4 className="font-bold text-lg">{title}</h4>
            <p className="text-sm text-gray-300">{description}</p>
        </div>
        <button onClick={onPurchase} className={`font-bold py-2 px-5 rounded-full transition-transform transform hover:scale-105 ${isPro ? 'bg-cyan-500 text-black' : 'bg-cyan-600 text-white'}`}>
            {price}
        </button>
    </div>
);


export default StoreScreen;