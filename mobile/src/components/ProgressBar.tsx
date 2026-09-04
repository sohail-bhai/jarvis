import React from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { colors, spacing, borderRadius } from '../theme';

interface ProgressBarProps {
  progress: number; // 0–100
  height?: number;
  showLabel?: boolean;
  color?: string;
}

export function ProgressBar({ progress, height = 6, showLabel = false, color }: ProgressBarProps) {
  const clampedProgress = Math.min(100, Math.max(0, progress));
  const barColor = color || colors.progressFill;
  const animVal = React.useRef(new Animated.Value(clampedProgress)).current;

  React.useEffect(() => {
    Animated.timing(animVal, {
      toValue: clampedProgress,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [clampedProgress]);

  const animatedWidth = animVal.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={styles.container}>
      <View style={[styles.track, { height }]}>
        <Animated.View
          style={[
            styles.fill,
            {
              width: animatedWidth,
              height,
              backgroundColor: barColor,
            },
          ]}
        />
      </View>
      {showLabel && (
        <Text style={styles.label}>{Math.round(clampedProgress)}%</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  track: {
    flex: 1,
    backgroundColor: colors.progressTrack,
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  fill: {
    borderRadius: borderRadius.full,
  },
  label: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textSecondary,
    minWidth: 32,
    textAlign: 'right',
  },
});
