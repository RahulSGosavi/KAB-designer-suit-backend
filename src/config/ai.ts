import dotenv from 'dotenv';

dotenv.config();

export const openaiApiKey = process.env.OPENAI_API_KEY || '';
export const geminiApiKey = process.env.GEMINI_API_KEY || '';

export const hasOpenAIKey = Boolean(openaiApiKey);
export const hasGeminiKey = Boolean(geminiApiKey);

