import { GoogleGenAI, Modality, Type } from "@google/genai";
import { IridologyAnalysis } from "../types";
import { Language } from "../lib/localization";

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  console.warn("API_KEY environment variable not set. AI features will not work.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY! });

export interface IrisDetectionResult {
    success: boolean;
    centerX?: number;
    centerY?: number;
    radius?: number; // Normalized to image width
    error?: string;
    box?: {
        xMin: number;
        yMin: number;
        xMax: number;
        yMax: number;
    };
}

// New, faster function for real-time video frame analysis during capture.
// It prioritizes speed and detection reliability over precision by using a simple bounding box.
export async function findEyeInFrame(base64ImageData: string): Promise<IrisDetectionResult> {
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash', // Using Flash model for speed
            contents: {
                parts: [
                    {
                        inlineData: {
                            data: base64ImageData,
                            mimeType: 'image/jpeg',
                        },
                    },
                    {
                        text: `**Objective:** Quickly locate the most prominent human eye in this video frame for a camera to focus on.

**CRITICAL INSTRUCTIONS:**
1.  **Find the Eyeball:** Your primary goal is to find the eyeball itself, which includes the iris (colored part) and pupil (black center).
2.  **IGNORE OTHER FEATURES:** You MUST ignore eyebrows, hair, glasses, and large areas of just skin. Do NOT create a box for an eyebrow.
3.  **Create Bounding Box:** If you find a clear eye, return a tight bounding box around it.
4.  **Handle Failure:** If you cannot confidently find an eye that meets these criteria, you MUST return \`"eyeFound": false\`.

**Output:**
- Return a single raw JSON object. No markdown.
- All coordinate values must be normalized (0.0 to 1.0).
- \`eyeFound\`: boolean.
- \`box\`: An object with four properties: \`xMin\`, \`yMin\`, \`xMax\`, \`yMax\`.`,
                    },
                ],
            },
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        eyeFound: { type: Type.BOOLEAN },
                        box: {
                            type: Type.OBJECT,
                            properties: {
                                xMin: { type: Type.NUMBER },
                                yMin: { type: Type.NUMBER },
                                xMax: { type: Type.NUMBER },
                                yMax: { type: Type.NUMBER },
                            },
                        }
                    },
                    required: ["eyeFound"],
                },
            },
        });

        const jsonString = response.text;
        const parsed: { 
            eyeFound: boolean; 
            box?: { xMin: number, yMin: number, xMax: number, yMax: number };
        } = JSON.parse(jsonString);
        
        if (parsed.eyeFound && parsed.box) {
             const box = parsed.box;
             return {
                 success: true,
                 centerX: (box.xMin + box.xMax) / 2,
                 centerY: (box.yMin + box.yMax) / 2,
                 radius: (box.xMax - box.xMin) / 2,
                 box: box,
             };
        } else {
             return { success: false, error: "No eye found in frame." };
        }

    } catch (error) {
        console.error("Error finding eye in frame with Gemini API:", error);
        return { success: false, error: "AI analysis failed." };
    }
}


// Updated existing function for the final, precise crop after capture.
// It now includes instructions to ignore reflections for better accuracy.
export async function detectIris(base64ImageData: string): Promise<IrisDetectionResult> {
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-pro',
            contents: {
                parts: [
                    {
                        inlineData: {
                            data: base64ImageData,
                            mimeType: 'image/jpeg',
                        },
                    },
                    {
                        text: `**Objective:** Find the precise center and radius of the human iris for a perfect circular crop.

**CRITICAL CONTEXT:** The user wants to crop ONLY the colored part of the eye (the iris). The final result MUST be centered on the pupil.

**Instructions:**
1.  **Identify Key Features:** Locate the pupil (black center), the iris (colored ring), and the sclera (white part).
2.  **Find Pupil Center:** Your top priority is to find the exact geometric center of the **pupil**. This is the most important step. If the pupil is partially obscured by an eyelid or reflection, estimate its true center. Do not get distracted by the eyelid.
3.  **Measure Iris Radius:** From the pupil's center, measure the radius outwards to the edge of the colored iris. The measurement should stop where the color ends and the white sclera begins.
4.  **Final Verification:** Before returning coordinates, double-check your work. Does the circle defined by your center and radius actually contain a detailed iris and a darker pupil? If it primarily contains eyelid, skin, or is wildly off-center, you MUST return \`"irisFound": false\`.

**Output:**
- Return a single raw JSON object. No other text, no markdown.
- All values are normalized from 0.0 to 1.0 relative to the input image dimensions.
- \`centerX\`, \`centerY\`: The precise center of the **pupil**.
- \`radius\`: The radius of the iris, measured from the pupil center, normalized to the image's width.
- \`irisFound\`: A boolean. If you cannot confidently identify a pupil and iris, return '{"irisFound": false}'.`,
                    },
                ],
            },
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        irisFound: { type: Type.BOOLEAN, description: "Whether a clear human iris was detected in the image." },
                        centerX: { type: Type.NUMBER, description: "Normalized horizontal center of the PUPIL (0.0 to 1.0)." },
                        centerY: { type: Type.NUMBER, description: "Normalized vertical center of the PUPIL (0.0 to 1.0)." },
                        radius: { type: Type.NUMBER, description: "Normalized radius of the iris, relative to image width." },
                    },
                    required: ["irisFound"],
                },
                thinkingConfig: { thinkingBudget: 32768 }
            },
        });

        const jsonString = response.text;
        const parsed: { irisFound: boolean; centerX?: number; centerY?: number; radius?: number; } = JSON.parse(jsonString);
        
        if (parsed.irisFound && typeof parsed.centerX === 'number' && typeof parsed.centerY === 'number' && typeof parsed.radius === 'number') {
             return {
                 success: true,
                 centerX: parsed.centerX,
                 centerY: parsed.centerY,
                 radius: parsed.radius,
             };
        } else {
             return {
                success: false,
                error: "Could not detect an eye in the photo. Please try again with a clearer, more direct shot."
             };
        }

    } catch (error) {
        console.error("Error detecting iris with Gemini API:", error);
        return { 
            success: false, 
            error: "Could not analyze the photo. The AI model may be temporarily unavailable." 
        };
    }
}


export async function enhanceEyeImage(base64ImageData: string): Promise<string> {
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash-image',
            contents: {
                parts: [
                    {
                        inlineData: {
                            data: base64ImageData,
                            mimeType: 'image/jpeg',
                        },
                    },
                    {
                        text: `**Objective:** You are a world-class photo retoucher specializing in high-detail macro photography. Your task is to perform a subtle, photorealistic enhancement of this pre-cropped human iris image.

**CRITICAL CORE PRINCIPLE: PRESERVATION OVER FABRICATION.** The final image MUST look like a professionally photographed version of the *exact same iris*. You must NOT invent, add, or fundamentally change any of the iris's unique structural features (fibers, crypts, rings).

**Instructions:**

1.  **Realistic Reflection Removal:**
    *   Carefully identify and remove any harsh light glare or reflections from the iris and pupil.
    *   When filling in the area where a reflection was, you MUST realistically reconstruct the underlying texture and color based *only* on the immediately surrounding, visible iris patterns. Do not guess or invent new patterns. The fill must be seamless and unnoticeable.

2.  **Subtle Detail & Clarity Enhancement:**
    *   Increase the local contrast and clarity of the existing iris fibers to make them appear sharper and more defined.
    *   Improve the three-dimensional appearance by subtly enhancing natural shadows and highlights within the iris structure.
    *   **DO NOT** add new fibers or alter the existing pattern.

3.  **Natural Color & Lighting Correction:**
    *   Gently balance the lighting across the iris to create a more even, studio-lit appearance.
    *   Slightly increase the color saturation to make the natural hues more vibrant, but **DO NOT** change the original eye color.

4.  **Pupil Refinement:**
    *   Ensure the pupil is a deep, natural-looking black. Clean up any minor reflections or haziness within the pupil.
    *   Maintain the pupil's natural circular shape.

5.  **Final Composition:**
    *   The final output MUST be a 1:1 square image.
    *   The background MUST be pure black (#000000).
    *   The enhanced iris should fill the entire circular area of the image.

**Output:**
- Return ONLY the enhanced image data.`,
                    },
                ],
            },
            config: {
                responseModalities: [Modality.IMAGE],
            },
        });

        const parts = response.candidates?.[0]?.content?.parts;
        if (parts) {
            for (const part of parts) {
                if (part.inlineData) {
                    return part.inlineData.data;
                }
            }
        }
        
        throw new Error("No enhanced image data received from API.");
    } catch (error) {
        console.error("Error enhancing image with Gemini API:", error);
        throw error;
    }
}

export async function applyEffectToEyeImage(base64ImageData: string, effectPrompt: string): Promise<string> {
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash-image',
            contents: {
                parts: [
                    {
                        inlineData: {
                            data: base64ImageData,
                            mimeType: 'image/jpeg',
                        },
                    },
                    {
                        text: effectPrompt,
                    },
                ],
            },
            config: {
                responseModalities: [Modality.IMAGE],
            },
        });

        const parts = response.candidates?.[0]?.content?.parts;
        if (parts) {
            for (const part of parts) {
                if (part.inlineData) {
                    return part.inlineData.data;
                }
            }
        }

        throw new Error("No image data with effect received from API.");
    } catch (error) {
        console.error("Error applying effect with Gemini API:", error);
        throw error;
    }
}

export async function analyzeIrisForIridology(base64ImageData: string, language: Language): Promise<IridologyAnalysis> {
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: {
                parts: [
                    {
                        inlineData: {
                            data: base64ImageData,
                            mimeType: 'image/jpeg',
                        },
                    },
                    {
                        text: `
**Persona:** You are a world-renowned iridology expert and holistic wellness educator with 30+ years of practice. Your tone is that of a trusted, empathetic, and highly knowledgeable mentor. You NEVER provide medical diagnoses. Your focus is on identifying constitutional patterns and offering general wellness advice.

**Core Mission: Unique & Balanced Analysis**
Every iris is unique. Your primary goal is to provide a highly personalized analysis of THIS SPECIFIC iris, avoiding generic, boilerplate descriptions. Your analysis MUST be balanced, highlighting both the iris's inherent strengths (e.g., dense, well-organized fibers) and areas that suggest a need for wellness support (e.g., lacunae, specific pigmentations).

**Task:** Perform an in-depth, personalized iridological analysis of the provided iris photograph.

**Instructions:**
1.  **Constitutional Analysis:**
    *   Determine the constitutional type (Lymphatic, Biliary, or Hematogenic) and strength ('Strong/Dense', 'Good', 'Fair', 'Poor/Loose').
    *   **Provide a UNIQUE explanation** of what this specific combination implies. Mention both the positive aspects of this constitution and the potential tendencies that require mindfulness.
2.  **Identify Key & Unique Signs:**
    *   Scan the iris for its 3-5 MOST DEFINING characteristics. Don't just list common signs; focus on what makes THIS iris stand out.
    *   For each sign, provide a DETAILED and PERSONALIZED interpretation:
        *   **signDescription:** Describe EXACTLY what you see in THIS image. Be specific (e.g., "A prominent, open lacuna in the upper-right quadrant, near the 1 o'clock position...").
        *   **signMeaning:** Explain the potential meaning using clear, simple analogies. Connect it to bodily systems and explain WHY it suggests a certain tendency.
        *   **recommendations:** Provide 2-4 practical, actionable wellness tips directly related to the finding.
3.  **Iris Color Analysis:**
    *   Analyze the specific hues, pigments, and color patterns visible in THIS iris.
    *   Write a \`summary\` that is specific to the observed colors and what they suggest.
    *   Identify 1-3 specific \`colorSign\`s. For each, describe its appearance and provide related wellness recommendations.
4.  **Overall Summary:**
    *   Write a brief, encouraging, and PERSONALIZED summary. It must recap the key strengths you identified and the primary areas for focus. It should feel like a conclusion to a one-on-one consultation.
5.  **Disclaimer:** ALWAYS include the provided disclaimer verbatim.

**CRITICAL: LANGUAGE & TONE REQUIREMENT**
*   Your entire response (all string values in the JSON) MUST be written in FLAWLESS, IDIOMATIC, and natural-sounding **${language === 'lt' ? 'Lithuanian' : 'English'}**.
*   It must sound like it was written by a native-speaking LITHUANIAN (or English) wellness professional. **AVOID LITERAL, AWKWARD TRANSLATIONS.** The Lithuanian must be perfect.
*   The JSON *keys* MUST remain in English as specified in the schema. Only the string *values* are translated.

**Output Format:** Your response MUST be a single, raw JSON object without any markdown formatting. Adhere to the provided schema precisely.
                        `,
                    },
                ],
            },
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        overallSummary: { type: Type.STRING, description: "A brief, holistic, and encouraging summary of the iris constitution." },
                        constitutionalType: { type: Type.STRING, description: "The constitutional type (e.g., 'Lymphatic')." },
                        constitutionalTypeExplanation: { type: Type.STRING, description: "A clear explanation of what this constitutional type generally implies."},
                        constitutionalStrength: { type: Type.STRING, description: "The strength/density of the iris fibers (e.g., 'Good')." },
                        keyFindings: {
                            type: Type.ARRAY,
                            description: "An array of 3-5 most prominent findings.",
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    signName: { type: Type.STRING, description: "The name of the iridological sign found." },
                                    signDescription: { type: Type.STRING, description: "A clear visual description of the sign in the iris." },
                                    signMeaning: { type: Type.STRING, description: "An interpretation of what this sign suggests and which body systems it may relate to, using analogies." },
                                    recommendations: {
                                        type: Type.ARRAY,
                                        description: "A list of 2-4 general, safe wellness recommendations.",
                                        items: { type: Type.STRING }
                                    },
                                },
                                required: ["signName", "signDescription", "signMeaning", "recommendations"],
                            }
                        },
                        colorAnalysis: {
                            type: Type.OBJECT,
                            description: "Analysis of iris color patterns and pigmentations.",
                            properties: {
                                summary: { type: Type.STRING, description: "A summary of what the overall color distribution suggests." },
                                findings: {
                                    type: Type.ARRAY,
                                    description: "An array of 1-3 specific color findings.",
                                    items: {
                                        type: Type.OBJECT,
                                        properties: {
                                            // FIX: Changed shorthand property to a full object definition.
                                            colorSign: { type: Type.STRING, description: "The name of the color sign/pigmentation observed." },
                                            description: { type: Type.STRING, description: "A visual description of the color sign." },
                                            recommendations: {
                                                type: Type.ARRAY,
                                                description: "General wellness recommendations related to this finding.",
                                                items: { type: Type.STRING }
                                            },
                                        },
                                        required: ["colorSign", "description", "recommendations"],
                                    }
                                }
                            },
                            required: ["summary", "findings"],
                        },
                        disclaimer: { type: Type.STRING, description: "The verbatim disclaimer text." }
                    },
                    required: [
                        "overallSummary",
                        "constitutionalType",
                        "constitutionalTypeExplanation",
                        "constitutionalStrength",
                        "keyFindings",
                        "colorAnalysis",
                        "disclaimer",
                    ],
                },
            },
        });

        const jsonString = response.text.trim();
        const analysisResult: IridologyAnalysis = JSON.parse(jsonString);

        if (!analysisResult || !analysisResult.constitutionalType) {
            throw new Error("Invalid or incomplete analysis data received from API.");
        }
        
        return analysisResult;

    } catch (error) {
        console.error("Error analyzing iris with Gemini API:", error);
        throw error;
    }
}