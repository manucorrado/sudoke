import { View, Text, StyleSheet } from "react-native";

export function SocialScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Social</Text>
      <Text style={styles.subtitle}>
        Challenge friends, send puzzle invites, and keep up with your crew's
        activity feed.
      </Text>
      <Text style={styles.hint}>Friends &amp; challenges will appear here.</Text>
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

export default SocialScreen;
