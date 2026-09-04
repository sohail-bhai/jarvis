import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';

type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'default';

interface StatusBadgeProps {
  label: string;
  variant?: BadgeVariant;
  dot?: boolean;
}

const variantColors: Record<BadgeVariant, { bg: string; text: string; dot: string }> = {
  success: { bg: colors.successLight, text: colors.success, dot: colors.success },
  warning: { bg: colors.warningLight, text: colors.warning, dot: colors.warning },
  error: { bg: colors.errorLight, text: colors.error, dot: colors.error },
  info: { bg: colors.primaryLight, text: colors.primary, dot: colors.primary },
  default: { bg: colors.surface, text: colors.textSecondary, dot: colors.textTertiary },
};

export function StatusBadge({ label, variant = 'default', dot = true }: StatusBadgeProps) {
  const scheme = variantColors[variant];

  return (
    <View style={[styles.container, { backgroundColor: scheme.bg }]}>
      {dot && <View style={[styles.dot, { backgroundColor: scheme.dot }]} />}
      <Text style={[styles.label, { color: scheme.text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: borderRadius.full,
    gap: 5,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  label: {
    ...typography.labelSmall,
  },
});
