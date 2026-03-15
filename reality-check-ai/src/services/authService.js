// ──────────────────────────────────────────────
// Firebase Auth Service
// Install: npm install firebase
// ──────────────────────────────────────────────

// Uncomment below once firebase is installed:

// import { initializeApp } from 'firebase/app'
// import {
//   getAuth,
//   signInWithEmailAndPassword,
//   createUserWithEmailAndPassword,
//   signInWithPopup,
//   GoogleAuthProvider,
//   signOut,
//   onAuthStateChanged,
// } from 'firebase/auth'

// const firebaseConfig = {
//   apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
//   authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
//   projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
// }

// const app = initializeApp(firebaseConfig)
// const auth = getAuth(app)
// const googleProvider = new GoogleAuthProvider()

// Placeholder exports for development without Firebase
export async function loginWithEmail(email, password) {
  console.log('Firebase not configured — mock login:', email)
  localStorage.setItem('authToken', 'mock-jwt-token')
  return { uid: 'mock-user', email }
}

export async function signupWithEmail(email, password) {
  console.log('Firebase not configured — mock signup:', email)
  localStorage.setItem('authToken', 'mock-jwt-token')
  return { uid: 'mock-user', email }
}

export async function loginWithGoogle() {
  console.log('Firebase not configured — mock Google login')
  localStorage.setItem('authToken', 'mock-jwt-token')
  return { uid: 'mock-user', email: 'user@gmail.com' }
}

export async function logout() {
  localStorage.removeItem('authToken')
}

export function onAuthChange(callback) {
  // Mock: check if token exists
  const token = localStorage.getItem('authToken')
  callback(token ? { uid: 'mock-user' } : null)
  return () => {} // unsubscribe
}
