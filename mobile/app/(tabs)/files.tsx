import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../../src/theme';
import { TabSelector } from '../../src/components/TabSelector';
import { FileItemComponent } from '../../src/components/FileItem';
import { FileActionsModal } from '../../src/components/FileActionsModal';
import { filesService } from '../../src/services/files';
import { FileItem, FileSource } from '../../src/services/types';

const FILE_TABS = ['All', 'Computer', 'Phone', 'Drive'];

export default function FilesScreen() {
  const [activeTab, setActiveTab] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    loadFiles();
  }, [activeTab]);

  const loadFiles = async () => {
    const source = activeTab === 'All' ? undefined : activeTab.toLowerCase() as FileSource;
    const data = await filesService.getFiles(source);
    setFiles(data);
  };

  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      const source = activeTab === 'All' ? undefined : activeTab.toLowerCase() as FileSource;
      const results = await filesService.searchFiles(query, source);
      setFiles(results);
    } else {
      loadFiles();
    }
  }, [activeTab]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadFiles();
    setRefreshing(false);
  };

  const handleFilePress = (file: FileItem) => {
    setSelectedFile(file);
    setModalVisible(true);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      {/* Header matching Screen 3 */}
      <View style={styles.header}>
        <Text style={styles.title}>Files</Text>
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

      {/* Tab Selector */}
      <TabSelector
        tabs={FILE_TABS}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

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
            <Text style={styles.emptyText}>No files found</Text>
            <Text style={styles.emptySubtext}>Try searching for something else</Text>
          </View>
        }
      />

      {/* File Actions Modal matching Screen 7 */}
      <FileActionsModal
        file={selectedFile}
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
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
