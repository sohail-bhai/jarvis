import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../theme';
import { FileItem as FileItemType } from '../services/types';
import { filesService } from '../services/files';

interface FileItemProps {
  file: FileItemType;
  onPress?: () => void;
  onMore?: () => void;
}

function getFileIcon(type: FileItemType['type']): { name: string; bg: string; color: string } {
  switch (type) {
    case 'presentation':
      return { name: 'easel', bg: '#FDEEEC', color: '#E85D4A' };
    case 'pdf':
      return { name: 'document-text', bg: '#FDEEEC', color: '#E85D4A' };
    case 'document':
      return { name: 'document', bg: '#EBF2FC', color: '#3B7DDD' };
    case 'spreadsheet':
      return { name: 'grid', bg: '#EDF7F0', color: '#4CAF6E' };
    case 'archive':
      return { name: 'archive', bg: '#F0F2F5', color: '#6B7B94' };
    case 'image':
      return { name: 'image', bg: '#FEF6E8', color: '#F5A623' };
    case 'code':
      return { name: 'code-slash', bg: '#F3EEFA', color: '#8B5CF6' };
    default:
      return { name: 'document-outline', bg: '#F0F2F5', color: '#6B7B94' };
  }
}

export function FileItemComponent({ file, onPress, onMore }: FileItemProps) {
  const icon = getFileIcon(file.type);

  return (
    <Pressable
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}
      onPress={onPress}
    >
      <View style={[styles.iconContainer, { backgroundColor: icon.bg }]}>
        <Ionicons name={icon.name as any} size={20} color={icon.color} />
      </View>
      <View style={styles.content}>
        <Text style={styles.name} numberOfLines={1}>{file.name}</Text>
        <Text style={styles.meta} numberOfLines={1}>
          {file.sourcePath ? `${file.sourcePath}` : file.source}
          {file.modifiedRelative ? ` · ${file.modifiedRelative}` : ''}
        </Text>
      </View>
      <Pressable onPress={onMore} style={styles.moreButton} hitSlop={8}>
        <Ionicons name="ellipsis-horizontal" size={18} color={colors.textTertiary} />
      </Pressable>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    gap: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  pressed: {
    backgroundColor: colors.surfaceHover,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
  },
  name: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  meta: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  moreButton: {
    padding: spacing.xs,
  },
});
