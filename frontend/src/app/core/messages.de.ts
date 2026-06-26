/** German UI strings, keyed. Default (and currently only) locale.
 *
 * A second locale is just another map of the same keys; the I18n service can
 * then select by locale. Entity titles/columns/field labels live in
 * features/entities.ts and are keyed here too. */
export const MESSAGES_DE: Record<string, string> = {
  // App shell / navigation
  'app.title': 'Agent Cockpit',
  'nav.agents': 'Agenten',
  'nav.inbox': 'Postbox',
  'nav.runs': 'Runs',

  // Agents
  'agents.heading': 'Agenten',
  'agents.name': 'Name',
  'agents.goal': 'Ziel (optional)',
  'agents.create': 'Anlegen',
  'agents.run': 'Ausführen',
  'agents.empty': 'Noch keine Agenten.',
  'agents.loadError': 'Agenten konnten nicht geladen werden.',
  'agents.createError': 'Agent konnte nicht erstellt werden.',
  'agents.runError': 'Run konnte nicht gestartet werden.',

  // Postbox (inbox)
  'inbox.heading': 'Postbox',
  'inbox.empty': 'Keine Einträge.',
  'inbox.reply': 'Antwort / Bearbeitung (optional)',
  'inbox.answered': 'Beantwortet',
  'inbox.loadError': 'Postbox konnte nicht geladen werden.',
  'inbox.respondError': 'Antwort fehlgeschlagen.',

  // Runs / metrics
  'runs.heading': 'Runs',
  'runs.total': 'Runs gesamt',
  'runs.status': 'Status',
  'runs.tokens': 'Tokens',
  'runs.cost': 'Kosten',
  'runs.empty': 'Keine Runs.',
  'runs.loadError': 'Runs konnten nicht geladen werden.',

  // Generic entity list
  'list.new': 'Neu',
  'list.empty': 'Keine Einträge.',
  'list.edit': 'Bearbeiten',
  'list.delete': 'Löschen',
  'list.loadError': 'Daten konnten nicht geladen werden.',
  'list.deleteError': 'Löschen fehlgeschlagen.',

  // Generic entity form
  'form.new': 'neu',
  'form.edit': 'bearbeiten',
  'form.save': 'Speichern',
  'form.cancel': 'Abbrechen',
  'form.requiredMissing': 'Pflichtfeld fehlt',
  'form.saveError': 'Speichern fehlgeschlagen.',
  'form.optionsError': 'Auswahllisten konnten nicht geladen werden.',
  'form.loadError': 'Eintrag konnte nicht geladen werden.',
};
