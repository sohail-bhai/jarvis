import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing } from '../theme';
import { Device } from '../services/types';

interface DeviceItemProps {
  device: Device;
  onPress?: () => void;
}

function getDeviceIcon(type: Device['type']): string {
  switch (type) {
    case 'laptop': return 'laptop-outline';
    case 'desktop': return 'desktop-outline';
    case 'phone': return 'phone-portrait-outline';
    case 'server': return 'server-outline';
    case 'tablet': return 'tablet-portrait-outline';
    default: return 'hardware-chip-outline';
  }
}

function getStatusColor(status: Device['status']): string {
  switch (status) {
    case 'online': return colors.success;
    case 'connected': return colors.primary;
    case 'offline': return colors.textTertiary;
    default: return colors.textTertiary;
  }
}

function getStatusLabel(status: Device['status']): string {
  switch (status) {
    case 'online': return 'Online';
    case 'connected': return 'Connected';
    case 'offline': return 'Offline';
    default: return status;
  }
}

export function DeviceItemComponent({ device, onPress }: DeviceItemProps) {
  const statusColor = getStatusColor(device.status);

  return (
    <Pressable
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}
      onPress={onPress}
    >
      <Ionicons name={getDeviceIcon(device.type) as any} size={22} color={colors.textSecondary} />
      <Text style={styles.name}>{device.name}</Text>
      <View style={styles.statusContainer}>
        <View style={[styles.dot, { backgroundColor: statusColor }]} />
        <Text style={[styles.status, { color: statusColor }]}>{getStatusLabel(device.status)}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.base,
    gap: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  pressed: {
    backgroundColor: colors.surfaceHover,
  },
  name: {
    ...typography.body,
    color: colors.textPrimary,
    flex: 1,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  status: {
    ...typography.caption,
  },
});
