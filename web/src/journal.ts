/** In development, send an entry to the journal kept in data/journal/web.jsonl. */
export function journal(entry: Record<string, unknown>): void {
  if (!import.meta.env.DEV) return;
  fetch(`${import.meta.env.BASE_URL}__journal`, {
    method: "POST",
    body: JSON.stringify({ page: location.search, ...entry }),
    keepalive: true,
  }).catch(() => {});
}

export function journalErrors(): void {
  window.addEventListener("error", (event) => {
    journal({ type: "erreur", message: event.message, source: `${event.filename}:${event.lineno}` });
  });
  window.addEventListener("unhandledrejection", (event) => {
    journal({ type: "erreur", message: String(event.reason) });
  });
}
