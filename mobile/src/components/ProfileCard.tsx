import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';

interface ProfileCardProps {
  name: string;
  initials: string;
  workspace: string;
}

export function ProfileCard({ name, initials, workspace }: ProfileCardProps) {
  return (
    <View style={styles.container}>
      <View style={styles.avatar}>
        <Text style={styles.initials}>{initials}</Text>
      </View>
      <View style={styles.info}>
        <Text style={styles.name}>{name}</Text>
        <Text style={styles.workspace}>{workspace}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xl,
    gap: spacing.base,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.avatarBackground,
    justifyContent: 'center',
    alignItems: 'center',
  },
  initials: {
    ...typography.title,
    color: colors.textInverse,
    fontSize: 22,
  },
  info: {
    flex: 1,
  },
  name: {
    ...typography.title,
    color: colors.textPrimary,
  },
  workspace: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
});
