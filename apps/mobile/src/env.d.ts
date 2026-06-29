// Expo statically inlines EXPO_PUBLIC_* variables at build time via its Babel
// plugin. Declare only what the app reads so we avoid pulling in @types/node.
declare const process: {
  readonly env: {
    readonly EXPO_PUBLIC_API_BASE_URL?: string;
  };
};
