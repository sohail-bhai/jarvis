import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, borderRadius, shadows } from '../src/theme';
import { googleService } from '../src/services/google';

export default function GoogleWorkspaceScreen() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  // Google is not wired to the control plane yet, so every answer below is an
  // example. Each one says so, because a made-up email that looks real is
  // worse than no email at all.
  const demo = googleService.isDemo;

  const handleQuickQuery = async (query: string) => {
    setLoading(true);
    const prefix = demo ? 'Example only - Google is not connected.\n\n' : '';

    if (query.includes('emails')) {
      const emails = await googleService.getImportantEmails();
      Alert.alert('Gmail', prefix + emails.map(e => `• ${e.from}: ${e.subject}`).join('\n'));
    } else if (query.includes('meetings') || query.includes('Calendar')) {
      const events = await googleService.getTodayEvents();
      Alert.alert('Calendar', prefix + events.map(e =>
        `• ${e.title} (${new Date(e.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`).join('\n'));
    } else {
      const files = await googleService.searchDrive('Hackwave');
      Alert.alert('Drive', prefix + files.map(f => `• ${f.name} (${f.size})`).join('\n'));
    }
    setLoading(false);
  };

  // No counts here: JARVIS has not looked at any of these accounts, so it has
  // nothing to count.
  const services = [
    { name: 'Google Drive', icon: 'folder-open-outline', color: '#4285F4', desc: 'Find and read your files' },
    { name: 'Gmail', icon: 'mail-outline', color: '#EA4335', desc: 'Search mail and draft replies' },
    { name: 'Google Calendar', icon: 'calendar-outline', color: '#34A853', desc: 'See and arrange your day' },
    { name: 'Google Docs', icon: 'document-text-outline', color: '#4285F4', desc: 'Write documents for you' },
    { name: 'Google Sheets', icon: 'grid-outline', color: '#34A853', desc: 'Put results into a spreadsheet' },
    { name: 'Google Slides', icon: 'easel-outline', color: '#FBBC05', desc: 'Turn work into a presentation' },
  ];

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable style={styles.backButton} onPress={() => router.back()} hitSlop={8}>
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </Pressable>
        <Text style={styles.headerTitle}>Google Workspace</Text>
        <View style={[styles.connectedBadge, demo && styles.demoBadge]}>
          <View style={[styles.connectedDot, demo && styles.demoDot]} />
          <Text style={[styles.connectedText, demo && styles.demoText]}>
            {demo ? 'Not connected' : 'Connected'}
          </Text>
        </View>
      </View>

      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {demo ? (
          <View style={styles.demoNotice}>
            <Ionicons name="information-circle-outline" size={18} color={colors.warning} />
            <Text style={styles.demoNoticeText}>
              Demo mode. Google isn't connected yet, so everything on this page is an
              example rather than your own mail, files or calendar.
            </Text>
          </View>
        ) : null}

        {/* Banner */}
        <View style={styles.bannerCard}>
          <Ionicons name="logo-google" size={28} color="#4285F4" />
          <View style={styles.bannerText}>
            <Text style={styles.bannerTitle}>JARVIS Google Control Layer</Text>
            <Text style={styles.bannerSub}>
              Ask JARVIS to search Drive, draft emails, check your schedule, or generate slides.
            </Text>
          </View>
        </View>

        {/* Quick Assistant Commands */}
        <Text style={styles.sectionTitle}>Ask JARVIS about Google Workspace</Text>
        <View style={styles.commandList}>
          <Pressable
            style={({ pressed }) => [styles.commandCard, pressed && styles.pressed]}
            onPress={() => handleQuickQuery('Find my Hackwave presentation')}
          >
            <Ionicons name="search-outline" size={18} color={colors.primary} />
            <Text style={styles.commandText}>"Find my Hackwave presentation"</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.textTertiary} />
          </Pressable>

          <Pressable
            style={({ pressed }) => [styles.commandCard, pressed && styles.pressed]}
            onPress={() => handleQuickQuery('What important emails do I have?')}
          >
            <Ionicons name="mail-unread-outline" size={18} color={colors.primary} />
            <Text style={styles.commandText}>"What important emails do I have?"</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.textTertiary} />
          </Pressable>

          <Pressable
            style={({ pressed }) => [styles.commandCard, pressed && styles.pressed]}
            onPress={() => handleQuickQuery('What meetings do I have today?')}
          >
            <Ionicons name="calendar-outline" size={18} color={colors.primary} />
            <Text style={styles.commandText}>"What meetings do I have today?"</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.textTertiary} />
          </Pressable>
        </View>

        {/* Service Grid */}
        <Text style={styles.sectionTitle}>Connected Services</Text>
        <View style={styles.servicesGrid}>
          {services.map((svc) => (
            <View key={svc.name} style={styles.serviceCard}>
              <View style={[styles.serviceIcon, { backgroundColor: `${svc.color}15` }]}>
                <Ionicons name={svc.icon as any} size={22} color={svc.color} />
              </View>
              <Text style={styles.serviceName}>{svc.name}</Text>
              <Text style={styles.serviceDesc}>{svc.desc}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  demoBadge: { backgroundColor: colors.surface },
  demoDot: { backgroundColor: colors.textTertiary },
  demoText: { color: colors.textSecondary },
  demoNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    backgroundColor: colors.warningLight,
    borderRadius: borderRadius.md,
    padding: spacing.base,
    marginBottom: spacing.base,
  },
  demoNoticeText: {
    ...typography.caption,
    color: colors.textPrimary,
    flex: 1,
  },
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    gap: spacing.md,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.title,
    color: colors.textPrimary,
    flex: 1,
  },
  connectedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.successLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: borderRadius.full,
    gap: 4,
  },
  connectedDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.success,
  },
  connectedText: {
    ...typography.labelSmall,
    color: colors.success,
  },
  container: {
    flex: 1,
  },
  content: {
    padding: spacing.lg,
    gap: spacing.xl,
  },
  bannerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: spacing.base,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.md,
  },
  bannerText: {
    flex: 1,
  },
  bannerTitle: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  bannerSub: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
    lineHeight: 18,
  },
  sectionTitle: {
    ...typography.subtitle,
    color: colors.textPrimary,
  },
  commandList: {
    gap: spacing.sm,
  },
  commandCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.card,
    padding: spacing.base,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.md,
    ...shadows.sm,
  },
  pressed: {
    backgroundColor: colors.surfaceHover,
  },
  commandText: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
    flex: 1,
  },
  servicesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  serviceCard: {
    width: '47%',
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  serviceIcon: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  serviceName: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  serviceDesc: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
});
