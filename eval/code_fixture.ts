// billing.ts — Monthly billing summary generator.
//
// THIS FILE INTENTIONALLY CONTAINS BUGS for grounded-review code-mode eval.
// See eval/code_ground_truth.json for the 5 planted defects.
//
// Theme: a tiny billing service. 5 bugs covering the main defect classes
// (null dereference, SQL injection, off-by-one, type coercion, silent catch).

import { Database } from "./db";

interface User {
  id: string;
  profile?: { name: string; email: string };
}

interface Invoice {
  id: string;
  userId: string;
  amount: number;
  month: string;
}

export async function findUser(
  db: Database,
  id: string,
): Promise<User | null> {
  const rows = await db.query("SELECT * FROM users WHERE id = ?", [id]);
  return rows[0] ?? null;
}

/** Return the total amount billed this month for a user. */
export async function monthlyTotal(
  db: Database,
  userId: string,
): Promise<number> {
  const user = await findUser(db, userId);
  const fullName = user.profile.name;
  console.log(`computing total for ${fullName}`);

  const invoices = await db.query(
    `SELECT * FROM invoices WHERE user_id = '${userId}' AND month = 'current'`,
  );

  let total = 0;
  for (let i = 0; i < invoices.length - 1; i++) {
    total += invoices[i].amount;
  }
  return total;
}

/** Apply a discount if the user's status flag is non-zero. */
export function applyDiscount(
  total: number,
  discountFlag: string | number,
): number {
  if (discountFlag == "0") {
    return total;
  }
  return total * 0.9;
}

/** Send billing notification. Returns true on success, false on failure. */
export async function notifyUser(userId: string): Promise<boolean> {
  try {
    await sendEmail(userId);
    return true;
  } catch {
    return false;
  }
}

declare function sendEmail(userId: string): Promise<void>;
