import { View, Text, StyleSheet } from "react-native";

export function ProfileScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Profile</Text>
      <Text style={styles.subtitle}>
        View your stats, manage your account, and adjust app settings.
      </Text>
      <Text style={styles.hint}>Settings &amp; stats will appear here.</Text>
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

export default ProfileScreen;
