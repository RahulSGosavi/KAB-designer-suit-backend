import { Request, Response, NextFunction } from 'express';

export class AppError extends Error {
  statusCode: number;
  isOperational: boolean;

  constructor(message: string, statusCode: number = 500) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

export const errorHandler = (
  err: Error | AppError,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const statusCode = err instanceof AppError ? err.statusCode : 500;
  const message = err.message || 'Internal server error';

  console.error('Error:', {
    message,
    statusCode,
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
    path: req.path,
    method: req.method,
    body: req.body,
  });

  // Provide more detailed error in development
  const errorResponse: any = {
    error: message,
  };

  if (process.env.NODE_ENV === 'development') {
    errorResponse.stack = err.stack;
    // Check for common database errors
    if (err.message?.includes('relation') && err.message?.includes('does not exist')) {
      errorResponse.hint = 'Database tables may not exist. Run: npm run migrate';
    }
    if (err.message?.includes('password authentication failed')) {
      errorResponse.hint = 'Database password incorrect. Check DB_PASSWORD in .env';
    }
    if (err.message?.includes('database') && err.message?.includes('does not exist')) {
      errorResponse.hint = 'Database does not exist. Create it first: CREATE DATABASE kab_design_tool;';
    }
  }

  res.status(statusCode).json(errorResponse);
};

export const notFoundHandler = (req: Request, res: Response) => {
  res.status(404).json({ error: 'Route not found' });
};

