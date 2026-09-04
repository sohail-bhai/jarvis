import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, typography, spacing } from '../../src/theme';
import { ActivityItemComponent } from '../../src/components/ActivityItem';
import { SectionHeader } from '../../src/components/SectionHeader';
import { activityService } from '../../src/services/activity';
import { openEventStream } from '../../src/api/live';
import { toActivity } from '../../src/api/mappers';
import { ActivityEntry } from '../../src/services/types';

export default function ActivityScreen() {
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const [problem, setProblem] = useState('');

  const loadActivity = useCallback(async () => {
    try {
      setActivity(await activityService.getActivity());
      setProblem('');
    } catch (error) {
      setProblem(error instanceof Error ? error.message : 'Could not reach your computer.');
    }
  }, []);

  useEffect(() => {
    loadActivity();

    // The timeline is the one screen that should never lag behind the work,
    // so each event is added as it arrives rather than reloading the list.
    const close = openEventStream({
      onEvent: event =>
        setActivity(current => {
          const entry = toActivity(event);
          if (current.some(item => item.id === entry.id)) return current;
          return [entry, ...current].slice(0, 200);
        }),
    });

    return close;
  }, [loadActivity]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadActivity();
    setRefreshing(false);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Activity</Text>
      </View>

      {/* Section Label */}
      <SectionHeader title="Today" />

      {/* Activity List */}
      <FlatList
        data={activity}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <ActivityItemComponent entry={item} />
        )}
        refreshing={refreshing}
        onRefresh={handleRefresh}
        contentContainerStyle={styles.list}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No activity yet</Text>
            <Text style={styles.emptySubtext}>Actions JARVIS takes will appear here</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.base,
    paddingBottom: spacing.sm,
  },
  title: {
    ...typography.titleLarge,
    color: colors.textPrimary,
  },
  list: {
    flexGrow: 1,
  },
  separator: {
    height: 1,
    backgroundColor: colors.divider,
    marginLeft: 92,
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
});
