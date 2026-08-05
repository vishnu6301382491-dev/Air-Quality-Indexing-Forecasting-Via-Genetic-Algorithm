import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getDatabase } from 'firebase/database';

// Firebase configuration from environment variables
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID,
  databaseURL: process.env.REACT_APP_FIREBASE_DATABASE_URL
};

const hasRequiredConfig = Boolean(firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId && firebaseConfig.appId);

let app = null;
let auth = null;
let database = null;

if (hasRequiredConfig) {
  try {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    database = firebaseConfig.databaseURL ? getDatabase(app) : null;
  } catch (error) {
    console.warn('Firebase is unavailable; authentication is disabled.', error);
  }
} else {
  console.info('Firebase configuration is missing; authentication is disabled.');
}

export { auth, database };
export default app;
