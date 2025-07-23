'use client';

import { useAuth0 } from '@auth0/auth0-react';
import { useEffect, useState } from 'react';
import ApiClient from '@/lib/api';

export function useAuth() {
  const {
    user,
    isAuthenticated,
    isLoading,
    getAccessTokenSilently,
    loginWithRedirect,
    logout,
  } = useAuth0();

  const [apiClient, setApiClient] = useState<ApiClient | null>(null);
  const [userSynced, setUserSynced] = useState(false);

  useEffect(() => {
    if (isAuthenticated && getAccessTokenSilently) {
      const client = new ApiClient(getAccessTokenSilently);
      setApiClient(client);

      // Sync user with backend using actual user object data
      const syncUser = async () => {
        if (user && !userSynced) {
          try {
            // Use the actual user data from Auth0 user object
            const email = user.email || `${user.sub}@placeholder.com`;
            const name = user.name || user.nickname || email.split('@')[0];
            const picture = user.picture || '';
            
            console.log('Syncing user with data:', { sub: user.sub, email, name, picture });
            
            await client.syncUser({
              auth0_id: user.sub!,
              email: email,
              name: name,
              picture: picture,
            });
            setUserSynced(true);
          } catch (error) {
            console.error('Failed to sync user:', error);
          }
        }
      };

      syncUser();
    }
  }, [isAuthenticated, user, getAccessTokenSilently, userSynced]);

  return {
    user,
    isAuthenticated,
    isLoading,
    loginWithRedirect,
    logout,
    apiClient,
    userSynced,
  };
}