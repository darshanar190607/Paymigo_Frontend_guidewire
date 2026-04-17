import admin from "firebase-admin";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";

let initialized = false;

const initFirebaseAdmin = () => {
  if (initialized || admin.apps.length > 0) return admin;

  const serviceAccountPath = resolve("config", "firebase-service-account.json");

  if (!existsSync(serviceAccountPath)) {
    throw new Error("firebase-service-account.json not found in config/. Auth will fail.");
  }

  const serviceAccount = JSON.parse(readFileSync(serviceAccountPath, "utf-8"));

  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
  });

  initialized = true;
  console.log(`✅ Firebase Admin initialized for project: ${serviceAccount.project_id}`);
  return admin;
};

export default initFirebaseAdmin;
