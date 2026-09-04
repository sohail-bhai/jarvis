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
import { useGoogleStatus } from '../../src/services/useGoogleStatus';
import { securityService } from '../../src/services/security';
import { sessionService } from '../../src/api/session';
import { getHost } from '../../src/api/client';

export default function YouScreen() {
  const router = useRouter();
  const { state, dispatch } = useAppState();
  const [deviceCount, setDeviceCount] = useState(0);
  const [approvalCount, setApprovalCount] = useState(0);
  const [reachable, setReachable] = useState(false);
  const [securityLine, setSecurityLine] = useState('');
  const google = useGoogleStatus();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setDeviceCount(await devicesService.getOnlineCount());

      const pending = await approvalsService.getPendingApprovals();
      setApprovalCount(pending.length);
      dispatch({ type: 'SET_APPROVAL_COUNT', payload: pending.length });

      const security = await securityService.getSecurityStatus();
      setSecurityLine(security.stopped ? 'Everything stopped' : 'Protected');
      setReachable(true);
    } catch {
      // Say nothing rather than something untrue: the computer is not
      // answering, so these numbers are unknown, not zero.
      setReachable(false);
      setSecurityLine('');
    }
  };

  const disconnect = () => {
    Alert.alert(
      'Disconnect this phone?',
      'JARVIS keeps working on your computer. This phone will need a new code to connect again.',
      [
        { text: 'Not now', style: 'cancel' },
        {
          text: 'Disconnect',
          style: 'destructive',
          onPress: async () => {
            await sessionService.disconnect();
            router.replace('/connect');
          },
        },
      ],
    );
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        {/* Header matching Screen 5 */}
        <View style={styles.header}>
          <Text style={styles.title}>You</Text>
          <Pressable
            style={styles.settingsButton}
            onPress={() => Alert.alert(
              'Settings',
              `JARVIS on your phone, version 1.2.\n\nConnected to ${getHost() || 'no computer yet'}.`,
            )}
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

        {/* Which computer this phone belongs to */}
        <MenuItem
          icon="desktop-outline"
          label="Your computer"
          value={reachable ? getHost().replace(/^https?:\/\//, '') : 'Not reachable'}
          onPress={() => router.push('/devices')}
        />
        <MenuItem
          icon="laptop-outline"
          label="My Devices"
          value={reachable ? `${deviceCount} connected` : 'Unknown'}
          onPress={() => router.push('/devices')}
        />
        <MenuItem
          icon="logo-google"
          iconColor="#4285F4"
          label="Google Workspace"
          value={google.loading ? 'Checking' : google.connected ? 'Connected' : 'Not connected'}
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
          value={securityLine || 'Unknown'}
          onPress={() => router.push('/security')}
        />

        {/* Section Divider */}
        <View style={styles.sectionDivider} />

        <MenuItem
          icon="link-outline"
          label="Connected Services"
          value={google.connected ? '2 connected' : '1 connected'}
          onPress={() => Alert.alert(
            'Connected Services',
            `• Your computer${reachable ? '' : ' (not reachable right now)'}\n` +
            `• Google Workspace${google.connected ? '' : ' - not connected yet'}`,
          )}
        />
        <MenuItem
          icon="log-out-outline"
          label="Disconnect this phone"
          onPress={disconnect}
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
