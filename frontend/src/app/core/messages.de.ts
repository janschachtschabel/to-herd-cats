/** German UI strings, keyed. Default (and currently only) locale.
 *
 * A second locale is just another map of the same keys; the I18n service can
 * then select by locale. Entity titles/columns/field labels live in
 * features/entities.ts and are keyed here too. */
export const MESSAGES_DE: Record<string, string> = {
  // App shell / navigation
  'app.title': 'Agent Cockpit',
  'app.devRoles': 'Rollen (dev)',
  'app.login': 'Anmelden',
  'app.logout': 'Abmelden',
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
  // Sent as the run goal when an agent has none set.
  'agents.defaultGoal': 'Führe deine konfigurierte Aufgabe aus.',
  // Agent create/edit form fields (features/agents/agent-fields.ts)
  'agentField.role': 'Rolle',
  'agentField.goal': 'Ziel',
  'agentField.description': 'Beschreibung',
  'agentField.instructions': 'Instruktionen',
  'agentField.status': 'Status',
  'agentField.llm': 'LLM-Verbindung',
  'agentField.tools': 'Werkzeuge',
  'agentField.skills': 'Skills',
  'agentField.dataSources': 'Wissensspeicher',
  'agentField.template': 'Standard-Template',

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

  // Entity titles (features/entities.ts)
  'title.llmConnections': 'LLM-Verbindungen',
  'title.mcpServers': 'MCP-Server',
  'title.tools': 'Werkzeuge',
  'title.dataSources': 'Datenquellen',
  'title.templates': 'Vorlagen',
  'title.channels': 'Kanäle',
  'title.triggers': 'Trigger',
  'title.skills': 'Skills',
  'title.roles': 'Rollen',

  // Entity column / field labels (features/entities.ts). Shared where the
  // concept is the same; a distinct key wherever the label diverges by context.
  'label.name': 'Name',
  'label.model': 'Modell',
  'label.apiBase': 'API-Basis-URL',
  'label.active': 'Aktiv',
  'label.transport': 'Transport',
  'label.command': 'Kommando',
  'label.url': 'URL',
  'label.type': 'Typ',
  'label.mcpServer': 'MCP-Server',
  'label.toolName': 'Tool-Name am Server',
  'label.kind': 'Art',
  'label.format': 'Format',
  'label.direction': 'Richtung',
  'label.mode': 'Modus',
  'label.cron': 'Cron',
  'label.cronScheduled': 'Cron (für scheduled)',
  'label.agent': 'Agent',
  'label.invocation': 'Aufruf',
  'label.description': 'Beschreibung',
  'label.permissions': 'Rechte',
  'label.apiKeyRef': 'API-Key-Referenz (env:VAR)',
  'label.credentialsRef': 'Credentials-Referenz (env:VAR)',
  'label.connectionRef': 'Verbindungs-Referenz (env:VAR)',
  'label.embeddingModel': 'Embedding-Modell',
  'label.collection': 'Collection',
  'label.timezone': 'Zeitzone (z. B. Europe/Berlin)',
  'label.renderTemplate': 'Render-Template (Jinja2)',
  'label.skillDescription': 'Beschreibung (Trigger für progressive disclosure)',
  'label.instructions': 'Anweisungen (SKILL.md-Inhalt)',
};
