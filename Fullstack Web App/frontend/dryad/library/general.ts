export function capitalizeFirstLetter(str : string) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function timeAgo(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();

  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  const intervals = [
    { unit: "year", seconds: 31536000 },
    { unit: "month", seconds: 2592000 },
    { unit: "week", seconds: 604800 },
    { unit: "day", seconds: 86400 },
    { unit: "hour", seconds: 3600 },
    { unit: "minute", seconds: 60 },
    { unit: "second", seconds: 1 },
  ] as const;

  for (const interval of intervals) {
    const value = Math.floor(seconds / interval.seconds);

    if (value >= 1) {
      return `${value} ${interval.unit}${value !== 1 ? "s" : ""} ago`;
    }
  }

  return "just now";
}

export async function copyTextToClipboard(text : string) {
  try {
    await navigator.clipboard.writeText(text);
    console.log('Text successfully copied to clipboard!');
  } catch (err) {
    console.error('Failed to copy text: ', err);
  }
}