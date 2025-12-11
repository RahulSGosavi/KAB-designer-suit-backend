import express, { Response, NextFunction } from 'express';
import { body, validationResult } from 'express-validator';
import { authenticate, type AuthRequest } from '../middleware/auth.js';
import type { BlockDefinition } from '../data/blockCatalog.js';
import { BLOCK_CATALOG } from '../data/blockCatalog.js';

const router = express.Router();

router.use(authenticate);

let runtimeCatalog: BlockDefinition[] = [...BLOCK_CATALOG];

router.get('/blocks', (_req, res: Response) => {
  res.json({ blocks: runtimeCatalog });
});

router.post(
  '/blocks',
  [
    body('id').trim().notEmpty(),
    body('name').trim().notEmpty(),
    body('category').trim().isIn(['kitchen', 'bathroom', 'furniture', 'electrical', 'plumbing']),
    body('width').isNumeric(),
    body('height').isNumeric(),
  ],
  (req: AuthRequest, res: Response, next: NextFunction) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }
      const block: BlockDefinition = {
        id: req.body.id,
        name: req.body.name,
        type: 'furniture',
        category: req.body.category,
        manufacturer: req.body.manufacturer,
        sku: req.body.sku,
        tags: req.body.tags,
        moduleClass: req.body.moduleClass,
        width: Number(req.body.width),
        height: Number(req.body.height),
        depth: req.body.depth ? Number(req.body.depth) : undefined,
        description: req.body.description,
        planSymbols: req.body.planSymbols || [],
      };

      runtimeCatalog = runtimeCatalog.filter((existing) => existing.id !== block.id).concat(block);

      res.status(201).json({ block });
    } catch (error) {
      next(error);
    }
  },
);

export default router;

