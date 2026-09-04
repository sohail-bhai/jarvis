import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, borderRadius } from '../../src/theme';
import { ProfileCard } from '../../src/components/ProfileCard';
import { MenuItem } from '../../src/components/MenuItem';
import { useAppState } from '../../src/store/AppContext';
import { devicesService } from '../../src/services/devices';
import { approvalsService } from '../../src/services/approvals';

export default function YouScreen() {
  const router = useRouter();
  const { state, dispatch } = useAppState();
  const [deviceCount, setDeviceCount] = useState(0);
  const [approvalCount, setApprovalCount] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const count = await devicesService.getOnlineCount();
    setDeviceCount(count);
    const aCount = await approvalsService.getApprovalCount();
    setApprovalCount(aCount);
    dispatch({ type: 'SET_APPROVAL_COUNT', payload: aCount });
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        {/* Header matching Screen 5 */}
        <View style={styles.header}>
          <Text style={styles.title}>You</Text>
          <Pressable
            style={styles.settingsButton}
            onPress={() => Alert.alert('Settings', 'JARVIS App Version 1.2\nConnected to Local AI Brain & Desktop Assistant')}
            hitSlop={8}
          >
            <Ionicons name="settings-outline" size={22} color={colors.textSecondary} />
          </Pressable>
        </View>

        {/* Profile Card */}
        <ProfileCard
          name={state.user.name}
          initials={state.user.initials}
          workspace={state.user.workspace}
        />

        {/* Divider */}
        <View style={styles.divider} />

        {/* Menu Items matching Screen 5 */}
        <MenuItem
          icon="laptop-outline"
          label="My Devices"
          value={`${deviceCount} connected`}
          onPress={() => router.push('/devices')}
        />
        <MenuItem
          icon="logo-google"
          iconColor="#4285F4"
          label="Google Workspace"
          value="Connected"
          onPress={() => router.push('/google' as any)}
        />
        <MenuItem
          icon="shield-checkmark-outline"
          label="Approvals"
          badge={approvalCount}
          onPress={() => router.push('/approvals')}
        />
        <MenuItem
          icon="airplane-outline"
          label="While I'm Away"
          value="Configure"
          onPress={() => router.push('/away' as any)}
        />
        <MenuItem
          icon="lock-closed-outline"
          label="Your Security"
          value="Protected"
          onPress={() => router.push('/security')}
        />

        {/* Section Divider */}
        <View style={styles.sectionDivider} />

        <MenuItem
          icon="link-outline"
          label="Connected Services"
          value="3 services"
          onPress={() => Alert.alert('Connected Services', '• Python Local Desktop Assistant\n• Google Workspace API\n• Telegram Notification Relay')}
        />
        <MenuItem
          icon="cog-outline"
          label="Settings"
          onPress={() => Alert.alert('Settings', 'Theme: Light (Restrained)\nNotification Level: High Priority Only\nOffline Fail-safe: Enabled')}
        />
        <MenuItem
          icon="help-circle-outline"
          label="Help & Feedback"
          onPress={() => Alert.alert('Help & Feedback', 'JARVIS Personal Control Plane.\nControl, delegate, and get things done from anywhere.')}
        />
      </ScrollView>
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
  settingsButton: {
    padding: spacing.xs,
  },
  divider: {
    height: 1,
    backgroundColor: colors.divider,
    marginHorizontal: spacing.lg,
  },
  sectionDivider: {
    height: 8,
    backgroundColor: colors.surface,
    marginVertical: spacing.sm,
  },
});
