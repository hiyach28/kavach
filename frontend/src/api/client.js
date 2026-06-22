export const apiClient = {
  // Fetch graph nodes & links for D3
  async getGraph() {
    const res = await fetch('/api/graph');
    if (!res.ok) throw new Error('Failed to fetch graph data');
    const json = await res.json();
    return json.data;
  },

  // Fetch districts list with calculated priority scores
  async getDistricts() {
    const res = await fetch('/api/districts');
    if (!res.ok) throw new Error('Failed to fetch district stats');
    const json = await res.json();
    return json.data;
  },

  // Fetch campaigns
  async getCampaigns() {
    // For now, extract from graph data as it returns campaigns list
    const data = await this.getGraph();
    return data.campaigns || [];
  },

  // Fetch cases (optional list, maybe not strictly needed if graph provides nodes)
  async getCases() {
    const res = await fetch('/api/cases');
    if (!res.ok) throw new Error('Failed to fetch cases');
    const json = await res.json();
    return json.data;
  },

  // Classify new case
  async classifyCase(text) {
    const res = await fetch('/api/classify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ raw_text: text })
    });
    if (!res.ok) throw new Error('Classification failed');
    const json = await res.json();
    return json.data; // Should return CaseResponseData
  },

  // Officer feedback loop
  async submitFeedback(caseId, verdict) {
    const res = await fetch('/api/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ case_id: caseId, verdict })
    });
    if (!res.ok) throw new Error('Feedback submission failed');
    const json = await res.json();
    return json.data;
  },

  // Audit log retriever
  async getAuditLogs(auditId) {
    const res = await fetch(`/api/audit/${auditId}`);
    if (!res.ok) return [];
    const json = await res.json();
    return json.data;
  }
};
