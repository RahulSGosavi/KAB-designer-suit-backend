import express, { Response, NextFunction } from 'express';
import { body, validationResult } from 'express-validator';
import sql from '../config/db.js';
import { authenticate, AuthRequest } from '../middleware/auth.js';
import { AppError } from '../middleware/errorHandler.js';

const router = express.Router();

// All routes require authentication
router.use(authenticate);

// Get all projects for the user's company
router.get('/', async (req: AuthRequest, res, next) => {
  try {
    if (!req.companyId) {
      throw new AppError('Unauthorized', 401);
    }
    const companyId: string = req.companyId;
    const result = await sql`
      SELECT p.id, p.name, p.description, p.status, p.design_mode, p.is_draft, p.folder_id, p.created_at, p.updated_at,
             u.email as created_by,
             (SELECT COUNT(*) FROM project_data pd WHERE pd.project_id = p.id) as version_count
      FROM projects p
      JOIN users u ON p.user_id = u.id
      WHERE p.company_id = ${companyId}
      ORDER BY p.updated_at DESC
    `;

    res.json({ projects: result });
  } catch (error) {
    next(error);
  }
});

// Get single project with data
router.get('/:id', async (req: AuthRequest, res, next) => {
  try {
    const { id } = req.params;
    if (!req.companyId) {
      throw new AppError('Unauthorized', 401);
    }
    const companyId: string = req.companyId;

    // Get project
    const projectResult = await sql`
      SELECT p.*, u.email as created_by
      FROM projects p
      JOIN users u ON p.user_id = u.id
      WHERE p.id = ${id} AND p.company_id = ${companyId}
    `;

    if (projectResult.length === 0) {
      throw new AppError('Project not found', 404);
    }

    const project = projectResult[0];

    // Get latest project data
    const dataResult = await sql`
      SELECT data_json, version, updated_at
      FROM project_data
      WHERE project_id = ${id}
      ORDER BY version DESC
      LIMIT 1
    `;

    // Get PDF backgrounds
    const pdfResult = await sql`
      SELECT id, file_url, file_name, page_count, metadata, created_at
      FROM pdf_backgrounds
      WHERE project_id = ${id}
      ORDER BY created_at DESC
    `;

    res.json({
      project: {
        ...project,
        data: dataResult[0]?.data_json || null,
        version: dataResult[0]?.version || 0,
        pdfBackgrounds: pdfResult,
      },
    });
  } catch (error) {
    next(error);
  }
});

// Create new project
router.post(
  '/',
  [
    body('name').trim().notEmpty().withMessage('Project name is required'),
    body('description').trim().optional(),
  ],
  async (req: AuthRequest, res: Response, next: NextFunction) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { name, description, data } = req.body;
      
      if (!req.companyId || !req.userId) {
        throw new AppError('Unauthorized', 401);
      }
      const companyId: string = req.companyId;
      const userId: string = req.userId;

      // Extract design_mode, is_draft, folder_id from data if provided
      const designMode = data?.design_mode || '2d';
      const isDraft = data?.is_draft ?? true;
      const folderId = data?.folder_id || null;

      // Convert undefined to null for database
      const descriptionValue: string | null = description ?? null;

      // Create project
      const projectResult = await sql`
        INSERT INTO projects (company_id, user_id, name, description, design_mode, is_draft, folder_id)
        VALUES (${companyId}, ${userId}, ${name}, ${descriptionValue}, ${designMode}, ${isDraft}, ${folderId})
        RETURNING *
      `;

      const project = projectResult[0];

      // Save initial project data if provided
      if (data) {
        await sql`
          INSERT INTO project_data (project_id, data_json, version)
          VALUES (${project.id}, ${JSON.stringify(data)}, 1)
        `;
      }

      res.status(201).json({ project });
    } catch (error) {
      next(error);
    }
  }
);

// Update project
router.put(
  '/:id',
  [
    body('name').trim().optional(),
    body('description').trim().optional(),
  ],
  async (req: AuthRequest, res: Response, next: NextFunction) => {
    try {
      const { id } = req.params;
      const { name, description } = req.body;
      
      if (!req.companyId) {
        throw new AppError('Unauthorized', 401);
      }
      const companyId: string = req.companyId;

      // Verify project belongs to company
      const checkResult = await sql`
        SELECT id FROM projects WHERE id = ${id} AND company_id = ${companyId}
      `;

      if (checkResult.length === 0) {
        throw new AppError('Project not found', 404);
      }

      // Build update query dynamically using template literals
      if (name === undefined && description === undefined) {
        return res.json({ message: 'No fields to update' });
      }

      // Convert undefined to null for database
      const descriptionValue: string | null = description ?? null;

      // Use conditional updates with postgres template syntax
      let result;
      if (name !== undefined && description !== undefined) {
        result = await sql`
          UPDATE projects 
          SET name = ${name}, description = ${descriptionValue}
          WHERE id = ${id} AND company_id = ${companyId}
          RETURNING *
        `;
      } else if (name !== undefined) {
        result = await sql`
          UPDATE projects 
          SET name = ${name}
          WHERE id = ${id} AND company_id = ${companyId}
          RETURNING *
        `;
      } else {
        result = await sql`
          UPDATE projects 
          SET description = ${descriptionValue}
          WHERE id = ${id} AND company_id = ${companyId}
          RETURNING *
        `;
      }

      res.json({ project: result[0] });
    } catch (error) {
      next(error);
    }
  }
);

// Save project data
router.post(
  '/:id/data',
  [body('data').notEmpty().withMessage('Project data is required')],
  async (req: AuthRequest, res: Response, next: NextFunction) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { id } = req.params;
      const { data } = req.body;
      
      if (!req.companyId) {
        throw new AppError('Unauthorized', 401);
      }
      const companyId: string = req.companyId;

      // Verify project belongs to company
      const checkResult = await sql`
        SELECT id FROM projects WHERE id = ${id} AND company_id = ${companyId}
      `;

      if (checkResult.length === 0) {
        throw new AppError('Project not found', 404);
      }

      // Get current version
      const versionResult = await sql`
        SELECT MAX(version) as max_version FROM project_data WHERE project_id = ${id}
      `;

      const nextVersion = (versionResult[0]?.max_version || 0) + 1;

      // Save new version
      const result = await sql`
        INSERT INTO project_data (project_id, data_json, version)
        VALUES (${id}, ${JSON.stringify(data)}, ${nextVersion})
        RETURNING id, version, updated_at
      `;

      // Update project updated_at
      await sql`
        UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ${id}
      `;

      res.status(201).json({
        message: 'Project data saved',
        version: result[0].version,
        savedAt: result[0].updated_at,
      });
    } catch (error) {
      next(error);
    }
  }
);

// Delete project
router.delete('/:id', async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;
    
    if (!req.companyId) {
      throw new AppError('Unauthorized', 401);
    }

    // Verify project belongs to company
    const checkResult = await sql`
      SELECT id FROM projects WHERE id = ${id} AND company_id = ${req.companyId}
    `;

    if (checkResult.length === 0) {
      throw new AppError('Project not found', 404);
    }

    // Delete project (cascade will delete related data)
    await sql`DELETE FROM projects WHERE id = ${id}`;

    res.json({ message: 'Project deleted successfully' });
  } catch (error) {
    next(error);
  }
});

export default router;
