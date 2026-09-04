import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, borderRadius, shadows } from '../src/theme';
import { googleService } from '../src/services/google';
import { useGoogleStatus } from '../src/services/useGoogleStatus';

export default function GoogleWorkspaceScreen() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  // The computer holds the Google token and says whether it works. Until it
  // does, every answer below is an example and is labelled as one, because a
  // made-up email that looks real is worse than no email at all.
  const google = useGoogleStatus();
  const demo = google.demo;

  const handleQuickQuery = async (query: string) => {
    setLoading(true);
    try {
      if (query.includes('emails')) {
        const answer = await googleService.getImportantEmails();
        Alert.alert('Gmail', describe(answer.live, answer.notice,
          answer.items.map(e => `• ${e.from}: ${e.subject}`),
          'No unread mail.'));
      } else if (query.includes('meetings') || query.includes('Calendar')) {
        const answer = await googleService.getTodayEvents();
        Alert.alert('Calendar', describe(answer.live, answer.notice,
          answer.items.map(e => `• ${e.title} (${formatTime(e.startTime)})`),
          'Nothing on your calendar today.'));
      } else {
        const answer = await googleService.searchDrive('Hackwave');
        Alert.alert('Drive', describe(answer.live, answer.notice,
          answer.items.map(f => `• ${f.name}${f.size ? ` (${f.size})` : ''}`),
          'No matching files.'));
      }
    } catch (error) {
      Alert.alert('Google', error instanceof Error ? error.message
        : 'JARVIS could not reach your computer.');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    if (google.connected) {
      Alert.alert('Google', `Connected as ${google.status?.account || 'your account'}.`);
      return;
    }
    setLoading(true);
    try {
      const started = await googleService.connect();
      Alert.alert('Connect Google', started.detail);
      await google.refresh();
    } catch (error) {
      Alert.alert('Connect Google', error instanceof Error ? error.message
        : 'JARVIS could not start the Google sign-in.');
    } finally {
      setLoading(false);
    }
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
              Demo mode. Everything on this page is an example rather than your own
              mail, files or calendar. {google.detail}
            </Text>
          </View>
        ) : null}

        {/* Connect, or say who is connected */}
        <Pressable
          style={({ pressed }) => [styles.connectCard, pressed && styles.pressed]}
          onPress={handleConnect}
          disabled={loading}
        >
          <Ionicons
            name={google.connected ? 'checkmark-circle' : 'log-in-outline'}
            size={22}
            color={google.connected ? colors.success : colors.primary}
          />
          <View style={styles.bannerText}>
            <Text style={styles.bannerTitle}>
              {google.connected ? 'Google is connected' : 'Connect your Google account'}
            </Text>
            <Text style={styles.bannerSub}>
              {google.connected
                ? google.status?.account || 'Signed in on your computer.'
                : 'Sign in once on your computer. The phone never holds the token.'}
            </Text>
          </View>
          {loading ? <ActivityIndicator size="small" color={colors.primary} /> : null}
        </Pressable>

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

/** Say plainly whether a list came from Google or is an example. */
function describe(live: boolean, notice: string | undefined,
                  lines: string[], empty: string): string {
  const prefix = live ? '' : `${notice ?? 'Example only - Google is not connected.'}\n\n`;
  return prefix + (lines.length ? lines.join('\n') : empty);
}

function formatTime(value: string): string {
  if (!value) return 'time unknown';
  const when = new Date(value);
  return Number.isNaN(when.getTime())
    ? 'time unknown'
    : when.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const styles = StyleSheet.create({
  connectCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.base,
    gap: spacing.md,
  },
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
