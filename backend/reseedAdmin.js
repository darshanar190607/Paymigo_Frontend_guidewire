import { PrismaClient } from "@prisma/client";
import bcrypt from "bcrypt";

const prisma = new PrismaClient();

async function main() {
  const email = "REDACTED";
  const password = "REDACTED";
  const name = "System Administrator";
  
  console.log(`🚀 Reseeding admin user: ${email}...`);
  
  const passwordHash = await bcrypt.hash(password, 10);
  
  // Ensure default zone exists
  await prisma.zone.upsert({
    where: { id: "default" },
    update: {},
    create: {
      id: "default",
      name: "Default Zone",
      city: "Chennai",
      pincode: "000000",
      riskTier: 1,
      riskMultiplier: 1.0,
    }
  });

  const admin = await prisma.worker.upsert({
    where: { email },
    update: {
      passwordHash,
      name,
    },
    create: {
      email,
      passwordHash,
      name,
      phone: "9999999999",
      pincode: "000000",
      zoneId: "default",
      riskTier: 1,
    }
  });

  console.log("✅ Admin reseeded successfully!");
  console.log(JSON.stringify(admin, null, 2));
}

main()
  .catch((e) => {
    console.error("❌ Reseed failed:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
