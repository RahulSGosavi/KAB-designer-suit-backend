export type ModuleClass =
  | 'base'
  | 'wall'
  | 'tall'
  | 'vanity'
  | 'corner'
  | 'appliance'
  | 'panel'
  | 'custom';

export type PlanShape =
  | {
      kind: 'rect';
      x: number;
      y: number;
      width: number;
      height: number;
      cornerRadius?: number;
      stroke?: 'base' | 'detail' | string;
      strokeWidth?: number;
      fill?: 'base' | 'detail' | string;
      dash?: number[];
    }
  | {
      kind: 'line';
      points: [number, number, number, number];
      stroke?: 'base' | 'detail' | string;
      strokeWidth?: number;
      dash?: number[];
    }
  | {
      kind: 'circle';
      x: number;
      y: number;
      radius: number;
      stroke?: 'base' | 'detail' | string;
      strokeWidth?: number;
      fill?: 'base' | 'detail' | string;
      dash?: number[];
    };

export interface BlockDefinition {
  id: string;
  name: string;
  type: 'furniture';
  category: 'kitchen' | 'bathroom' | 'furniture' | 'electrical' | 'plumbing';
  manufacturer?: string;
  sku?: string;
  tags?: string[];
  moduleClass?: ModuleClass;
  width: number;
  height: number;
  depth?: number;
  description?: string;
  planSymbols: PlanShape[];
}

export const BLOCK_CATALOG: BlockDefinition[] = [
  {
    id: 'bed-single',
    name: 'Bed (Single)',
    type: 'furniture',
    category: 'furniture',
    manufacturer: 'Generic Furniture Co.',
    sku: 'BED-S-1000',
    width: 1000,
    height: 2000,
    planSymbols: [
      { kind: 'rect', x: 0, y: 0, width: 1, height: 1, cornerRadius: 0.04 },
      { kind: 'rect', x: 0.05, y: 0.05, width: 0.9, height: 0.35, fill: 'detail' },
      { kind: 'rect', x: 0.05, y: 0.45, width: 0.9, height: 0.5, fill: 'detail', dash: [0.02, 0.03] },
      { kind: 'line', points: [0.05, 0.45, 0.95, 0.45], stroke: 'detail' },
    ],
  },
  {
    id: 'bed-double',
    name: 'Bed (Double)',
    type: 'furniture',
    category: 'furniture',
    manufacturer: 'Generic Furniture Co.',
    sku: 'BED-D-1600',
    width: 1600,
    height: 2000,
    planSymbols: [
      { kind: 'rect', x: 0, y: 0, width: 1, height: 1, cornerRadius: 0.05 },
      { kind: 'line', points: [0.5, 0.05, 0.5, 0.95], stroke: 'detail', dash: [0.03, 0.03] },
      { kind: 'rect', x: 0.07, y: 0.07, width: 0.86, height: 0.32, fill: 'detail' },
      { kind: 'rect', x: 0.07, y: 0.45, width: 0.86, height: 0.48, fill: 'detail', dash: [0.02, 0.03] },
      { kind: 'line', points: [0.07, 0.45, 0.93, 0.45], stroke: 'detail' },
    ],
  },
  {
    id: 'sofa-3',
    name: 'Sofa (3-Seater)',
    type: 'furniture',
    category: 'furniture',
    manufacturer: 'ComfortLiving',
    sku: 'SOFA-3-2100',
    width: 2100,
    height: 800,
    planSymbols: [
      { kind: 'rect', x: 0, y: 0.1, width: 1, height: 0.8, cornerRadius: 0.05 },
      { kind: 'rect', x: 0.05, y: 0.05, width: 0.9, height: 0.35, fill: 'detail' },
      { kind: 'line', points: [0.33, 0.1, 0.33, 0.9], dash: [0.02, 0.02], stroke: 'detail' },
      { kind: 'line', points: [0.66, 0.1, 0.66, 0.9], dash: [0.02, 0.02], stroke: 'detail' },
      { kind: 'rect', x: 0.02, y: 0.2, width: 0.06, height: 0.6, fill: 'detail' },
      { kind: 'rect', x: 0.92, y: 0.2, width: 0.06, height: 0.6, fill: 'detail' },
    ],
  },
  {
    id: 'base-cabinet',
    name: 'Base Cabinet',
    type: 'furniture',
    category: 'kitchen',
    manufacturer: 'KAB Kitchens',
    sku: 'CAB-B-600',
    moduleClass: 'base',
    width: 600,
    height: 600,
    depth: 600,
    planSymbols: [
      { kind: 'rect', x: 0, y: 0, width: 1, height: 1 },
      { kind: 'line', points: [0.5, 0, 0.5, 1], stroke: 'detail' },
      { kind: 'circle', x: 0.25, y: 0.5, radius: 0.04, fill: 'detail' },
      { kind: 'circle', x: 0.75, y: 0.5, radius: 0.04, fill: 'detail' },
    ],
  },
  {
    id: 'sink-unit',
    name: 'Sink Base Unit',
    type: 'furniture',
    category: 'kitchen',
    manufacturer: 'KAB Kitchens',
    sku: 'SINK-900',
    moduleClass: 'base',
    width: 900,
    height: 600,
    depth: 600,
    planSymbols: [
      { kind: 'rect', x: 0, y: 0, width: 1, height: 1 },
      { kind: 'rect', x: 0.08, y: 0.1, width: 0.84, height: 0.6, fill: 'detail' },
      { kind: 'circle', x: 0.35, y: 0.4, radius: 0.05, stroke: 'base' },
      { kind: 'circle', x: 0.65, y: 0.4, radius: 0.05, stroke: 'base' },
      { kind: 'line', points: [0.08, 0.8, 0.92, 0.8], stroke: 'detail' },
      { kind: 'circle', x: 0.5, y: 0.25, radius: 0.03, fill: 'detail' },
    ],
  },
  {
    id: 'dining-table-rect',
    name: 'Dining Table (Rect)',
    type: 'furniture',
    category: 'furniture',
    manufacturer: 'Atelier Tables',
    sku: 'TABLE-RECT-1800',
    width: 1800,
    height: 900,
    planSymbols: [
      { kind: 'rect', x: 0, y: 0, width: 1, height: 1, cornerRadius: 0.08 },
      { kind: 'rect', x: 0.05, y: 0.15, width: 0.9, height: 0.7, stroke: 'detail' },
      { kind: 'circle', x: 0.15, y: 0.25, radius: 0.04, fill: 'detail' },
      { kind: 'circle', x: 0.15, y: 0.75, radius: 0.04, fill: 'detail' },
      { kind: 'circle', x: 0.85, y: 0.25, radius: 0.04, fill: 'detail' },
      { kind: 'circle', x: 0.85, y: 0.75, radius: 0.04, fill: 'detail' },
    ],
  },
  {
    id: 'wc',
    name: 'Toilet (WC)',
    type: 'furniture',
    category: 'bathroom',
    manufacturer: 'SanitaryWorks',
    sku: 'WC-400',
    width: 400,
    height: 700,
    planSymbols: [
      { kind: 'rect', x: 0.35, y: 0, width: 0.3, height: 0.45, cornerRadius: 0.1 },
      { kind: 'circle', x: 0.5, y: 0.7, radius: 0.28, stroke: 'base' },
      { kind: 'circle', x: 0.5, y: 0.7, radius: 0.15, stroke: 'detail' },
    ],
  },
  {
    id: 'wardrobe',
    name: 'Wardrobe',
    type: 'furniture',
    category: 'furniture',
    manufacturer: 'Closets Pro',
    sku: 'WARD-1200',
    width: 1200,
    height: 2400,
    planSymbols: [
      { kind: 'rect', x: 0, y: 0, width: 1, height: 1 },
      { kind: 'line', points: [0.33, 0, 0.33, 1], stroke: 'detail' },
      { kind: 'line', points: [0.66, 0, 0.66, 1], stroke: 'detail' },
      { kind: 'circle', x: 0.16, y: 0.5, radius: 0.03, fill: 'detail' },
      { kind: 'circle', x: 0.5, y: 0.5, radius: 0.03, fill: 'detail' },
      { kind: 'circle', x: 0.84, y: 0.5, radius: 0.03, fill: 'detail' },
    ],
  },
];

