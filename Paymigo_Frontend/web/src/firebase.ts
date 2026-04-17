import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';
// Use environment variables if they are set, otherwise fallback to backend project
const finalConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyCOyOylcA8LxpO1BqhJF6H4EKU1O6Ejm84",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "paymigo-27412.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "paymigo-27412",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "paymigo-27412.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "1036534455680",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:1036534455680:web:68a1fc53f58657a79e7565",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-1YETP6KLRP",
  firestoreDatabaseId: import.meta.env.VITE_FIREBASE_DATABASE_ID || "(default)"
};


const app = initializeApp(finalConfig);
export const auth = getAuth(app);
export const db = getFirestore(app, finalConfig.firestoreDatabaseId);
export const storage = getStorage(app);
export const googleProvider = new GoogleAuthProvider();



export const signInWithGoogle = () => signInWithPopup(auth, googleProvider);
export const logout = () => signOut(auth);
export { signInWithEmailAndPassword, createUserWithEmailAndPassword };
