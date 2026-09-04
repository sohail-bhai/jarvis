import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius, shadows } from '../../src/theme';
import { ProgressBar } from '../../src/components/ProgressBar';
import { tasksService } from '../../src/services/tasks';
import { openEventStream } from '../../src/api/live';
import { Task, TaskStep } from '../../src/services/types';

function getStepIcon(status: TaskStep['status']): { name: string; color: string } {
  switch (status) {
    case 'completed':
      return { name: 'checkmark-circle', color: colors.success };
    case 'running':
      return { name: 'sync-circle', color: colors.primary };
    case 'failed':
      return { name: 'close-circle', color: colors.error };
    default:
      return { name: 'ellipse-outline', color: colors.textTertiary };
  }
}

export default function TaskDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [task, setTask] = useState<Task | null>(null);
  const [problem, setProblem] = useState('');

  const loadTask = useCallback(async () => {
    if (!id) return;
    try {
      const data = await tasksService.getTask(id);
      if (data) setTask(data);
      setProblem('');
    } catch (error) {
      setProblem(error instanceof Error ? error.message : 'Could not reach your computer.');
    }
  }, [id]);

  useEffect(() => {
    loadTask();

    // Follow this one task as the computer works it, rather than asking the
    // computer for it twice a second.
    const close = openEventStream({
      taskId: id,
      onEvent: () => loadTask(),
    });

    // A slow reload covers whatever the socket missed while the phone slept.
    const interval = setInterval(loadTask, 20000);

    return () => {
      close();
      clearInterval(interval);
    };
  }, [id, loadTask]);

  const handleCancel = async () => {
    if (!id) return;
    try {
      await tasksService.cancelTask(id);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : 'Could not stop the task.');
    }
    // Show what the computer actually did, not what was asked for.
    loadTask();
  };

  if (!task) {
    return (
      <View style={styles.pending}>
        <Text style={styles.pendingText}>
          {problem || 'Loading this task...'}
        </Text>
      </View>
    );
  }

  const isActive = task.status === 'running' || task.status === 'pending' || task.status === 'waiting_approval';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Task Header */}
      <View style={styles.headerCard}>
        <Text style={styles.taskTitle}>{task.title}</Text>
        <Text style={styles.taskDescription}>{task.description}</Text>

        {isActive && (
          <View style={styles.progressSection}>
            <ProgressBar progress={task.progress} height={8} showLabel />
          </View>
        )}

        {task.status === 'completed' && task.result && (
          <View style={styles.resultBanner}>
            <Ionicons name="checkmark-circle" size={20} color={colors.success} />
            <Text style={styles.resultText}>{task.result}</Text>
          </View>
        )}

        {task.status === 'cancelled' && (
          <View style={styles.cancelledBanner}>
            <Ionicons name="ban-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.cancelledText}>{task.error || 'This task was cancelled by user.'}</Text>
          </View>
        )}

        {task.status === 'failed' && task.error && (
          <View style={styles.errorBanner}>
            <Ionicons name="close-circle" size={20} color={colors.error} />
            <Text style={styles.errorText}>{task.error}</Text>
          </View>
        )}
      </View>

      {/* Steps Timeline */}
      {task.steps.length > 0 && (
        <View style={styles.stepsSection}>
          <Text style={styles.stepsTitle}>Progress</Text>
          {task.steps.map((step, index) => {
            const icon = getStepIcon(step.status);
            const isLast = index === task.steps.length - 1;

            return (
              <View key={step.id} style={styles.stepRow}>
                {/* Timeline line */}
                <View style={styles.stepTimeline}>
                  <Ionicons name={icon.name as any} size={22} color={icon.color} />
                  {!isLast && <View style={styles.timelineLine} />}
                </View>

                {/* Step content */}
                <View style={styles.stepContent}>
                  <Text style={[
                    styles.stepTitle,
                    step.status === 'pending' && styles.stepTitlePending,
                  ]}>
                    {step.title}
                  </Text>
                  {step.agentName && (
                    <Text style={styles.stepAgent}>{step.agentName}</Text>
                  )}
                  {step.completedAt && (
                    <Text style={styles.stepTime}>{step.completedAt}</Text>
                  )}
                </View>
              </View>
            );
          })}
        </View>
      )}

      {/* Actions */}
      {isActive && (
        <View style={styles.actionsSection}>
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={handleCancel}
            activeOpacity={0.6}
            hitSlop={{ top: 20, bottom: 20, left: 30, right: 30 }}
          >
            <Ionicons name="stop-circle-outline" size={20} color={colors.error} />
            <Text style={styles.cancelText}>Cancel Task</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  pending: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    backgroundColor: colors.background,
  },
  pendingText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  content: {
    padding: spacing.lg,
    gap: spacing.base,
    paddingBottom: spacing['4xl'],
  },
  headerCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    ...shadows.sm,
  },
  taskTitle: {
    ...typography.title,
    color: colors.textPrimary,
  },
  taskDescription: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  progressSection: {
    marginTop: spacing.base,
  },
  resultBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.successLight,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginTop: spacing.base,
    gap: spacing.sm,
  },
  resultText: {
    ...typography.body,
    color: colors.success,
    flex: 1,
  },
  cancelledBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginTop: spacing.base,
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cancelledText: {
    ...typography.body,
    color: colors.textSecondary,
    flex: 1,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.errorLight,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginTop: spacing.base,
    gap: spacing.sm,
  },
  errorText: {
    ...typography.body,
    color: colors.error,
    flex: 1,
  },
  stepsSection: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    ...shadows.sm,
  },
  stepsTitle: {
    ...typography.subtitle,
    color: colors.textPrimary,
    marginBottom: spacing.base,
  },
  stepRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  stepTimeline: {
    alignItems: 'center',
    width: 24,
  },
  timelineLine: {
    width: 2,
    flex: 1,
    backgroundColor: colors.border,
    marginVertical: 4,
    minHeight: 24,
  },
  stepContent: {
    flex: 1,
    paddingBottom: spacing.base,
  },
  stepTitle: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  stepTitlePending: {
    color: colors.textTertiary,
  },
  stepAgent: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  stepTime: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: 1,
  },
  actionsSection: {
    alignItems: 'center',
    paddingTop: spacing.base,
  },
  cancelButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.errorLight,
    backgroundColor: colors.card,
  },
  pressed: {
    opacity: 0.7,
  },
  cancelText: {
    ...typography.label,
    color: colors.error,
  },
});
