import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, borderRadius, shadows } from '../../src/theme';
import { JarvisInput } from '../../src/components/JarvisInput';
import { QuickAction } from '../../src/components/QuickAction';
import { ApprovalSheet } from '../../src/components/ApprovalSheet';
import { useAppState } from '../../src/store/AppContext';
import { jarvisService } from '../../src/services/jarvis';
import { tasksService } from '../../src/services/tasks';
import { approvalsService } from '../../src/services/approvals';
import { googleService } from '../../src/services/google';
import { openEventStream } from '../../src/api/live';
import { getHost } from '../../src/api/client';
import { Task, ApprovalRequest } from '../../src/services/types';

export default function HomeScreen() {
  const router = useRouter();
  const { state, dispatch } = useAppState();
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [approvalVisible, setApprovalVisible] = useState(false);
  const [currentApproval, setCurrentApproval] = useState<ApprovalRequest | null>(null);
  const [online, setOnline] = useState(false);
  const [problem, setProblem] = useState('');

  const greeting = jarvisService.getGreeting();
  const suggestions = jarvisService.getSuggestions();

  const loadData = useCallback(async () => {
    try {
      const tasks = await tasksService.getTasks();
      dispatch({ type: 'SET_TASKS', payload: tasks });

      const active = tasks.find(task =>
        ['running', 'pending', 'waiting_approval'].includes(task.status));
      // The list omits steps, so the card asks for the one task it shows.
      setActiveTask(active ? ((await tasksService.getTask(active.id)) ?? active) : null);

      const approvals = await approvalsService.getPendingApprovals();
      dispatch({ type: 'SET_APPROVAL_COUNT', payload: approvals.length });

      setOnline(true);
      setProblem('');
    } catch (error) {
      setOnline(false);
      setProblem(error instanceof Error ? error.message : 'Could not reach your computer.');
    }
  }, [dispatch]);

  useEffect(() => {
    loadData();

    // The computer pushes what it is doing, so the phone reloads when
    // something actually changed rather than asking twice a second.
    const close = openEventStream({
      types: [
        'task_created', 'task_completed', 'task_failed', 'task_cancelled',
        'step_started', 'step_finished', 'approval_requested', 'approval_resolved',
      ],
      onEvent: () => loadData(),
      onStatus: setOnline,
    });

    // A slow safety net for anything the socket missed while the phone slept.
    const interval = setInterval(loadData, 30000);

    return () => {
      close();
      clearInterval(interval);
    };
  }, [loadData]);

  const handleCommand = useCallback(async (text: string) => {
    try {
      // The computer plans the steps and starts working them straight away.
      const task = await jarvisService.processCommand(text);
      setActiveTask(task);
      dispatch({ type: 'ADD_TASK', payload: task });
      setProblem('');
      router.push(`/task/${task.id}`);
    } catch (error) {
      setProblem(
        error instanceof Error ? error.message : 'JARVIS could not start that.',
      );
    }
  }, [dispatch, router]);

  const handleQuickAction = useCallback((label: string) => {
    switch (label) {
      case 'Continue my project':
        handleCommand('Continue my Hackwave project on my laptop');
        break;
      case 'Find my files':
        handleCommand('Find my Hackwave presentation');
        break;
      case 'Check my emails':
        handleCommand('Check my emails and tell me what matters');
        break;
      case 'Research something':
        handleCommand('Research the latest AI agent frameworks and summarize them');
        break;
    }
  }, [handleCommand]);

  const handleApprove = async () => {
    if (!currentApproval) return;
    await approvalsService.approve(currentApproval.id);
    setApprovalVisible(false);
    setCurrentApproval(null);
    loadData();
  };

  const handleDeny = async () => {
    if (!currentApproval) return;
    await approvalsService.deny(currentApproval.id);
    setApprovalVisible(false);
    setCurrentApproval(null);
    loadData();
  };

  // What each of these says has to be true. A card that claims a service is
  // connected when it is not is worse than a card that admits it is not.
  const envCards = [
    {
      title: 'My Computer',
      status: online ? '● Online' : '○ Not reachable',
      color: online ? colors.primary : colors.textTertiary,
      bg: online ? colors.primaryLight : colors.surface,
      icon: 'laptop-outline',
    },
    {
      title: 'My Phone',
      status: '● Connected',
      color: colors.success,
      bg: colors.successLight,
      icon: 'phone-portrait-outline',
    },
    {
      title: 'Google Drive',
      status: googleService.isConnected() ? '● Connected' : '○ Not connected',
      color: googleService.isConnected() ? colors.warning : colors.textTertiary,
      bg: googleService.isConnected() ? colors.warningLight : colors.surface,
      icon: 'folder-outline',
    },
    {
      title: 'Internet',
      status: online ? '● Ready' : '○ Waiting',
      color: online ? '#8B5CF6' : colors.textTertiary,
      bg: online ? '#F3EEFA' : colors.surface,
      icon: 'globe-outline',
    },
  ];

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* Top Bar matching desktop reference image */}
        <View style={styles.topBar}>
          <Pressable style={styles.topBarButton} onPress={() => router.push('/(tabs)/you')}>
            <Ionicons name="menu-outline" size={24} color={colors.textPrimary} />
          </Pressable>
          <View style={styles.topBarRight}>
            <Pressable style={styles.topBarButton} onPress={() => router.push('/approvals')}>
              <Ionicons name="notifications-outline" size={22} color={colors.textPrimary} />
              {state.approvalCount > 0 && (
                <View style={styles.notificationDot} />
              )}
            </Pressable>
            <Pressable style={styles.avatarSmall} onPress={() => router.push('/(tabs)/you')}>
              <Text style={styles.avatarSmallText}>{state.user.initials}</Text>
            </Pressable>
          </View>
        </View>

        {/* Greeting Banner */}
        <View style={styles.greetingSection}>
          <Text style={styles.greeting}>☀️ {greeting},</Text>
          <Text style={styles.greetingName}>How can I help you today?</Text>
        </View>

        {/* Command Input Bar */}
        <View style={styles.inputSection}>
          <JarvisInput onSubmit={handleCommand} />

          {problem ? (
            <Pressable style={styles.problemBar} onPress={() => router.push('/connect')}>
              <Ionicons name="cloud-offline-outline" size={16} color={colors.error} />
              <Text style={styles.problemText}>
                {problem} Tap to check the connection to {getHost() || 'your computer'}.
              </Text>
            </Pressable>
          ) : null}
        </View>

        {/* Suggestion Chips */}
        <View style={styles.quickActions}>
          {suggestions.map((s) => (
            <QuickAction
              key={s.label}
              label={s.label}
              icon={s.icon}
              onPress={() => handleQuickAction(s.label)}
            />
          ))}
        </View>

        {/* Environment Status Grid (Matching reference image) */}
        <View style={styles.envGrid}>
          {envCards.map((env) => (
            <View key={env.title} style={[styles.envCard, { backgroundColor: env.bg }]}>
              <Ionicons name={env.icon as any} size={20} color={env.color} />
              <Text style={styles.envTitle}>{env.title}</Text>
              <Text style={[styles.envStatus, { color: env.color }]}>{env.status}</Text>
            </View>
          ))}
        </View>

        {/* Current Active Task Card matching reference image */}
        {activeTask && (activeTask.status === 'running' || activeTask.status === 'pending' || activeTask.status === 'waiting_approval') && (
          <View style={styles.activeTaskSection}>
            <Pressable
              style={({ pressed }) => [styles.currentTaskCard, pressed && styles.pressed]}
              onPress={() => router.push(`/task/${activeTask.id}`)}
            >
              <View style={styles.taskCardHeader}>
                <View style={styles.taskCardTag}>
                  <Ionicons name="sync-outline" size={14} color={colors.primary} />
                  <Text style={styles.taskTagText}>Current Task</Text>
                </View>
                <Pressable onPress={() => router.push(`/task/${activeTask.id}`)}>
                  <Text style={styles.viewDetailsText}>View Details ›</Text>
                </Pressable>
              </View>

              <Text style={styles.taskCardTitle}>{activeTask.title}</Text>
              <Text style={styles.taskCardSub}>{activeTask.description}</Text>

              {/* Step Timeline Pills matching reference image */}
              {activeTask.steps && activeTask.steps.length > 0 && (
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.stepsPillRow}>
                  {activeTask.steps.map((step, idx) => {
                    const isCompleted = step.status === 'completed';
                    const isRunning = step.status === 'running';
                    return (
                      <View
                        key={step.id}
                        style={[
                          styles.stepPill,
                          isCompleted ? styles.stepPillSuccess : isRunning ? styles.stepPillActive : styles.stepPillPending,
                        ]}
                      >
                        <Text
                          style={
                            isCompleted
                              ? styles.stepPillTextSuccess
                              : isRunning
                              ? styles.stepPillTextActive
                              : styles.stepPillTextPending
                          }
                        >
                          {isCompleted ? '✓' : isRunning ? '●' : '○'} {idx + 1}. {step.title}
                        </Text>
                      </View>
                    );
                  })}
                </ScrollView>
              )}
            </Pressable>
          </View>
        )}

        {/* Quick Category Navigation Cards matching reference image */}
        <View style={styles.categoriesRow}>
          <Pressable style={styles.categoryCard} onPress={() => router.push('/(tabs)/files')}>
            <Ionicons name="folder-outline" size={20} color={colors.primary} />
            <Text style={styles.catTitle}>My Files ›</Text>
            <Text style={styles.catSub}>Find and access files from any device</Text>
          </Pressable>

          <Pressable style={styles.categoryCard} onPress={() => router.push('/google' as any)}>
            <Ionicons name="logo-google" size={20} color="#4285F4" />
            <Text style={styles.catTitle}>Google ›</Text>
            <Text style={styles.catSub}>Search Drive, Gmail, Calendar & more</Text>
          </Pressable>

          <Pressable style={styles.categoryCard} onPress={() => handleCommand('Search the web for news')}>
            <Ionicons name="globe-outline" size={20} color="#8B5CF6" />
            <Text style={styles.catTitle}>Web ›</Text>
            <Text style={styles.catSub}>Search internet or do online tasks</Text>
          </Pressable>
        </View>

        {/* Natural Language Tip Banner matching reference image */}
        <View style={styles.tipBanner}>
          <Ionicons name="sparkles" size={18} color={colors.primary} />
          <View style={styles.tipContent}>
            <Text style={styles.tipTitle}>You can just ask in normal language.</Text>
            <Text style={styles.tipQuotes}>"Send this file to my phone" · "Find my last email" · "Open project folder"</Text>
          </View>
        </View>
      </ScrollView>

      {/* Approval Sheet */}
      <ApprovalSheet
        approval={currentApproval}
        visible={approvalVisible}
        onApprove={handleApprove}
        onDeny={handleDeny}
        onClose={() => setApprovalVisible(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  container: {
    flex: 1,
  },
  content: {
    paddingBottom: spacing['4xl'],
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  topBarButton: {
    padding: spacing.xs,
    position: 'relative',
  },
  topBarRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  notificationDot: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.notificationBadge,
  },
  avatarSmall: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarSmallText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textInverse,
  },
  greetingSection: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.xs,
  },
  greeting: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  greetingName: {
    ...typography.titleLarge,
    color: colors.textPrimary,
    marginTop: 2,
  },
  inputSection: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.base,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: spacing.lg,
    gap: spacing.sm,
  },
  envGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    gap: spacing.sm,
  },
  envCard: {
    width: '48%',
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    gap: 4,
    borderWidth: 1,
    borderColor: colors.border,
  },
  envTitle: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  envStatus: {
    ...typography.caption,
    fontWeight: '600',
  },
  problemBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.errorLight,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.md,
    marginTop: spacing.md,
  },
  problemText: {
    ...typography.caption,
    color: colors.error,
    flex: 1,
  },
  activeTaskSection: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
  },
  currentTaskCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  taskCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  taskCardTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  taskTagText: {
    ...typography.captionMedium,
    color: colors.primary,
  },
  viewDetailsText: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  taskCardTitle: {
    ...typography.subtitle,
    color: colors.textPrimary,
  },
  taskCardSub: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
    marginBottom: spacing.md,
  },
  stepsPillRow: {
    flexDirection: 'row',
    gap: spacing.xs,
  },
  stepPill: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: borderRadius.full,
  },
  stepPillSuccess: {
    backgroundColor: colors.successLight,
  },
  stepPillTextSuccess: {
    ...typography.labelSmall,
    color: colors.success,
  },
  stepPillActive: {
    backgroundColor: colors.primaryLight,
  },
  stepPillTextActive: {
    ...typography.labelSmall,
    color: colors.primary,
  },
  stepPillPending: {
    backgroundColor: colors.surface,
  },
  stepPillTextPending: {
    ...typography.labelSmall,
    color: colors.textTertiary,
  },
  categoriesRow: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    gap: spacing.sm,
  },
  categoryCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 2,
    ...shadows.sm,
  },
  catTitle: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
    marginTop: 4,
  },
  catSub: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  tipBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryLight,
    marginHorizontal: spacing.lg,
    marginTop: spacing.lg,
    padding: spacing.base,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: '#D0E2FF',
    gap: spacing.md,
  },
  tipContent: {
    flex: 1,
  },
  tipTitle: {
    ...typography.bodyMedium,
    color: colors.primary,
  },
  tipQuotes: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  pressed: {
    opacity: 0.75,
  },
});
