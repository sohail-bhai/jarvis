import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, Pressable, Modal, TextInput, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, borderRadius, shadows } from '../../src/theme';
import { TabSelector } from '../../src/components/TabSelector';
import { TaskCard } from '../../src/components/TaskCard';
import { tasksService } from '../../src/services/tasks';
import { jarvisService } from '../../src/services/jarvis';
import { useAppState } from '../../src/store/AppContext';
import { Task } from '../../src/services/types';

export default function TasksScreen() {
  const router = useRouter();
  const { dispatch } = useAppState();
  const [activeTab, setActiveTab] = useState('Active');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, 1500);
    return () => clearInterval(interval);
  }, [activeTab]);

  const loadTasks = async () => {
    if (activeTab === 'Active') {
      const data = await tasksService.getActiveTasks();
      setTasks(data);
    } else {
      const data = await tasksService.getCompletedTasks();
      setTasks(data);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadTasks();
    setRefreshing(false);
  };

  const handleCreateTask = async () => {
    if (!newTaskTitle.trim()) {
      Alert.alert('Empty Command', 'Please enter a task description.');
      return;
    }
    const task = await jarvisService.processCommand(newTaskTitle);
    dispatch({ type: 'ADD_TASK', payload: task });
    setCreateModalVisible(false);
    setNewTaskTitle('');
    loadTasks();
    router.push(`/task/${task.id}`);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Tasks</Text>
        <Pressable
          style={styles.addButton}
          onPress={() => setCreateModalVisible(true)}
          hitSlop={8}
        >
          <Ionicons name="add" size={24} color={colors.primary} />
        </Pressable>
      </View>

      {/* Tab Selector matching Screen 2 */}
      <TabSelector
        tabs={['Active', 'Completed']}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Task List */}
      <FlatList
        data={tasks}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <TaskCard
            task={item}
            onPress={() => router.push(`/task/${item.id}`)}
          />
        )}
        refreshing={refreshing}
        onRefresh={handleRefresh}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="checkmark-done-circle-outline" size={48} color={colors.textTertiary} />
            <Text style={styles.emptyText}>
              {activeTab === 'Active' ? 'No active tasks' : 'No completed tasks'}
            </Text>
            <Text style={styles.emptySubtext}>
              {activeTab === 'Active' ? 'Ask JARVIS to do something!' : 'Tasks will appear here when finished.'}
            </Text>
          </View>
        }
      />

      {/* Create Task Modal */}
      <Modal
        visible={createModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setCreateModalVisible(false)}
      >
        <Pressable style={styles.overlay} onPress={() => setCreateModalVisible(false)}>
          <Pressable style={styles.modalCard} onPress={e => e.stopPropagation()}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>New JARVIS Task</Text>
              <Pressable onPress={() => setCreateModalVisible(false)}>
                <Ionicons name="close" size={20} color={colors.textSecondary} />
              </Pressable>
            </View>

            <TextInput
              style={styles.taskInput}
              placeholder="What would you like JARVIS to do?"
              placeholderTextColor={colors.textTertiary}
              value={newTaskTitle}
              onChangeText={setNewTaskTitle}
              autoFocus
            />

            <View style={styles.modalActions}>
              <Pressable
                style={styles.cancelBtn}
                onPress={() => setCreateModalVisible(false)}
              >
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </Pressable>
              <Pressable
                style={styles.submitBtn}
                onPress={handleCreateTask}
              >
                <Text style={styles.submitBtnText}>Start Task</Text>
              </Pressable>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
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
    paddingTop: spacing.base,
    paddingBottom: spacing.sm,
  },
  title: {
    ...typography.titleLarge,
    color: colors.textPrimary,
  },
  addButton: {
    padding: spacing.xs,
  },
  list: {
    flexGrow: 1,
  },
  empty: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 80,
    gap: spacing.sm,
  },
  emptyText: {
    ...typography.subtitle,
    color: colors.textSecondary,
  },
  emptySubtext: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  overlay: {
    flex: 1,
    backgroundColor: colors.overlay,
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: colors.background,
    borderTopLeftRadius: borderRadius['2xl'],
    borderTopRightRadius: borderRadius['2xl'],
    padding: spacing.xl,
    gap: spacing.md,
    ...shadows.xl,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalTitle: {
    ...typography.title,
    color: colors.textPrimary,
  },
  taskInput: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    ...typography.body,
    color: colors.textPrimary,
    borderWidth: 1,
    borderColor: colors.border,
  },
  modalActions: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  cancelBtn: {
    flex: 1,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surface,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  submitBtn: {
    flex: 1,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
  },
  cancelBtnText: {
    ...typography.button,
    color: colors.textSecondary,
  },
  submitBtnText: {
    ...typography.button,
    color: colors.textInverse,
  },
});
