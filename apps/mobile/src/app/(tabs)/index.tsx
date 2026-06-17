import { View, Text, StyleSheet } from "react-native";

export function TodayScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Today's Puzzle</Text>
      <Text style={styles.subtitle}>
        Your daily ranked Sudoku challenge. Complete it to earn ELO and climb the
        leaderboard.
      </Text>
      <Text style={styles.hint}>Puzzle loading will appear here.</Text>
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

export default TodayScreen;
