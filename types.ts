
export enum AppScreen {
  ONBOARDING = 'ONBOARDING',
  CAPTURE = 'CAPTURE',
  CROP = 'CROP',
  PROCESSING = 'PROCESSING',
  ENHANCE_RESULT = 'ENHANCE_RESULT',
  EDIT = 'EDIT',
  EXPORT = 'EXPORT',
  STORE = 'STORE',
  GALLERY = 'GALLERY',
  SETTINGS = 'SETTINGS',
  WATCHFACE = 'WATCHFACE',
  IRIDOLOGY = 'IRIDOLOGY',
}

export interface HistoryItem {
  id: string;
  thumbnail: string;
  original: string;
  enhanced: string;
}

export interface IridologyFinding {
  signName: string;
  signDescription: string;
  signMeaning: string;
  recommendations: string[];
}

export interface ColorFinding {
  colorSign: string;
  description: string;
  recommendations: string[];
}

export interface IridologyAnalysis {
  overallSummary: string;
  constitutionalType: string;
  constitutionalTypeExplanation: string;
  constitutionalStrength: string;
  keyFindings: IridologyFinding[];
  colorAnalysis: {
    summary: string;
    findings: ColorFinding[];
  };
  disclaimer: string;
}

export interface CropData {
  centerX: number;
  centerY: number;
  radius: number;
}
