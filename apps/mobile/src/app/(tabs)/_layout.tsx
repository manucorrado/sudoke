import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import type { ComponentProps } from "react";

type IoniconsName = ComponentProps<typeof Ionicons>["name"];

interface TabConfig {
  name: string;
  title: string;
  icon: IoniconsName;
  focusedIcon: IoniconsName;
}

const TABS: readonly TabConfig[] = [
  { name: "index", title: "Today", icon: "calendar-outline", focusedIcon: "calendar" },
  { name: "play", title: "Play", icon: "play-circle-outline", focusedIcon: "play-circle" },
  { name: "leaderboard", title: "Leaderboard", icon: "trophy-outline", focusedIcon: "trophy" },
  { name: "social", title: "Social", icon: "people-outline", focusedIcon: "people" },
  { name: "profile", title: "Profile", icon: "person-outline", focusedIcon: "person" },
] as const;

export function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: "#1a1a2e",
        tabBarInactiveTintColor: "#999",
        headerTitleAlign: "center",
        tabBarStyle: {
          borderTopColor: "#eee",
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
