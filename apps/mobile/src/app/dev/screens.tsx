import { View, Text, StyleSheet, ScrollView } from "react-native";

const DEV_SCREENS = [
  { name: "Puzzle Board", path: "/dev/puzzle-board" },
  { name: "Number Pad", path: "/dev/number-pad" },
  { name: "Timer Component", path: "/dev/timer" },
  { name: "Auth Flow", path: "/dev/auth-flow" },
  { name: "Theme Preview", path: "/dev/theme-preview" },
] as const;

export function DevScreensIndex() {
  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.container}
    >
      <Text style={styles.title}>Dev / Test Screens</Text>
      <Text style={styles.subtitle}>
        Agent-visible route for development and testing.
      </Text>

      {DEV_SCREENS.map((screen) => (
        <View key={screen.path} style={styles.row}>
          <Text style={styles.screenName}>{screen.name}</Text>
          <Text style={styles.screenPath}>{screen.path}</Text>
        </View>
      ))}

      <Text style={styles.hint}>
        These routes are placeholders. Wire them up as you build each component.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: "#fff",
  },
  container: {
    padding: 32,
    paddingTop: 64,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1a1a2e",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: "#888",
    marginBottom: 24,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#e0e0e0",
  },
  screenName: {
    fontSize: 16,
    fontWeight: "500",
    color: "#1a1a2e",
  },
  screenPath: {
    fontSize: 13,
    color: "#aaa",
    fontFamily: "monospace",
  },
  hint: {
    fontSize: 13,
    color: "#bbb",
    fontStyle: "italic",
    marginTop: 24,
    textAlign: "center",
  },
});

export default DevScreensIndex;
