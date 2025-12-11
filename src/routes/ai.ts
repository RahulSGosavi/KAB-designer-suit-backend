import express from 'express';
import { hasOpenAIKey, hasGeminiKey, openaiApiKey } from '../config/ai.js';

const router = express.Router();

// Public endpoint to let frontend know which AI providers are configured
router.get('/config', (_req, res) => {
  res.json({
    hasOpenAIKey,
    hasGeminiKey,
  });
});

// Normalize/interpret a freeform prompt (spelling & intent softening)
router.post('/interpret', async (req, res) => {
  const { prompt } = req.body || {};
  const text: string = (prompt || '').toString().trim();

  if (!text) {
    return res.status(400).json({ error: 'prompt is required' });
  }

  // If no OpenAI key, do a small heuristic fallback
  if (!openaiApiKey) {
    const normalized = text
      .replace(/\b(make|build|draw)\b/gi, 'create')
      .replace(/\b(color|paint)\b/gi, 'paint')
      .replace(/\b(move|shift|relocate|place|put)\b/gi, 'move')
      .replace(/\b(set)\b/gi, 'set')
      .replace(/\b(kitchen island)\b/gi, 'island')
      .trim();
    return res.json({ normalizedPrompt: normalized });
  }

  try {
    // Use OpenAI Chat Completions via fetch (no SDK dependency)
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${openaiApiKey}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content:
              'You normalize user design commands. Fix spelling, keep intent concise. Use verbs like create/add/move/paint/set. Keep colors and units. Return one short sentence.',
          },
          { role: 'user', content: text },
        ],
        max_tokens: 120,
        temperature: 0,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      return res.status(502).json({ error: 'llm_failed', detail: errText });
    }

    const data = await response.json();
    const normalized =
      data?.choices?.[0]?.message?.content?.trim() || text;

    res.json({ normalizedPrompt: normalized });
  } catch (err: any) {
    console.error('AI interpret error:', err?.message || err);
    res.status(500).json({ error: 'interpret_failed' });
  }
});

export default router;

