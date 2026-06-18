import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { appStorage, secureStorage, StorageKeys } from '@/lib/storage';
import { sdk, type AuthContext as SdkAuthContext, type MeDTO } from '@/lib/sdk';

const GUEST_TOKEN_KEY = StorageKeys.guestToken;
const BEARER_KEY = StorageKeys.bearer;

interface AuthState {
  readonly status: 'loading' | 'guest' | 'authenticated' | 'anonymous';
  readonly guestToken: string | null;
  readonly bearer: string | null;
  readonly me: MeDTO | null;
}

interface AuthContextValue extends AuthState {
  readonly authCtx: SdkAuthContext;
  ensureGuest: () => Promise<string>;
  setBearer: (token: string | null) => Promise<void>;
  refreshMe: () => Promise<void>;
  signOut: () => Promise<void>;
}

const Ctx = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  readonly children: ReactNode;
}

/**
 * Guest-first auth provider.
 *
 * On first launch the app provisions an anonymous guest session so the
 * player can immediately try a sample puzzle (PRD §4, §5.1). A real
 * account, once acquired via Clerk (post-Epic-2 wiring), is layered on
 * top and used to authenticate the API; the guest session id is kept for
 * later claim flows (§16, §6.2 of Epic 6).
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    status: 'loading',
    guestToken: null,
    bearer: null,
    me: null,
  });

  const setBearer = useCallback(async (token: string | null) => {
    if (token) {
      await secureStorage.set(BEARER_KEY, token);
    } else {
      await secureStorage.remove(BEARER_KEY);
    }
    setState((prev) => ({ ...prev, bearer: token }));
  }, []);

  const refreshMe = useCallback(async () => {
    setState((prev) => {
      if (!prev.bearer) return { ...prev, me: null };
      return prev;
    });
    const bearer = await secureStorage.get(BEARER_KEY);
    if (!bearer) return;
    try {
      const me = await sdk.getMe({ bearer });
      setState((prev) => ({ ...prev, me, status: 'authenticated' }));
    } catch {
      // bearer is stale — fall back to guest if we have one
      await secureStorage.remove(BEARER_KEY);
      setState((prev) => ({
        ...prev,
        bearer: null,
        me: null,
        status: prev.guestToken ? 'guest' : 'anonymous',
      }));
    }
  }, []);

  const ensureGuest = useCallback(async (): Promise<string> => {
    const existing = await appStorage.get(GUEST_TOKEN_KEY);
    if (existing) {
      setState((prev) => ({
        ...prev,
        guestToken: existing,
        status: prev.bearer ? prev.status : 'guest',
      }));
      return existing;
    }
    const session = await sdk.createGuestSession();
    await appStorage.set(GUEST_TOKEN_KEY, session.token);
    setState((prev) => ({
      ...prev,
      guestToken: session.token,
      status: prev.bearer ? prev.status : 'guest',
    }));
    return session.token;
  }, []);

  const signOut = useCallback(async () => {
    await secureStorage.remove(BEARER_KEY);
    setState((prev) => ({
      ...prev,
      bearer: null,
      me: null,
      status: prev.guestToken ? 'guest' : 'anonymous',
    }));
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [guestToken, bearer] = await Promise.all([
        appStorage.get(GUEST_TOKEN_KEY),
        secureStorage.get(BEARER_KEY),
      ]);
      if (cancelled) return;
      setState({
        status: bearer ? 'authenticated' : guestToken ? 'guest' : 'anonymous',
        guestToken,
        bearer,
        me: null,
      });
      if (bearer) {
        try {
          const me = await sdk.getMe({ bearer });
          if (!cancelled) setState((prev) => ({ ...prev, me }));
        } catch {
          if (!cancelled) {
            await secureStorage.remove(BEARER_KEY);
            setState((prev) => ({
              ...prev,
              bearer: null,
              me: null,
              status: prev.guestToken ? 'guest' : 'anonymous',
            }));
          }
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      authCtx: {
        ...(state.bearer ? { bearer: state.bearer } : {}),
        ...(state.guestToken ? { guestToken: state.guestToken } : {}),
      },
      ensureGuest,
      setBearer,
      refreshMe,
      signOut,
    }),
    [state, ensureGuest, setBearer, refreshMe, signOut],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(Ctx);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
