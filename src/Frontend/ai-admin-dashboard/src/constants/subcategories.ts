/**
 * Subcategories for accessory products
 * Organized hierarchically by main category slug
 */

export const SUBCATEGORIES: Record<string, string[]> = {
  'rolling-papers': [
    '1¼ Size',
    '1½ Size',
    'King Size',
    'King Size Slim',
    'Regular Size',
    'Flavored',
    'Hemp Papers',
    'Rice Papers',
    'Pre-Rolled Cones'
  ],
  'tips-filters': [
    'Glass Tips',
    'Paper Tips',
    'Wooden Tips',
    'Reusable Filters',
    'Activated Carbon',
    'Pre-Made Tips'
  ],
  'blunt-wraps': [
    'Tobacco Wraps',
    'Hemp Wraps',
    'Flavored Wraps',
    'Natural Leaf',
    'Pre-Rolled Blunts'
  ],
  'grinders': [
    '2-Piece',
    '3-Piece',
    '4-Piece',
    'Electric',
    'Metal',
    'Acrylic',
    'Wooden',
    'Travel Size'
  ],
  'lighters': [
    'Disposable',
    'Refillable',
    'Torch',
    'Electric',
    'Hemp Wick',
    'Matches'
  ],
  'rolling-trays': [
    'Small',
    'Medium',
    'Large',
    'Metal',
    'Wood',
    'Plastic',
    'Magnetic',
    'LED'
  ],
  'storage-containers': [
    'Glass Jars',
    'Metal Tins',
    'Plastic Containers',
    'Smell Proof Bags',
    'Humidity Control',
    'UV Protection',
    'Travel Cases'
  ],
  'pipes-bowls': [
    'Glass Pipes',
    'Metal Pipes',
    'Wooden Pipes',
    'Silicone Pipes',
    'One-Hitters',
    'Chillums',
    'Bubblers',
    'Bowls & Slides'
  ],
  'bongs': [
    'Glass Bongs',
    'Acrylic Bongs',
    'Silicone Bongs',
    'Beaker Base',
    'Straight Tube',
    'Percolators',
    'Bubblers',
    'Downstems',
    'Bowl Pieces'
  ],
  'vaporizers': [
    'Dry Herb',
    'Concentrate',
    'Desktop',
    'Portable',
    'Pen Style',
    'Batteries',
    'Cartridges',
    'Accessories'
  ],
  'ashtrays': [
    'Glass',
    'Metal',
    'Ceramic',
    'Silicone',
    'Pocket',
    'Tabletop',
    'Outdoor'
  ],
  'rolling-machines': [
    '70mm',
    '79mm',
    '110mm',
    'Automatic',
    'Manual',
    'Joint Roller',
    'Blunt Roller'
  ],
  'cleaning-supplies': [
    'Cleaning Solutions',
    'Pipe Cleaners',
    'Brushes',
    'Wipes',
    'Alcohol',
    'Salt',
    'Cleaning Kits'
  ],
  'smell-proof-bags': [
    'Small Pouches',
    'Medium Bags',
    'Large Cases',
    'Backpacks',
    'Duffel Bags',
    'Lockable',
    'Waterproof'
  ],
  'other-accessories': [
    'Scales',
    'Magnifiers',
    'Scoops',
    'Funnels',
    'Stickers',
    'Apparel',
    'Books',
    'Miscellaneous'
  ]
};

/**
 * Get subcategories for a given category slug
 */
export const getSubcategoriesForCategory = (categorySlug: string): string[] => {
  return SUBCATEGORIES[categorySlug] || [];
};

/**
 * Get category slug from category ID
 */
export const getCategorySlug = (
  categoryId: string | number,
  categories: Array<{ id: number; slug: string }>
): string => {
  const category = categories.find(cat => cat.id === Number(categoryId));
  return category?.slug || '';
};
