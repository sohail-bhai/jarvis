import { useFonts } from 'expo-font';
import { Stack, router } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';

import { sessionService } from '../src/api/session';
import { AppProvider } from '../src/store/AppContext';
import { colors } from '../src/theme';

import { LogBox } from 'react-native';

LogBox.ignoreLogs([
  'Cannot connect to Expo CLI',
  'Running application',
]);

export {
  ErrorBoundary,
} from 'expo-router';

export const unstable_settings = {
  initialRouteName: '(tabs)',
};

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded, error] = useFonts({
    Inter: require('../assets/fonts/SpaceMono-Regular.ttf'),
  });

  // Until the phone knows which computer it belongs to, every screen would
  // have nothing to show, so the connect screen comes first.
  const [checked, setChecked] = useState(false);
  const [paired, setPaired] = useState(false);

  useEffect(() => {
    sessionService.load().then(state => {
      setPaired(state.paired);
      setChecked(true);
    });
  }, []);

  useEffect(() => {
    if (checked && !paired) {
      router.replace('/connect');
    }
  }, [checked, paired]);

  useEffect(() => {
    if (error) throw error;
  }, [error]);

  useEffect(() => {
    if (loaded && checked) {
      SplashScreen.hideAsync();
    }
  }, [loaded, checked]);

  if (!loaded || !checked) {
    return null;
  }

  return (
    <AppProvider>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: colors.background,
          },
          headerTintColor: colors.textPrimary,
          headerTitleStyle: {
            fontWeight: '600',
            fontSize: 17,
          },
          headerShadowVisible: false,
          contentStyle: {
            backgroundColor: colors.background,
          },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="connect"
          options={{
            headerShown: false,
            // Nothing works before this, so there is nowhere to go back to.
            gestureEnabled: false,
          }}
        />
        <Stack.Screen
          name="task/[id]"
          options={{
            title: 'Task Details',
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="devices"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="security"
          options={{
            title: 'Your Security',
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="approvals"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="away"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="google"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
      </Stack>
    </AppProvider>
  );
}
