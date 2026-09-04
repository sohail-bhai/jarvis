import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';
import { ProgressBar } from './ProgressBar';
import { Task } from '../services/types';

interface TaskCardProps {
  task: Task;
  compact?: boolean;
  onPress?: () => void;
}

function getStatusIcon(status: Task['status']): { name: string; color: string } {
  switch (status) {
    case 'running':
      return { name: 'sync-circle', color: colors.primary };
    case 'completed':
      return { name: 'checkmark-circle', color: colors.success };
    case 'failed':
      return { name: 'close-circle', color: colors.error };
    case 'cancelled':
      return { name: 'ban', color: colors.textTertiary };
    case 'waiting_approval':
      return { name: 'time', color: colors.warning };
    default:
      return { name: 'ellipse-outline', color: colors.textTertiary };
  }
}

export function TaskCard({ task, compact = false, onPress }: TaskCardProps) {
  const statusIcon = getStatusIcon(task.status);

  if (compact) {
    return (
      <Pressable
        style={({ pressed }) => [styles.compactContainer, pressed && styles.pressed]}
        onPress={onPress}
      >
        <View style={styles.compactHeader}>
          <Text style={styles.compactLabel}>Currently working</Text>
          <View style={styles.inProgressBadge}>
            <View style={styles.inProgressDot} />
            <Text style={styles.inProgressText}>In progress</Text>
          </View>
        </View>
        <Text style={styles.compactTitle} numberOfLines={1}>{task.title}</Text>
        <Text style={styles.compactDescription} numberOfLines={1}>{task.description}</Text>
        <View style={styles.compactProgress}>
          <ProgressBar progress={task.progress} showLabel />
        </View>
      </Pressable>
    );
  }

  return (
    <Pressable
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}
      onPress={onPress}
    >
      <View style={styles.row}>
        <Ionicons name={statusIcon.name as any} size={24} color={statusIcon.color} />
        <View style={styles.content}>
          <View style={styles.titleRow}>
            <Text style={styles.title} numberOfLines={1}>{task.title}</Text>
            {task.status === 'running' && (
              <Text style={styles.percentage}>{task.progress}%</Text>
            )}
            {task.status === 'cancelled' && (
              <Text style={styles.cancelledLabel}>Cancelled</Text>
            )}
          </View>
          <Text style={styles.description} numberOfLines={1}>{task.description}</Text>
          {task.status === 'running' && (
            <View style={styles.progressContainer}>
              <ProgressBar progress={task.progress} />
            </View>
          )}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.card,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.base,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  pressed: {
    backgroundColor: colors.surfaceHover,
  },
  row: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  content: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
    flex: 1,
  },
  percentage: {
    ...typography.label,
    color: colors.primary,
    marginLeft: spacing.sm,
  },
  cancelledLabel: {
    ...typography.labelSmall,
    color: colors.textTertiary,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    marginLeft: spacing.sm,
  },
  description: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  progressContainer: {
    marginTop: spacing.sm,
  },

  // Compact variant (Home screen)
  compactContainer: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  compactHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  compactLabel: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  inProgressBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: borderRadius.full,
    gap: 4,
  },
  inProgressDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.primary,
  },
  inProgressText: {
    ...typography.labelSmall,
    color: colors.primary,
  },
  compactTitle: {
    ...typography.subtitle,
    color: colors.textPrimary,
  },
  compactDescription: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  compactProgress: {
    marginTop: spacing.md,
  },
});
