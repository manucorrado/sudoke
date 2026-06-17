import { View, Text, StyleSheet } from "react-native";

export function PlayScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Play</Text>
      <Text style={styles.subtitle}>
        Practice puzzles, browse the archive, or start a custom game at your
        preferred difficulty.
      </Text>
      <Text style={styles.hint}>Game modes will appear here.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#1a1a2e",
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: "#555",
    textAlign: "center",
    lineHeight: 24,
    marginBottom: 24,
  },
  hint: {
    fontSize: 14,
    color: "#aaa",
    fontStyle: "italic",
  },
});

export default PlayScreen;
