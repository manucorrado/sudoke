import { Redirect, Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator, View } from 'react-native';
import type { ComponentProps } from 'react';
import { useOnboarding } from '@/features/onboarding/useOnboarding';
import { colors } from '@/theme/tokens';

type IoniconsName = ComponentProps<typeof Ionicons>['name'];

interface TabConfig {
  name: string;
  title: string;
  icon: IoniconsName;
  focusedIcon: IoniconsName;
}

const TABS: readonly TabConfig[] = [
  { name: 'index', title: 'Today', icon: 'calendar-outline', focusedIcon: 'calendar' },
  { name: 'play', title: 'Play', icon: 'play-circle-outline', focusedIcon: 'play-circle' },
  { name: 'leaderboard', title: 'Leaderboard', icon: 'trophy-outline', focusedIcon: 'trophy' },
  { name: 'social', title: 'Social', icon: 'people-outline', focusedIcon: 'people' },
  { name: 'profile', title: 'Profile', icon: 'person-outline', focusedIcon: 'person' },
] as const;

export function TabLayout() {
  const { status: onboardingStatus } = useOnboarding();

  if (onboardingStatus === 'loading') {
    return (
      <View
        style={{
          flex: 1,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: colors.bg,
        }}
      >
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (onboardingStatus === 'pending') {
    return <Redirect href="/onboarding" />;
  }

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.text,
        tabBarInactiveTintColor: colors.textMuted,
        headerTitleAlign: 'center',
        tabBarStyle: {
          borderTopColor: colors.border,
        },
      }}
    >
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            tabBarIcon: ({ focused, color, size }) => (
              <Ionicons
                name={focused ? tab.focusedIcon : tab.icon}
                size={size}
                color={color}
              />
            ),
          }}
        />
      ))}
    </Tabs>
  );
}

export default TabLayout;
