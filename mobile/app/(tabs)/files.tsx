import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../../src/theme';
import { FileItemComponent } from '../../src/components/FileItem';
import { FileActionsModal } from '../../src/components/FileActionsModal';
import { filesService } from '../../src/services/files';
import { jarvisService } from '../../src/services/jarvis';
import { FileItem } from '../../src/services/types';

export default function FilesScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  // Empty is the top level: the folders the computer agreed to share.
  const [folder, setFolder] = useState('');
  // The folder above this one, as the computer names it. The server decides
  // this rather than the phone, so a share boundary is never crossed by
  // trimming a path locally.
  const [parent, setParent] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState('');
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const loadFiles = useCallback(async () => {
    try {
      const listing = await filesService.list(folder);
      setFiles(listing.files);
      setParent(listing.parent);
      setProblem('');
    } catch (error) {
      setFiles([]);
      setParent('');
      setProblem(error instanceof Error ? error.message : 'Could not read your files.');
    }
  }, [folder]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      loadFiles();
      return;
    }
    try {
      setFiles(await filesService.searchFiles(query));
      setProblem('');
    } catch (error) {
      setFiles([]);
      setProblem(error instanceof Error ? error.message : 'Could not search your files.');
    }
  }, [loadFiles]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadFiles();
    setRefreshing(false);
  };

  const handleFilePress = (file: FileItem) => {
    // A folder opens; anything else offers what you can do with it.
    if (file.type === 'folder') {
      setSearchQuery('');
      setFolder(file.sourcePath ?? '');
      return;
    }
    setSelectedFile(file);
    setModalVisible(true);
  };

  const goUp = () => {
    setSearchQuery('');
    setFolder(parent);
  };

  /** Send something from the phone to the folder currently open. */
  const handleUpload = async () => {
    setBusy(true);
    try {
      const saved = await filesService.uploadFromPhone(folder);
      if (saved) {
        Alert.alert('Sent to your computer', `${saved.name} is now in ${folder || 'your shared folders'}.`);
        await loadFiles();
      }
    } catch (error) {
      Alert.alert('Could not send it',
        error instanceof Error ? error.message : 'Your computer refused the file.');
    } finally {
      setBusy(false);
    }
  };

  const handleFileAction = async (action: string, file: FileItem) => {
    setBusy(true);
    try {
      if (action === 'Open') {
        await filesService.openOnPhone(file);
      } else if (action === 'Download') {
        await filesService.download(file);
        Alert.alert('Saved to this phone', `${file.name} was copied from your computer.`);
      } else if (action === 'Delete') {
        await filesService.remove(file);
        Alert.alert('Deleted', `${file.name} is gone from your computer.`);
        await loadFiles();
      } else if (action.startsWith('Ask JARVIS')) {
        await jarvisService.processCommand(`Tell me about the file ${file.sourcePath ?? file.name}`);
        Alert.alert('JARVIS is on it', `Follow it on the Tasks tab.`);
      }
    } catch (error) {
      Alert.alert(action, error instanceof Error ? error.message
        : 'Your computer could not do that.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      {/* Header matching Screen 3 */}
      <View style={styles.header}>
        <Text style={styles.title}>Files</Text>
        <TouchableOpacity style={styles.uploadButton} onPress={handleUpload} disabled={busy}>
          {busy
            ? <ActivityIndicator size="small" color={colors.primary} />
            : <Ionicons name="cloud-upload-outline" size={20} color={colors.primary} />}
          <Text style={styles.uploadLabel}>Send</Text>
        </TouchableOpacity>
      </View>

      {/* Search Bar with Filter Icon */}
      <View style={styles.searchContainer}>
        <Ionicons name="search-outline" size={18} color={colors.textTertiary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search your files..."
          placeholderTextColor={colors.textTertiary}
          value={searchQuery}
          onChangeText={handleSearch}
          returnKeyType="search"
        />
        <Ionicons name="options-outline" size={18} color={colors.textSecondary} />
      </View>

      {/* Where you are, and the way back out of it */}
      {folder && !searchQuery ? (
        <TouchableOpacity style={styles.crumb} onPress={goUp} disabled={!parent}>
          <Ionicons name="chevron-back" size={16} color={colors.primary} />
          <Text style={styles.crumbText} numberOfLines={1}>
            {folder}
          </Text>
        </TouchableOpacity>
      ) : null}

      {problem ? <Text style={styles.problem}>{problem}</Text> : null}

      {/* File List */}
      <FlatList
        data={files}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <FileItemComponent
            file={item}
            onPress={() => handleFilePress(item)}
            onMore={() => handleFilePress(item)}
          />
        )}
        refreshing={refreshing}
        onRefresh={handleRefresh}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="folder-open-outline" size={48} color={colors.textTertiary} />
            <Text style={styles.emptyText}>Nothing here</Text>
            <Text style={styles.emptySubtext}>
              {searchQuery
                ? 'No file matches that name.'
                : 'Your computer shares folders with JARVIS. Add some in its settings.'}
            </Text>
          </View>
        }
      />

      {/* File Actions Modal matching Screen 7 */}
      <FileActionsModal
        file={selectedFile}
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        onAction={handleFileAction}
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.base,
    paddingBottom: spacing.sm,
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  uploadLabel: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '600',
  },
  title: {
    ...typography.titleLarge,
    color: colors.textPrimary,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    marginHorizontal: spacing.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.sm,
  },
  searchInput: {
    flex: 1,
    ...typography.body,
    color: colors.textPrimary,
    padding: 0,
  },
  crumb: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  crumbText: {
    ...typography.caption,
    color: colors.primary,
    flex: 1,
  },
  problem: {
    ...typography.caption,
    color: colors.error,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
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
});
