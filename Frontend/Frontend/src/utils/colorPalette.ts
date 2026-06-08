// Color palette for courses - vibrant and distinct colors
export const COURSE_COLORS = {
  "Python Programming": "#10B981", // Emerald
  "Web Development": "#F59E0B", // Amber
  "Web Development with React": "#F59E0B", // Amber
  "Database Management Systems": "#3B82F6", // Blue
  "Machine Learning Fundamentals": "#8B5CF6", // Purple
  "Machine Learning Basics": "#8B5CF6", // Purple
  "Data Science with Python": "#EC4899", // Pink
  "SQL Basics": "#06B6D4", // Cyan
  "Cybersecurity": "#EF4444", // Red
  "Cloud Computing": "#6366F1", // Indigo
  "Advanced React": "#14B8A6", // Teal
  "JavaScript Basics": "#FBBF24", // Gold
  "TypeScript Advanced": "#60A5FA", // Light Blue
};

// Fallback colors if course not in predefined list
const FALLBACK_COLORS = [
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#3B82F6", // Blue
  "#8B5CF6", // Purple
  "#EC4899", // Pink
  "#06B6D4", // Cyan
  "#EF4444", // Red
  "#6366F1", // Indigo
  "#14B8A6", // Teal
  "#FBBF24", // Gold
  "#F97316", // Orange
  "#84CC16", // Lime
];

const colorCache = new Map<string, string>();

/**
 * Get a consistent color for a course title
 * Uses predefined colors if available, otherwise generates from a palette
 */
export function getColorForCourse(courseTitle: string): string {
  if (!courseTitle) return FALLBACK_COLORS[0];

  // Check if already cached
  if (colorCache.has(courseTitle)) {
    return colorCache.get(courseTitle)!;
  }

  // Check if in predefined list
  if (courseTitle in COURSE_COLORS) {
    const color = COURSE_COLORS[courseTitle as keyof typeof COURSE_COLORS];
    colorCache.set(courseTitle, color);
    return color;
  }

  // Generate color from hash
  let hash = 0;
  for (let i = 0; i < courseTitle.length; i++) {
    hash = ((hash << 5) - hash) + courseTitle.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }
  const colorIndex = Math.abs(hash) % FALLBACK_COLORS.length;
  const color = FALLBACK_COLORS[colorIndex];
  colorCache.set(courseTitle, color);
  return color;
}

/**
 * Convert hex color to RGB
 */
export function hexToRGB(hex: string): { r: number; g: number; b: number } {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : { r: 0, g: 0, b: 0 };
}

/**
 * Get lighter version of a color (for backgrounds)
 */
export function getColorWithOpacity(hex: string, opacity: number): string {
  const rgb = hexToRGB(hex);
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity})`;
}
