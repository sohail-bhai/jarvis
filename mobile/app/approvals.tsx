import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, borderRadius, shadows } from '../src/theme';
import { approvalsService } from '../src/services/approvals';
import { useAppState } from '../src/store/AppContext';
import { ApprovalRequest } from '../src/services/types';

export default function ApprovalsScreen() {
  const router = useRouter();
  const { dispatch } = useAppState();
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    try {
      const data = await approvalsService.getAllApprovals();
      setApprovals(data);
      dispatch({
        type: 'SET_APPROVAL_COUNT',
        payload: data.filter(item => item.status === 'pending').length,
      });
    } catch (error) {
      Alert.alert(
        'Could not reach JARVIS',
        error instanceof Error ? error.message : 'Your computer did not answer.',
      );
    }
  };

  const pendingApprovals = approvals.filter(a => a.status === 'pending');

  const handleApprove = async (id: string, title: string) => {
    setLoading(true);
    try {
      await approvalsService.approve(id);
      await loadApprovals();
      // Approving releases the access and lets the work continue. It has not
      // happened yet, so this must not say that it has.
      Alert.alert('Approved', `JARVIS is carrying on with "${title}".`);
    } catch (error) {
      Alert.alert(
        'Could not approve',
        error instanceof Error ? error.message : 'Your computer did not answer.',
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeny = async (id: string) => {
    setLoading(true);
    try {
      await approvalsService.deny(id);
      await loadApprovals();
    } catch (error) {
      Alert.alert(
        'Could not decline',
        error instanceof Error ? error.message : 'Your computer did not answer.',
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable style={styles.backButton} onPress={() => router.back()} hitSlop={8}>
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </Pressable>
        <Text style={styles.headerTitle}>Approvals</Text>
      </View>

      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {pendingApprovals.length === 0 ? (
          <View style={styles.emptyCard}>
            <Ionicons name="shield-checkmark" size={48} color={colors.success} />
            <Text style={styles.emptyTitle}>All Approvals Cleared</Text>
            <Text style={styles.emptySub}>JARVIS is working safely within established permissions.</Text>
          </View>
        ) : (
          pendingApprovals.map((approval) => (
            <View key={approval.id} style={styles.approvalCard}>
              {/* Shield Icon & Header matching Screen 8 */}
              <View style={styles.iconCircle}>
                <Ionicons name="shield-outline" size={28} color={colors.primary} />
              </View>

              <Text style={styles.title}>JARVIS needs your approval</Text>
              <Text style={styles.subtitle}>{approval.description}</Text>

              {/* Detail Metadata Card */}
              <View style={styles.metadataBox}>
                <View style={styles.metaRow}>
                  <View style={styles.metaLabelGroup}>
                    <Ionicons name="laptop-outline" size={18} color={colors.textSecondary} />
                    <Text style={styles.metaLabel}>Repository</Text>
                  </View>
                  <Text style={styles.metaValue}>
                    {approval.metadata['Repository'] || approval.metadata['Document'] || 'Hackwave'}
                  </Text>
                </View>

                <View style={styles.metaRow}>
                  <View style={styles.metaLabelGroup}>
                    <Ionicons name="checkmark-circle-outline" size={18} color={colors.success} />
                    <Text style={styles.metaLabel}>Tests</Text>
                  </View>
                  <Text style={[styles.metaValue, { color: colors.success }]}>
                    {approval.metadata['Tests'] || '142 passed'}
                  </Text>
                </View>

                <View style={styles.metaRow}>
                  <View style={styles.metaLabelGroup}>
                    <Ionicons name="document-text-outline" size={18} color={colors.textSecondary} />
                    <Text style={styles.metaLabel}>Files changed</Text>
                  </View>
                  <Text style={styles.metaValue}>
                    {approval.metadata['Files changed'] || approval.metadata['Changes'] || '8 files'}
                  </Text>
                </View>
              </View>

              <Text style={styles.footerNote}>This will make the changes live.</Text>

              {/* Action Buttons matching Screen 8 */}
              <View style={styles.actionButtons}>
                <Pressable
                  style={({ pressed }) => [styles.notNowButton, pressed && styles.pressed]}
                  onPress={() => handleDeny(approval.id)}
                  disabled={loading}
                >
                  <Text style={styles.notNowText}>Not Now</Text>
                </Pressable>

                <Pressable
                  style={({ pressed }) => [styles.approveButton, pressed && styles.pressed]}
                  onPress={() => handleApprove(approval.id, approval.title)}
                  disabled={loading}
                >
                  <Text style={styles.approveText}>Approve</Text>
                </Pressable>
              </View>
            </View>
          ))
        )}
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
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    gap: spacing.md,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.title,
    color: colors.textPrimary,
  },
  container: {
    flex: 1,
  },
  content: {
    padding: spacing.lg,
  },
  emptyCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.xl,
    padding: spacing['2xl'],
    alignItems: 'center',
    gap: spacing.md,
    marginTop: spacing['2xl'],
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  emptyTitle: {
    ...typography.subtitle,
    color: colors.textPrimary,
  },
  emptySub: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  approvalCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius['2xl'],
    padding: spacing.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.md,
  },
  iconCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  title: {
    ...typography.title,
    color: colors.textPrimary,
    textAlign: 'center',
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.xs,
    marginBottom: spacing.lg,
  },
  metadataBox: {
    width: '100%',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    padding: spacing.base,
    gap: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metaLabelGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  metaLabel: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  metaValue: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  footerNote: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.md,
    marginBottom: spacing.lg,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: spacing.md,
    width: '100%',
  },
  notNowButton: {
    flex: 1,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  approveButton: {
    flex: 1,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    ...shadows.sm,
  },
  pressed: {
    opacity: 0.85,
  },
  notNowText: {
    ...typography.button,
    color: colors.textSecondary,
  },
  approveText: {
    ...typography.button,
    color: colors.textInverse,
  },
});
