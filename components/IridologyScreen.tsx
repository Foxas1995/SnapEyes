
import React, { useState, useCallback, useMemo } from 'react';
import { IridologyAnalysis } from '../types';
import { analyzeIrisForIridology } from '../services/geminiService';
import { CameraIcon, SparklesIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';

interface IridologyScreenProps {
    enhancedImage: string | null;
    onGoToCapture: () => void;
}

const IridologyScreen: React.FC<IridologyScreenProps> = ({ enhancedImage, onGoToCapture }) => {
    const { t, language } = useLocalization();
    const [isLoading, setIsLoading] = useState(false);
    const [analysis, setAnalysis] = useState<IridologyAnalysis | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleAnalyze = useCallback(async () => {
        if (!enhancedImage) return;

        setIsLoading(true);
        setError(null);
        setAnalysis(null);

        try {
            const base64Data = enhancedImage.split(',')[1];
            const result = await analyzeIrisForIridology(base64Data, language);
            setAnalysis(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An unknown error occurred.');
        } finally {
            setIsLoading(false);
        }
    }, [enhancedImage, language]);

    const practicalTips = useMemo(() => {
        if (!analysis) return [];
        const structuralTips = analysis.keyFindings.flatMap(finding => finding.recommendations);
        const colorTips = analysis.colorAnalysis?.findings.flatMap(finding => finding.recommendations) || [];
        const allTips = [...structuralTips, ...colorTips];
        return [...new Set(allTips)]; // Get unique tips
    }, [analysis]);

    const renderContent = () => {
        if (!enhancedImage) {
            return (
                <div className="flex flex-col items-center justify-center text-center p-8 h-full">
                    <div className="w-24 h-24 bg-gray-800 rounded-full flex items-center justify-center mb-6">
                        <CameraIcon className="w-12 h-12 text-cyan-400" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">{t('getReading')}</h3>
                    <p className="text-gray-400 mb-6 max-w-sm">{t('getReadingSub')}</p>
                    <button
                        onClick={onGoToCapture}
                        className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-3 px-6 rounded-full transition-transform transform hover:scale-105"
                    >
                        {t('captureYourEyepic')}
                    </button>
                </div>
            );
        }

        if (isLoading) {
            return (
                <div className="flex flex-col items-center justify-center h-full text-center p-8">
                    <div className="relative w-40 h-40">
                        <img src={enhancedImage} alt="Analyzing Iris" className="w-full h-full rounded-full object-cover opacity-50" />
                        <div className="absolute inset-0 border-4 border-cyan-500 rounded-full animate-spin-slow"></div>
                        <div className="absolute inset-2 border-2 border-cyan-300 rounded-full animate-spin-slow-reverse"></div>
                    </div>
                    <h2 className="text-2xl font-bold mt-12 text-white">{t('analyzingIris')}</h2>
                    <p className="text-gray-300 mt-2">{t('analyzingIrisSub')}</p>
                    <style>{`
                        @keyframes spin-slow { to { transform: rotate(360deg); } }
                        .animate-spin-slow { animation: spin-slow 5s linear infinite; }
                        @keyframes spin-slow-reverse { to { transform: rotate(-360deg); } }
                        .animate-spin-slow-reverse { animation: spin-slow-reverse 6s linear infinite; }
                    `}</style>
                </div>
            );
        }
        
        if (error) {
             return (
                <div className="flex flex-col items-center justify-center text-center p-8 h-full">
                    <div className="w-20 h-20 flex items-center justify-center bg-red-500/20 rounded-full mb-4">
                       <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">{t('analysisFailed')}</h3>
                    <p className="text-gray-400 mb-6 max-w-sm">{error}</p>
                    <button
                        onClick={handleAnalyze}
                        className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-3 px-6 rounded-full transition-transform transform hover:scale-105"
                    >
                        {t('tryAgain')}
                    </button>
                </div>
             );
        }

        if (analysis) {
            return (
                <div className="p-6 space-y-6">
                    <div className="text-center">
                         <img src={enhancedImage} alt="Analyzed Iris" className="w-32 h-32 rounded-full object-cover mx-auto mb-4 border-4 border-cyan-700 shadow-lg"/>
                         <h2 className="text-2xl font-bold text-white">{t('yourReading')}</h2>
                         <p className="text-cyan-400">{analysis.constitutionalType} {t('constitution')}</p>
                    </div>

                    <div className="bg-gray-800 p-4 rounded-lg">
                        <h3 className="font-semibold text-white mb-2">{t('overallSummary')}</h3>
                        <p className="text-gray-300 text-sm leading-relaxed">{analysis.overallSummary}</p>
                    </div>
                    
                     <div className="grid grid-cols-2 gap-4 text-center">
                        <div className="bg-gray-800 p-3 rounded-lg">
                            <h4 className="text-xs text-gray-400 uppercase tracking-wider">{t('constitution')}</h4>
                            <p className="font-bold text-white text-lg">{analysis.constitutionalType}</p>
                        </div>
                        <div className="bg-gray-800 p-3 rounded-lg">
                             <h4 className="text-xs text-gray-400 uppercase tracking-wider">{t('strength')}</h4>
                            <p className="font-bold text-white text-lg">{analysis.constitutionalStrength}</p>
                        </div>
                    </div>
                    
                    <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-gray-300 text-sm leading-relaxed">{analysis.constitutionalTypeExplanation}</p>
                    </div>


                    <div>
                        <h3 className="font-semibold text-white mb-3 text-lg">{t('keyFindings')}</h3>
                        <div className="space-y-3">
                            {analysis.keyFindings.map((finding, index) => (
                                <div key={index} className="bg-gray-800 p-4 rounded-lg">
                                    <h4 className="font-bold text-cyan-400 text-lg">{finding.signName}</h4>
                                    
                                    <div className="mt-3 border-t border-gray-700 pt-3">
                                        <h5 className="font-semibold text-white text-sm mb-1">{t('signDescription')}</h5>
                                        <p className="text-sm text-gray-300 mb-3">{finding.signDescription}</p>
                                    </div>

                                    <div>
                                        <h5 className="font-semibold text-white text-sm mb-1">{t('signMeaning')}</h5>
                                        <p className="text-sm text-gray-300 mb-3">{finding.signMeaning}</p>
                                    </div>

                                    <div className="text-xs bg-gray-700 p-3 rounded text-gray-200">
                                        <p className="font-semibold mb-2 text-white">{t('wellnessTips')}:</p>
                                        <ul className="list-disc list-inside pl-2 space-y-1">
                                            {finding.recommendations.map((rec, i) => (
                                                <li key={i}>{rec}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {analysis.colorAnalysis && analysis.colorAnalysis.findings.length > 0 && (
                        <div>
                            <h3 className="font-semibold text-white mb-3 text-lg">{t('irisColorAnalysis')}</h3>
                            <div className="bg-gray-800 p-4 rounded-lg mb-3">
                                <h4 className="font-semibold text-white text-sm mb-1">{t('colorAnalysisSummary')}</h4>
                                <p className="text-gray-300 text-sm leading-relaxed">{analysis.colorAnalysis.summary}</p>
                            </div>
                            <div className="space-y-3">
                                {analysis.colorAnalysis.findings.map((finding, index) => (
                                    <div key={index} className="bg-gray-800 p-4 rounded-lg">
                                        <h4 className="font-bold text-cyan-400 text-lg">{finding.colorSign}</h4>
                                        
                                        <div className="mt-3 border-t border-gray-700 pt-3">
                                            <h5 className="font-semibold text-white text-sm mb-1">{t('signDescription')}</h5>
                                            <p className="text-sm text-gray-300 mb-3">{finding.description}</p>
                                        </div>

                                        {finding.recommendations && finding.recommendations.length > 0 && (
                                            <div className="text-xs bg-gray-700 p-3 rounded text-gray-200">
                                                <p className="font-semibold mb-2 text-white">{t('wellnessTips')}:</p>
                                                <ul className="list-disc list-inside pl-2 space-y-1">
                                                    {finding.recommendations.map((rec, i) => (
                                                        <li key={i}>{rec}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {practicalTips.length > 0 && (
                        <div>
                            <h3 className="font-semibold text-white mb-3 text-lg">{t('practicalTips')}</h3>
                            <div className="bg-gray-800 p-4 rounded-lg">
                                <ul className="list-disc list-inside space-y-2 text-gray-300 text-sm">
                                    {practicalTips.map((tip, index) => (
                                    <li key={index}>{tip}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}
                    
                    <button
                        onClick={onGoToCapture}
                        className="w-full mt-4 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-full flex items-center justify-center space-x-2 transition-colors"
                    >
                        <CameraIcon className="w-5 h-5" />
                        <span>{t('analyzeAnotherEye')}</span>
                    </button>

                    <div className="text-xs text-gray-500 text-left pt-4">
                        <p><strong>{t('disclaimer')}:</strong> {analysis.disclaimer}</p>
                    </div>
                </div>
            );
        }

        return (
            <div className="flex flex-col items-center justify-center text-center p-8 h-full">
                <img src={enhancedImage} alt="Your Iris" className="w-48 h-48 rounded-full object-cover mb-6 shadow-2xl shadow-cyan-500/20" />
                <h3 className="text-xl font-bold text-white mb-2">{t('readyForAnalysis')}</h3>
                <p className="text-gray-400 mb-6 max-w-sm">{t('readyForAnalysisSub')}</p>
                <button
                    onClick={handleAnalyze}
                    className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-4 px-8 rounded-full transition-transform transform hover:scale-105 flex items-center space-x-2"
                >
                    <SparklesIcon className="w-6 h-6" />
                    <span>{t('analyzeMyIris')}</span>
                </button>
            </div>
        );
    };

    return (
        <div className="bg-gray-900 min-h-full text-gray-300">
            {renderContent()}
        </div>
    );
};

export default IridologyScreen;
