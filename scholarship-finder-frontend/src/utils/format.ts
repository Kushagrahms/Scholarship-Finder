
export function displayAmount(
  amount: string | number | null | undefined,
  amountText?: string | null
): string {
  if (amountText?.trim()) return amountText;

  if (amount !== null && amount !== undefined && String(amount).trim()) {
    const value = Number(amount);

    if (!Number.isFinite(value)) return String(amount);

    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(value);
  }

  return "Amount not specified";
}

export function displayDate(
  value: string | null | undefined
): string {
  if (!value) return "Deadline not confirmed";

  const date = new Date(`${value.slice(0, 10)}T00:00:00`);

  if (Number.isNaN(date.getTime())) return "Date unavailable";

  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

export function humanize(
  value: string | null | undefined
): string {
  if (!value?.trim()) return "Not specified";

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function safeExternalUrl(
  value: string | null | undefined
): string | null {
  if (!value) return null;

  try {
    const url = new URL(value);

    return ["https:", "http:"].includes(url.protocol)
      ? url.toString()
      : null;
  } catch {
    return null;
  }
}
