import React from 'react';
import { View, Text, StyleSheet, Pressable, Modal, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';
import { FileItem } from '../services/types';

interface FileActionsModalProps {
  file: FileItem | null;
  visible: boolean;
  onClose: () => void;
  onAction?: (actionName: string, file: FileItem) => void;
}

export function FileActionsModal({ file, visible, onClose, onAction }: FileActionsModalProps) {
  if (!file) return null;

  const handleAction = (actionName: string) => {
    onClose();
    if (onAction) {
      onAction(actionName, file);
    } else {
      Alert.alert(actionName, `${actionName} performed on ${file.name}`);
    }
  };

  const getFileIcon = (type: FileItem['type']) => {
    switch (type) {
      case 'presentation': return { name: 'easel', color: '#E85D4A', bg: '#FDEEEC' };
      case 'pdf': return { name: 'document-text', color: '#E85D4A', bg: '#FDEEEC' };
      case 'document': return { name: 'document', color: '#3B7DDD', bg: '#EBF2FC' };
      case 'spreadsheet': return { name: 'grid', color: '#4CAF6E', bg: '#EDF7F0' };
      case 'archive': return { name: 'archive', color: '#6B7B94', bg: '#F0F2F5' };
      default: return { name: 'document-outline', color: '#6B7B94', bg: '#F0F2F5' };
    }
  };

  const iconInfo = getFileIcon(file.type);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <Pressable style={styles.overlay} onPress={onClose}>
        <Pressable style={styles.sheet} onPress={e => e.stopPropagation()}>
          {/* Header */}
          <View style={styles.header}>
            <View style={[styles.fileIconBox, { backgroundColor: iconInfo.bg }]}>
              <Ionicons name={iconInfo.name as any} size={24} color={iconInfo.color} />
            </View>
            <View style={styles.headerTitleBox}>
              <Text style={styles.fileName} numberOfLines={1}>{file.name}</Text>
              <Text style={styles.fileSub}>{file.type.toUpperCase()} · {file.size}</Text>
            </View>
            <Pressable style={styles.closeButton} onPress={onClose} hitSlop={8}>
              <Ionicons name="close" size={22} color={colors.textSecondary} />
            </Pressable>
          </View>

          <View style={styles.divider} />

          {/* Action List matching Reference Image Screen 7 */}
          <View style={styles.actionList}>
            <Pressable
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
              onPress={() => handleAction('Open')}
            >
              <Ionicons name="open-outline" size={20} color={colors.textPrimary} />
              <Text style={styles.actionLabel}>Open</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
              onPress={() => handleAction('Send to my laptop')}
            >
              <Ionicons name="laptop-outline" size={20} color={colors.textPrimary} />
              <Text style={styles.actionLabel}>Send to my laptop</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
              onPress={() => handleAction('Share')}
            >
              <Ionicons name="share-outline" size={20} color={colors.textPrimary} />
              <Text style={styles.actionLabel}>Share</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
              onPress={() => handleAction('Download')}
            >
              <Ionicons name="download-outline" size={20} color={colors.textPrimary} />
              <Text style={styles.actionLabel}>Download</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
              onPress={() => handleAction('Ask JARVIS about this file')}
            >
              <Ionicons name="sparkles-outline" size={20} color={colors.primary} />
              <Text style={[styles.actionLabel, { color: colors.primary }]}>Ask JARVIS about this file</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
              onPress={() => handleAction('View in Drive')}
            >
              <Ionicons name="logo-google" size={20} color={colors.textPrimary} />
              <Text style={styles.actionLabel}>View in Drive</Text>
            </Pressable>

            <View style={styles.divider} />

            <Pressable
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
              onPress={() => handleAction('Delete')}
            >
              <Ionicons name="trash-outline" size={20} color={colors.error} />
              <Text style={[styles.actionLabel, { color: colors.error }]}>Delete</Text>
            </Pressable>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: colors.overlay,
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: colors.background,
    borderTopLeftRadius: borderRadius['2xl'],
    borderTopRightRadius: borderRadius['2xl'],
    paddingTop: spacing.lg,
    paddingBottom: spacing['3xl'],
    paddingHorizontal: spacing.lg,
    ...shadows.xl,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
    gap: spacing.md,
  },
  fileIconBox: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitleBox: {
    flex: 1,
  },
  fileName: {
    ...typography.subtitle,
    color: colors.textPrimary,
  },
  fileSub: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  closeButton: {
    padding: spacing.xs,
    borderRadius: borderRadius.full,
    backgroundColor: colors.surface,
  },
  divider: {
    height: 1,
    backgroundColor: colors.divider,
    marginVertical: spacing.sm,
  },
  actionList: {
    gap: 2,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
    borderRadius: borderRadius.md,
    gap: spacing.md,
  },
  pressed: {
    backgroundColor: colors.surfaceHover,
  },
  actionLabel: {
    ...typography.body,
    color: colors.textPrimary,
    fontWeight: '500',
  },
});
