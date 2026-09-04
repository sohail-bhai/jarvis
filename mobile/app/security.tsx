import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius, shadows } from '../src/theme';
import { MenuItem } from '../src/components/MenuItem';
import { StatusBadge } from '../src/components/StatusBadge';
import { securityService } from '../src/services/security';
import { Permission, SecurityEvent } from '../src/services/types';

export default function SecurityScreen() {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [securityStatus, setSecurityStatus] = useState<{ status: string; message: string }>({ status: 'protected', message: '' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const perms = await securityService.getPermissions();
    setPermissions(perms);
    const evts = await securityService.getSecurityEvents();
    setEvents(evts);
    const status = await securityService.getSecurityStatus();
    setSecurityStatus(status);
  };

  const handleEmergencyStop = () => {
    Alert.alert(
      'Emergency Stop',
      'This will immediately stop all JARVIS operations. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Stop Everything',
          style: 'destructive',
          onPress: async () => {
            await securityService.emergencyStop();
            loadData();
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Security Status */}
      <View style={styles.statusCard}>
        <View style={[
          styles.statusIcon,
          securityStatus.status !== 'protected' && { backgroundColor: colors.errorLight }
        ]}>
          <Ionicons
            name={securityStatus.status === 'protected' ? 'shield-checkmark' : 'hand-left'}
            size={32}
            color={securityStatus.status === 'protected' ? colors.success : colors.error}
          />
        </View>
        <Text style={styles.statusTitle}>
          {securityStatus.status === 'protected' ? 'All Systems Secure' : 'Emergency Stop Active'}
        </Text>
        <StatusBadge
          label={securityStatus.status === 'protected' ? 'Protected' : 'Stopped'}
          variant={securityStatus.status === 'protected' ? 'success' : 'error'}
        />
        {securityStatus.status !== 'protected' && (
          <Pressable
            style={styles.resumeButton}
            onPress={async () => {
              await securityService.resumeFromEmergency();
              loadData();
              Alert.alert('Operations Resumed', 'JARVIS security status returned to Protected.');
            }}
          >
            <Text style={styles.resumeText}>Resume Normal Operations</Text>
          </Pressable>
        )}
      </View>

      {/* Active Permissions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Active Permissions</Text>
        {permissions.map(perm => (
          <View key={perm.id} style={styles.permRow}>
            <View style={styles.permInfo}>
              <Text style={styles.permService}>{perm.service}</Text>
              <Text style={styles.permScope}>{perm.scope}</Text>
              {perm.isTemporary && (
                <StatusBadge label="Temporary" variant="warning" dot={false} />
              )}
            </View>
            <Pressable
              onPress={async () => {
                await securityService.revokePermission(perm.id);
                loadData();
              }}
            >
              <Text style={styles.revokeText}>Revoke</Text>
            </Pressable>
          </View>
        ))}
      </View>

      {/* Recent Events */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Security Events</Text>
        {events.map(event => (
          <View key={event.id} style={styles.eventRow}>
            <Ionicons
              name={
                event.type === 'access_granted' ? 'key-outline' :
                event.type === 'access_revoked' ? 'lock-closed-outline' :
                event.type === 'sensitive_action' ? 'eye-outline' :
                'time-outline'
              }
              size={18}
              color={event.severity === 'high' ? colors.error : colors.textSecondary}
            />
            <View style={styles.eventContent}>
              <Text style={styles.eventText}>{event.description}</Text>
              <Text style={styles.eventTime}>
                {new Date(event.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
              </Text>
            </View>
          </View>
        ))}
      </View>

      {/* Emergency Stop */}
      <Pressable
        style={({ pressed }) => [styles.emergencyButton, pressed && styles.emergencyPressed]}
        onPress={handleEmergencyStop}
      >
        <Ionicons name="hand-left" size={20} color={colors.textInverse} />
        <Text style={styles.emergencyText}>Stop Everything</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  content: {
    padding: spacing.lg,
    gap: spacing.base,
    paddingBottom: spacing['4xl'],
  },
  statusCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    alignItems: 'center',
    gap: spacing.sm,
    ...shadows.sm,
  },
  statusIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.successLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statusTitle: {
    ...typography.subtitle,
    color: colors.textPrimary,
  },
  resumeButton: {
    marginTop: spacing.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  resumeText: {
    ...typography.captionMedium,
    color: colors.primary,
  },
  section: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    ...shadows.sm,
  },
  sectionTitle: {
    ...typography.subtitle,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  permRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  permInfo: {
    flex: 1,
    gap: 2,
  },
  permService: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  permScope: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  revokeText: {
    ...typography.label,
    color: colors.error,
  },
  eventRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
    paddingVertical: spacing.sm,
  },
  eventContent: {
    flex: 1,
  },
  eventText: {
    ...typography.body,
    color: colors.textPrimary,
    fontSize: 14,
  },
  eventTime: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: 2,
  },
  emergencyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.killSwitch,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.lg,
    marginTop: spacing.md,
  },
  emergencyPressed: {
    opacity: 0.85,
  },
  emergencyText: {
    ...typography.button,
    color: colors.textInverse,
  },
});
