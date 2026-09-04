import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Switch, Pressable, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, borderRadius, shadows } from '../src/theme';

interface AwayOption {
  id: string;
  label: string;
  icon: string;
  enabled: boolean;
}

export default function WhileAwayScreen() {
  const router = useRouter();
  const [options, setOptions] = useState<AwayOption[]>([
    { id: 'opt-1', label: 'Continue my project', icon: 'code-slash-outline', enabled: true },
    { id: 'opt-2', label: 'Check my emails', icon: 'mail-outline', enabled: true },
    { id: 'opt-3', label: 'Research my topic', icon: 'search-outline', enabled: true },
    { id: 'opt-4', label: 'Organize my files', icon: 'folder-outline', enabled: false },
    { id: 'opt-5', label: 'Run scheduled tasks', icon: 'time-outline', enabled: false },
  ]);
  const [isWorking, setIsWorking] = useState(false);

  const toggleOption = (id: string) => {
    setOptions(prev => prev.map(opt => opt.id === id ? { ...opt, enabled: !opt.enabled } : opt));
  };

  const handleStartWorking = () => {
    const activeCount = options.filter(o => o.enabled).length;
    if (activeCount === 0) {
      Alert.alert('Select Tasks', 'Please enable at least one task for JARVIS to perform while you are away.');
      return;
    }
    setIsWorking(true);
    Alert.alert(
      'JARVIS Working Mode Activated',
      `JARVIS will autonomously handle ${activeCount} task(s) while you are away and notify you when approvals or results are ready.`,
      [{ text: 'OK', onPress: () => router.back() }]
    );
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable style={styles.backButton} onPress={() => router.back()} hitSlop={8}>
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </Pressable>
        <Ionicons name="airplane-outline" size={22} color={colors.primary} />
      </View>

      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Title Section */}
        <View style={styles.titleSection}>
          <Text style={styles.title}>While I'm Away</Text>
          <Text style={styles.subtitle}>
            Let JARVIS keep working while you're out. I'll notify you when it's done or needs you.
          </Text>
        </View>

        {/* Options List */}
        <View style={styles.optionsCard}>
          {options.map((opt, idx) => (
            <React.Fragment key={opt.id}>
              {idx > 0 && <View style={styles.divider} />}
              <View style={styles.optionRow}>
                <View style={styles.iconBox}>
                  <Ionicons name={opt.icon as any} size={20} color={colors.primary} />
                </View>
                <Text style={styles.optionLabel}>{opt.label}</Text>
                <Switch
                  value={opt.enabled}
                  onValueChange={() => toggleOption(opt.id)}
                  trackColor={{ false: colors.border, true: colors.primaryLight }}
                  thumbColor={opt.enabled ? colors.primary : colors.textTertiary}
                />
              </View>
            </React.Fragment>
          ))}
        </View>

        {/* Action Button */}
        <Pressable
          style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed]}
          onPress={handleStartWorking}
        >
          <Ionicons name="play" size={18} color={colors.textInverse} />
          <Text style={styles.primaryButtonText}>
            {isWorking ? 'Update Working Mode' : 'Start Working'}
          </Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  backButton: {
    padding: spacing.xs,
  },
  container: {
    flex: 1,
  },
  content: {
    padding: spacing.lg,
    gap: spacing.xl,
  },
  titleSection: {
    gap: spacing.xs,
  },
  title: {
    ...typography.titleLarge,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    lineHeight: 22,
  },
  optionsCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
    gap: spacing.md,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  optionLabel: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
    flex: 1,
  },
  divider: {
    height: 1,
    backgroundColor: colors.divider,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.lg,
    gap: spacing.sm,
    marginTop: spacing.md,
    ...shadows.sm,
  },
  pressed: {
    opacity: 0.85,
  },
  primaryButtonText: {
    ...typography.button,
    color: colors.textInverse,
  },
});
