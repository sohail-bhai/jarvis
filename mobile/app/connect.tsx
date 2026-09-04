/**
 * Connecting this phone to your computer.
 *
 * Two steps, in the order a person can actually do them: say where the
 * computer is, then type the code it shows. Reaching the computer and being
 * allowed to use it are separate things, so the address is checked first and a
 * typo is reported as a wrong address rather than as a wrong code.
 */
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ApiError, getHost } from '../src/api/client';
import { sessionService } from '../src/api/session';
import { borderRadius, colors, spacing, typography } from '../src/theme';

type Step = 'address' | 'code';

export default function ConnectScreen() {
  const [step, setStep] = useState<Step>('address');
  const [address, setAddress] = useState('');
  const [code, setCode] = useState('');
  const [name, setName] = useState('My phone');
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState('');

  useEffect(() => {
    // Offer the last address back, so reconnecting is one tap.
    sessionService.load().then(state => setAddress(state.host || getHost()));
  }, []);

  const checkAddress = async () => {
    setBusy(true);
    setProblem('');
    try {
      await sessionService.checkHost(address);
      setStep('code');
    } catch (error) {
      setProblem(
        error instanceof ApiError
          ? `${error.message} Check the computer is on and JARVIS is running.`
          : 'Could not reach that address.',
      );
    } finally {
      setBusy(false);
    }
  };

  const pair = async () => {
    setBusy(true);
    setProblem('');
    try {
      await sessionService.pair(code, name);
      router.replace('/(tabs)');
    } catch (error) {
      setProblem(
        error instanceof ApiError
          ? error.status === 403
            ? 'That code was wrong or has expired. Ask the computer for a new one.'
            : error.message
          : 'Could not connect.',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View style={styles.badge}>
            <Ionicons name="hardware-chip-outline" size={26} color={colors.primary} />
          </View>

          <Text style={styles.title}>Connect to your computer</Text>
          <Text style={styles.subtitle}>
            JARVIS runs on your computer. This phone asks it to do things, and shows you
            what it did.
          </Text>

          {step === 'address' ? (
            <View style={styles.card}>
              <Text style={styles.label}>Where is your computer?</Text>
              <TextInput
                style={styles.input}
                value={address}
                onChangeText={setAddress}
                placeholder="192.168.1.20:8765"
                placeholderTextColor={colors.textTertiary}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="url"
                editable={!busy}
              />
              <Text style={styles.hint}>
                Its address on your network, or its Tailscale name if you use one. The
                computer shows this when JARVIS starts.
              </Text>
            </View>
          ) : (
            <View style={styles.card}>
              <Text style={styles.label}>Enter the code from your computer</Text>
              <TextInput
                style={[styles.input, styles.codeInput]}
                value={code}
                onChangeText={setCode}
                placeholder="000000"
                placeholderTextColor={colors.textTertiary}
                keyboardType="number-pad"
                maxLength={6}
                editable={!busy}
              />
              <Text style={styles.hint}>
                On the computer, open Settings and choose Connect a phone. The code lasts
                ten minutes.
              </Text>

              <Text style={[styles.label, styles.spaced]}>What should JARVIS call this phone?</Text>
              <TextInput
                style={styles.input}
                value={name}
                onChangeText={setName}
                placeholder="My phone"
                placeholderTextColor={colors.textTertiary}
                editable={!busy}
              />
            </View>
          )}

          {problem ? (
            <View style={styles.problem}>
              <Ionicons name="alert-circle-outline" size={18} color={colors.error} />
              <Text style={styles.problemText}>{problem}</Text>
            </View>
          ) : null}

          <TouchableOpacity
            style={[styles.button, busy && styles.buttonBusy]}
            onPress={step === 'address' ? checkAddress : pair}
            disabled={busy || (step === 'address' ? !address.trim() : code.trim().length < 4)}
          >
            {busy ? (
              <ActivityIndicator color={colors.textInverse} />
            ) : (
              <Text style={styles.buttonText}>
                {step === 'address' ? 'Continue' : 'Connect'}
              </Text>
            )}
          </TouchableOpacity>

          {step === 'code' ? (
            <TouchableOpacity onPress={() => { setStep('address'); setProblem(''); }}>
              <Text style={styles.back}>Use a different address</Text>
            </TouchableOpacity>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  flex: { flex: 1 },
  content: { padding: spacing.xl, paddingTop: spacing['3xl'] },
  badge: {
    width: 52,
    height: 52,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  title: { ...typography.titleLarge, color: colors.textPrimary },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    marginBottom: spacing.xl,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
  label: { ...typography.label, color: colors.textPrimary, marginBottom: spacing.sm },
  spaced: { marginTop: spacing.lg },
  input: {
    ...typography.body,
    color: colors.textPrimary,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.md,
  },
  codeInput: { fontSize: 24, letterSpacing: 8, textAlign: 'center' },
  hint: { ...typography.caption, color: colors.textSecondary, marginTop: spacing.sm },
  problem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    backgroundColor: colors.errorLight,
    borderRadius: borderRadius.md,
    padding: spacing.base,
    marginTop: spacing.base,
  },
  problemText: { ...typography.caption, color: colors.error, flex: 1 },
  button: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.base,
    alignItems: 'center',
    marginTop: spacing.xl,
  },
  buttonBusy: { opacity: 0.7 },
  buttonText: { ...typography.button, color: colors.textInverse },
  back: {
    ...typography.caption,
    color: colors.primary,
    textAlign: 'center',
    marginTop: spacing.base,
  },
});
