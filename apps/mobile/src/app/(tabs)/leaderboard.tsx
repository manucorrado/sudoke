import { View, Text, StyleSheet } from "react-native";

export function LeaderboardScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Leaderboard</Text>
      <Text style={styles.subtitle}>
        See how you rank against players worldwide. Filter by friends, region, or
        all-time records.
      </Text>
      <Text style={styles.hint}>Rankings will appear here.</Text>
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

export default LeaderboardScreen;
