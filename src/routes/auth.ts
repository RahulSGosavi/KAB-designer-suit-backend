import express, { Request, Response, NextFunction } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import type { StringValue } from 'ms';
import { body, validationResult } from 'express-validator';
import sql from '../config/db.js';
import { AppError } from '../middleware/errorHandler.js';

const router = express.Router();

// Register new company and user
router.post(
  '/register',
  [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 }),
    body('companyName').trim().notEmpty(),
    body('firstName').trim().optional(),
    body('lastName').trim().optional(),
  ],
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { email, password, companyName, firstName, lastName } = req.body;

      // Check if user already exists
      let existingUser;
      try {
        existingUser = await sql`SELECT id FROM users WHERE email = ${email}`;
      } catch (dbError: any) {
        console.error('Database query error:', dbError);
        if (dbError.code === 'ECONNREFUSED' || dbError.code === 'ENOTFOUND') {
          throw new AppError('Database connection failed. Please check your DATABASE_URL in .env file.', 503);
        }
        if (dbError.code === '42P01') {
          throw new AppError('Database tables do not exist. Please run: npm run migrate', 503);
        }
        throw dbError;
      }

      if (existingUser.length > 0) {
        throw new AppError('User already exists', 400);
      }

      // Create company
      const companySlug = companyName
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');

      let companyResult;
      try {
        companyResult = await sql`
          INSERT INTO companies (name, slug) 
          VALUES (${companyName}, ${companySlug})
          RETURNING id, name, slug
        `;
      } catch (dbError: any) {
        console.error('Database error creating company:', dbError);
        if (dbError.code === '42P01') {
          throw new AppError('Database tables do not exist. Please run: npm run migrate', 503);
        }
        throw dbError;
      }

      const company = companyResult[0];

      // Hash password
      const passwordHash = await bcrypt.hash(password, 10);

      // Create user
      const userResult = await sql`
        INSERT INTO users (company_id, email, password_hash, first_name, last_name, role) 
        VALUES (${company.id}, ${email}, ${passwordHash}, ${firstName || null}, ${lastName || null}, 'admin')
        RETURNING id, email, first_name, last_name, role
      `;

      const user = userResult[0];

      // Generate JWT token
      const jwtSecret = process.env.JWT_SECRET;
      if (!jwtSecret) {
        throw new AppError('JWT_SECRET not configured', 500);
      }
      const expiresIn: StringValue | number =
        (process.env.JWT_EXPIRES_IN || '7d') as StringValue;
      const token = jwt.sign(
        {
          userId: user.id,
          companyId: company.id,
          role: user.role,
        },
        jwtSecret,
        { expiresIn }
      );

      res.status(201).json({
        token,
        user: {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          role: user.role,
        },
        company: {
          id: company.id,
          name: company.name,
          slug: company.slug,
        },
      });
    } catch (error) {
      console.error('Registration error:', error);
      next(error);
    }
  }
);

// Login
router.post(
  '/login',
  [
    body('email').isEmail().normalizeEmail(),
    body('password').notEmpty(),
  ],
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { email, password } = req.body;

      // Find user with company
      const result = await sql`
        SELECT u.id, u.email, u.password_hash, u.first_name, u.last_name, u.role, u.company_id,
               c.id as company_id, c.name as company_name, c.slug as company_slug
        FROM users u
        JOIN companies c ON u.company_id = c.id
        WHERE u.email = ${email} AND u.status = 'active'
      `;

      if (result.length === 0) {
        throw new AppError('Invalid credentials', 401);
      }

      const user = result[0];

      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password_hash);
      if (!isValidPassword) {
        throw new AppError('Invalid credentials', 401);
      }

      // Generate JWT token
      const jwtSecret = process.env.JWT_SECRET;
      if (!jwtSecret) {
        throw new AppError('JWT_SECRET not configured', 500);
      }
      const expiresIn: StringValue | number =
        (process.env.JWT_EXPIRES_IN || '7d') as StringValue;
      const token = jwt.sign(
        {
          userId: user.id,
          companyId: user.company_id,
          role: user.role,
        },
        jwtSecret,
        { expiresIn }
      );

      res.json({
        token,
        user: {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          role: user.role,
        },
        company: {
          id: user.company_id,
          name: user.company_name,
          slug: user.company_slug,
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

export default router;
