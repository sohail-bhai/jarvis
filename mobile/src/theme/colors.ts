export const colors = {
  // Backgrounds
  background: '#FFFFFF',
  surface: '#F8F9FB',
  surfaceHover: '#F0F2F5',

  // Primary
  primary: '#3B7DDD',
  primaryLight: '#EBF2FC',
  primaryDark: '#2C5FA8',

  // Text
  textPrimary: '#1B2A4A',
  textSecondary: '#6B7B94',
  textTertiary: '#9EAABB',
  textInverse: '#FFFFFF',

  // Status
  success: '#4CAF6E',
  successLight: '#EDF7F0',
  warning: '#F5A623',
  warningLight: '#FEF6E8',
  error: '#E85D4A',
  errorLight: '#FDEEEC',

  // Borders & Dividers
  border: '#E8ECF1',
  borderLight: '#F0F2F5',
  divider: '#EEF0F4',

  // Cards & Surfaces
  card: '#FFFFFF',
  cardElevated: '#FFFFFF',

  // Tab Bar
  tabBarBackground: '#FFFFFF',
  tabBarBorder: '#E8ECF1',
  tabBarActive: '#3B7DDD',
  tabBarInactive: '#9EAABB',

  // Overlay
  overlay: 'rgba(27, 42, 74, 0.5)',
  overlayLight: 'rgba(27, 42, 74, 0.08)',

  // Specific UI
  progressTrack: '#E8ECF1',
  progressFill: '#3B7DDD',
  notificationBadge: '#E85D4A',
  avatarBackground: '#3B7DDD',
  killSwitch: '#E85D4A',

  // File type colors
  filePresentation: '#E85D4A',
  filePdf: '#E85D4A',
  fileDocument: '#3B7DDD',
  fileSpreadsheet: '#4CAF6E',
  fileArchive: '#6B7B94',
  fileImage: '#F5A623',
  fileFolder: '#6B7B94',
} as const;

export type ColorToken = keyof typeof colors;
