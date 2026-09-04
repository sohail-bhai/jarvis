import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing } from '../theme';
import { ActivityEntry } from '../services/types';

interface ActivityItemProps {
  entry: ActivityEntry;
}

function getActivityIcon(type: ActivityEntry['type']): { name: string; color: string } {
  switch (type) {
    case 'success':
      return { name: 'checkmark-circle', color: colors.success };
    case 'warning':
      return { name: 'warning', color: colors.warning };
    case 'error':
      return { name: 'close-circle', color: colors.error };
    case 'approval':
      return { name: 'shield-checkmark', color: colors.primary };
    default:
      return { name: 'information-circle', color: colors.primary };
  }
}

export function ActivityItemComponent({ entry }: ActivityItemProps) {
  const icon = getActivityIcon(entry.type);

  return (
    <View style={styles.container}>
      <Text style={styles.time}>{entry.timeLabel}</Text>
      <Ionicons name={icon.name as any} size={22} color={icon.color} style={styles.icon} />
      <View style={styles.content}>
        <Text style={styles.title}>{entry.title}</Text>
        {entry.description ? (
          <Text style={styles.description}>{entry.description}</Text>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    gap: spacing.md,
  },
  time: {
    ...typography.caption,
    color: colors.textTertiary,
    width: 60,
    paddingTop: 2,
  },
  icon: {
    marginTop: 1,
  },
  content: {
    flex: 1,
  },
  title: {
    ...typography.body,
    color: colors.textPrimary,
  },
  description: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
});
