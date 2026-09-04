import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, Pressable, Modal, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, borderRadius, shadows } from '../src/theme';
import { DeviceItemComponent } from '../src/components/DeviceItem';
import { devicesService } from '../src/services/devices';
import { Device } from '../src/services/types';

export default function DevicesScreen() {
  const router = useRouter();
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      setDevices(await devicesService.getDevices());
    } catch (error) {
      setDevices([]);
      Alert.alert(
        'Could not reach JARVIS',
        error instanceof Error ? error.message : 'Your computer did not answer.',
      );
    }
  };

  const handleDevicePress = (device: Device) => {
    setSelectedDevice(device);
    setModalVisible(true);
  };

  const handleAction = async (action: string) => {
    if (!selectedDevice) return;
    setModalVisible(false);
    if (action === 'Send task') {
      router.push(`/(tabs)?prompt=Send task to ${selectedDevice.name}`);
    } else if (action === 'Send file') {
      router.push('/(tabs)/files');
    } else if (action === 'View status') {
      Alert.alert(
        `${selectedDevice.name} Status`,
        `OS: ${selectedDevice.os}\nStatus: ${selectedDevice.status}\nCapabilities: ${(selectedDevice.capabilities || []).join(', ')}`
      );
    } else {
      // Nothing behind this yet, so it must not claim the action happened.
      Alert.alert(
        action,
        `JARVIS cannot do this on ${selectedDevice.name} yet.`,
      );
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      {/* Header matching Screen 9 */}
      <View style={styles.header}>
        <Pressable style={styles.backButton} onPress={() => router.back()} hitSlop={8}>
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </Pressable>
        <Text style={styles.headerTitle}>My Devices</Text>
        <Pressable
          style={styles.addButton}
          onPress={() => Alert.alert('Add Device', 'Searching for local JARVIS agents & devices on your Wi-Fi network...')}
          hitSlop={8}
        >
          <Ionicons name="add" size={24} color={colors.primary} />
        </Pressable>
      </View>

      {/* Device List */}
      <FlatList
        data={devices}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <DeviceItemComponent device={item} onPress={() => handleDevicePress(item)} />
        )}
        contentContainerStyle={styles.list}
      />

      {/* Device Actions Modal */}
      {selectedDevice && (
        <Modal
          visible={modalVisible}
          transparent
          animationType="fade"
          onRequestClose={() => setModalVisible(false)}
        >
          <Pressable style={styles.overlay} onPress={() => setModalVisible(false)}>
            <Pressable style={styles.modalCard} onPress={e => e.stopPropagation()}>
              <View style={styles.modalHeader}>
                <Ionicons
                  name={selectedDevice.type === 'laptop' ? 'laptop-outline' : selectedDevice.type === 'phone' ? 'phone-portrait-outline' : 'desktop-outline'}
                  size={24}
                  color={colors.primary}
                />
                <View style={styles.modalTitleBox}>
                  <Text style={styles.modalTitle}>{selectedDevice.name}</Text>
                  <Text style={styles.modalSub}>{selectedDevice.os} · {selectedDevice.status.toUpperCase()}</Text>
                </View>
                <Pressable onPress={() => setModalVisible(false)}>
                  <Ionicons name="close" size={20} color={colors.textSecondary} />
                </Pressable>
              </View>

              <View style={styles.divider} />

              <Pressable style={styles.actionRow} onPress={() => handleAction('Send task')}>
                <Ionicons name="flash-outline" size={18} color={colors.primary} />
                <Text style={styles.actionText}>Send task to device</Text>
              </Pressable>

              <Pressable style={styles.actionRow} onPress={() => handleAction('Send file')}>
                <Ionicons name="document-text-outline" size={18} color={colors.textPrimary} />
                <Text style={styles.actionText}>Send file to device</Text>
              </Pressable>

              <Pressable style={styles.actionRow} onPress={() => handleAction('View status')}>
                <Ionicons name="information-circle-outline" size={18} color={colors.textPrimary} />
                <Text style={styles.actionText}>View hardware capabilities</Text>
              </Pressable>
            </Pressable>
          </Pressable>
        </Modal>
      )}
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
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.title,
    color: colors.textPrimary,
  },
  addButton: {
    padding: spacing.xs,
  },
  list: {
    flexGrow: 1,
  },
  overlay: {
    flex: 1,
    backgroundColor: colors.overlay,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  modalCard: {
    width: '100%',
    backgroundColor: colors.card,
    borderRadius: borderRadius.xl,
    padding: spacing.xl,
    ...shadows.xl,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  modalTitleBox: {
    flex: 1,
  },
  modalTitle: {
    ...typography.subtitle,
    color: colors.textPrimary,
  },
  modalSub: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: colors.divider,
    marginVertical: spacing.md,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    gap: spacing.md,
  },
  actionText: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
});
