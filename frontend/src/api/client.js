// KAVACH Stateful API Client Wrapper (Mock Implementation for Local Frontend Run)

// De-identification logic: Regex-masks phone numbers (10-digit and with +91) and Aadhaar numbers (12-digit)
export function deidentify(text) {
  let maskedText = text;
  const tokenMap = {};
  let phoneCounter = 1;
  let aadhaarCounter = 1;

  // Phone numbers (e.g. +91 9876543210, +91-98765-43210, 9876543210)
  const phoneRegex = /(\+91[\-\s]?)?[6-9]\d{9}|(\+91[\-\s]?)\d{5}[\-\s]?\d{5}/g;
  maskedText = maskedText.replace(phoneRegex, (match) => {
    const token = `[PHONE_${phoneCounter++}]`;
    tokenMap[token] = match;
    return token;
  });

  // Aadhaar numbers (12-digit numeric sequences, optionally grouped by space/dash)
  const aadhaarRegex = /\b\d{4}[\-\s]?\d{4}[\-\s]?\d{4}\b/g;
  maskedText = maskedText.replace(aadhaarRegex, (match) => {
    const token = `[AADHAAR_${aadhaarCounter++}]`;
    tokenMap[token] = match;
    return token;
  });

  return { maskedText, tokenMap };
}

// Pre-seeded districts mock data
const SEEDED_DISTRICTS = [
  { name: "Pune", state: "Maharashtra", geojson_id: "27.25", complaint_count: 34, estimated_loss: 125000000, campaigns_count: 1 },
  { name: "Mumbai", state: "Maharashtra", geojson_id: "27.23", complaint_count: 58, estimated_loss: 240000000, campaigns_count: 1 },
  { name: "Dhanbad", state: "Jharkhand", geojson_id: "20.16", complaint_count: 42, estimated_loss: 82000000, campaigns_count: 1 },
  { name: "Delhi", state: "Delhi", geojson_id: "07.03", complaint_count: 28, estimated_loss: 67000000, campaigns_count: 0 },
  { name: "Bengaluru", state: "Karnataka", geojson_id: "29.20", complaint_count: 45, estimated_loss: 154000000, campaigns_count: 0 },
  { name: "Cyberabad", state: "Telangana", geojson_id: "36.03", complaint_count: 38, estimated_loss: 112000000, campaigns_count: 0 },
  { name: "Noida", state: "Uttar Pradesh", geojson_id: "09.12", complaint_count: 25, estimated_loss: 53000000, campaigns_count: 0 },
  { name: "Kolkata", state: "West Bengal", geojson_id: "19.21", complaint_count: 19, estimated_loss: 34000000, campaigns_count: 0 },
  { name: "Ahmedabad", state: "Gujarat", geojson_id: "24.07", complaint_count: 14, estimated_loss: 28000000, campaigns_count: 0 },
  { name: "Jodhpur", state: "Rajasthan", geojson_id: "08.18", complaint_count: 12, estimated_loss: 19000000, campaigns_count: 0 }
];

// Pre-seeded campaigns mock data
const SEEDED_CAMPAIGNS = [
  { id: 1, label: "Campaign A — Pune Digital Arrest Ring", case_count: 5, total_estimated_loss: 125000000, last_clustered_at: new Date().toISOString() },
  { id: 2, label: "Campaign B — Jamtara UPI Spoofing Group", case_count: 5, total_estimated_loss: 82000000, last_clustered_at: new Date().toISOString() },
  { id: 3, label: "Campaign C — Mumbai Investment Mule Network", case_count: 5, total_estimated_loss: 240000000, last_clustered_at: new Date().toISOString() }
];

// Helper to generate UUID-like string
const generateUUID = () => 'act_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

// Pre-seeded cases
const SEEDED_CASES = [
  // Campaign A - Digital Arrest
  {
    id: 1,
    audit_id: generateUUID(),
    raw_text_deidentified: "Target received call from investigator claiming packages containing illegal items sent in their name. Forced to stay on camera for [PHONE_1] hours under 'digital arrest' and transfer money to verify accounts.",
    pii_token_map: JSON.stringify({ "[PHONE_1]": "24" }),
    fraud_type: "digital_arrest",
    risk_score: 95,
    confidence: 0.98,
    verdict: "Classic Digital Arrest scam. Fake customs/CBI call demanding camera presence and assets validation.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Pune",
    campaign_id: 1,
    status: "classified",
    created_at: new Date(Date.now() - 5 * 24 * 3600 * 1000).toISOString(),
    infra: ["customs-verify@upi", "fedex-scam-call"]
  },
  {
    id: 2,
    audit_id: generateUUID(),
    raw_text_deidentified: "Victim placed under digital arrest by callers posing as Mumbai Police claiming Aadhaar card [AADHAAR_1] is linked to money laundering. Transferred ₹5,00,000.",
    pii_token_map: JSON.stringify({ "[AADHAAR_1]": "3829-1928-4829" }),
    fraud_type: "digital_arrest",
    risk_score: 98,
    confidence: 0.96,
    verdict: "High risk Digital Arrest. Aadhaar impersonation and severe financial loss.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Pune",
    campaign_id: 1,
    status: "classified",
    created_at: new Date(Date.now() - 4 * 24 * 3600 * 1000).toISOString(),
    infra: ["customs-verify@upi", "mumbai-police-scam"]
  },
  {
    id: 3,
    audit_id: generateUUID(),
    raw_text_deidentified: "Individual threatened with immediate arrest over Skype call for customs violations. Demanded wire transfer via UPI handle customs-verify@upi.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "digital_arrest",
    risk_score: 90,
    confidence: 0.92,
    verdict: "Active Digital Arrest campaign targeting Pune region utilizing Skype screen sharing.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Pune",
    campaign_id: 1,
    status: "classified",
    created_at: new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString(),
    infra: ["customs-verify@upi"]
  },
  {
    id: 4,
    audit_id: generateUUID(),
    raw_text_deidentified: "Elderly resident contacted on Skype. Extorted for ₹2,50,000 to clear name from fake cargo contraband shipment. UPI destination customs-verify@upi.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "digital_arrest",
    risk_score: 92,
    confidence: 0.95,
    verdict: "Contraband parcel extortion and digital arrest. Uses same customs-verify@upi infrastructure.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Pune",
    campaign_id: 1,
    status: "classified",
    created_at: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString(),
    infra: ["customs-verify@upi"]
  },
  {
    id: 5,
    audit_id: generateUUID(),
    raw_text_deidentified: "Fraudster impersonated Telecom Regulatory official, saying phone number [PHONE_1] will be blocked. Forced Skype connection for asset clearance via customs-verify@upi.",
    pii_token_map: JSON.stringify({ "[PHONE_1]": "+91-99999-88888" }),
    fraud_type: "digital_arrest",
    risk_score: 96,
    confidence: 0.94,
    verdict: "Telecom blocking notice coupled with Skype digital arrest and shared UPI infrastructure.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Pune",
    campaign_id: 1,
    status: "classified",
    created_at: new Date(Date.now() - 1 * 24 * 3600 * 1000).toISOString(),
    infra: ["customs-verify@upi"]
  },

  // Campaign B - UPI Spoofing
  {
    id: 6,
    audit_id: generateUUID(),
    raw_text_deidentified: "Merchant received spoofed UPI alert screenshot showing success for transfer to shop QR. Lost goods worth ₹50,000. Scammer phone [PHONE_1].",
    pii_token_map: JSON.stringify({ "[PHONE_1]": "9123456789" }),
    fraud_type: "upi_spoofing",
    risk_score: 82,
    confidence: 0.89,
    verdict: "UPI Spoofing attack using custom fake transaction confirmation app overlay.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Dhanbad",
    campaign_id: 2,
    status: "classified",
    created_at: new Date(Date.now() - 4 * 24 * 3600 * 1000).toISOString(),
    infra: ["refund@ybl", "spoof-merchant-app"]
  },
  {
    id: 7,
    audit_id: generateUUID(),
    raw_text_deidentified: "UPI spoof app displayed fake notification. Payment request sent via refund@ybl to deceive merchant into entering UPI PIN.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "upi_spoofing",
    risk_score: 85,
    confidence: 0.91,
    verdict: "Reverse UPI payment request scam using spoofed refund alert notifications.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Dhanbad",
    campaign_id: 2,
    status: "classified",
    created_at: new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString(),
    infra: ["refund@ybl"]
  },
  {
    id: 8,
    audit_id: generateUUID(),
    raw_text_deidentified: "Individual was tricked into scanning QR code for receiving cashback. UPI handle linked: refund@ybl.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "upi_spoofing",
    risk_score: 78,
    confidence: 0.88,
    verdict: "QR scan cash-back trap. Uses the refund@ybl destination.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Dhanbad",
    campaign_id: 2,
    status: "classified",
    created_at: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString(),
    infra: ["refund@ybl"]
  },
  {
    id: 9,
    audit_id: generateUUID(),
    raw_text_deidentified: "Scammer claimed excess credit was sent by mistake, requesting return of money using QR code linking refund@ybl.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "upi_spoofing",
    risk_score: 80,
    confidence: 0.90,
    verdict: "Over-payment fake credit refund request routed to refund@ybl.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Dhanbad",
    campaign_id: 2,
    status: "classified",
    created_at: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString(),
    infra: ["refund@ybl"]
  },
  {
    id: 10,
    audit_id: generateUUID(),
    raw_text_deidentified: "Fake customer support phone number [PHONE_1] sent UPI request using refund@ybl claiming security update check.",
    pii_token_map: JSON.stringify({ "[PHONE_1]": "+91-88877-66554" }),
    fraud_type: "upi_spoofing",
    risk_score: 84,
    confidence: 0.93,
    verdict: "Phishing call masquerading as bank support directing users to refund@ybl.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Dhanbad",
    campaign_id: 2,
    status: "classified",
    created_at: new Date(Date.now() - 1 * 24 * 3600 * 1000).toISOString(),
    infra: ["refund@ybl"]
  },

  // Campaign C - Investment Mule
  {
    id: 11,
    audit_id: generateUUID(),
    raw_text_deidentified: "Invested ₹5,00,000 in fake trading app showing 300% weekly returns. Bank transfer to account ending in [PHONE_1] (IFSC SBIN000213). Money frozen.",
    pii_token_map: JSON.stringify({ "[PHONE_1]": "*5678" }),
    fraud_type: "investment_fraud",
    risk_score: 92,
    confidence: 0.95,
    verdict: "Stock trading dashboard scam. Monies routed to mule account *5678.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Mumbai",
    campaign_id: 3,
    status: "classified",
    created_at: new Date(Date.now() - 6 * 24 * 3600 * 1000).toISOString(),
    infra: ["*5678", "earn-more@oksbi"]
  },
  {
    id: 12,
    audit_id: generateUUID(),
    raw_text_deidentified: "Victim recruited via Telegram group for high yield cryptocurrency trading. Deposited funds via earn-more@oksbi to mule account.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "investment_fraud",
    risk_score: 89,
    confidence: 0.90,
    verdict: "Crypto pump-and-dump group targeting Mumbai area. Uses earn-more@oksbi UPI.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Mumbai",
    campaign_id: 3,
    status: "classified",
    created_at: new Date(Date.now() - 5 * 24 * 3600 * 1000).toISOString(),
    infra: ["earn-more@oksbi"]
  },
  {
    id: 13,
    audit_id: generateUUID(),
    raw_text_deidentified: "Part-time task job scam. Complete YouTube video likes for cash, then forced to invest ₹10,00,000 on website, pay via earn-more@oksbi.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "investment_fraud",
    risk_score: 94,
    confidence: 0.94,
    verdict: "Like-and-earn tasks leading to fake investment demands. Shared UPI destination earn-more@oksbi.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Mumbai",
    campaign_id: 3,
    status: "classified",
    created_at: new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString(),
    infra: ["earn-more@oksbi"]
  },
  {
    id: 14,
    audit_id: generateUUID(),
    raw_text_deidentified: "Lured into VIP IPO allotment group. Made bank transfer to mule account ending *5678 and UPI transfer to earn-more@oksbi.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "investment_fraud",
    risk_score: 96,
    confidence: 0.97,
    verdict: "High-value pre-IPO share allocation scam routing to multiple shared nodes.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Mumbai",
    campaign_id: 3,
    status: "classified",
    created_at: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString(),
    infra: ["*5678", "earn-more@oksbi"]
  },
  {
    id: 15,
    audit_id: generateUUID(),
    raw_text_deidentified: "Forex trading platform app. Deposited ₹2,00,000. Refused withdrawal unless tax is paid to UPI handle: earn-more@oksbi.",
    pii_token_map: JSON.stringify({}),
    fraud_type: "investment_fraud",
    risk_score: 91,
    confidence: 0.92,
    verdict: "Forex withdrawal block extortion using standard earn-more@oksbi handle.",
    reporting_portal: "https://www.cybercrime.gov.in",
    district: "Mumbai",
    campaign_id: 3,
    status: "classified",
    created_at: new Date(Date.now() - 1 * 24 * 3600 * 1000).toISOString(),
    infra: ["earn-more@oksbi"]
  }
];

// Helper to initialize local storage
function initLocalStorage() {
  if (!localStorage.getItem("kavach_cases")) {
    localStorage.setItem("kavach_cases", JSON.stringify(SEEDED_CASES));
  }
  if (!localStorage.getItem("kavach_campaigns")) {
    localStorage.setItem("kavach_campaigns", JSON.stringify(SEEDED_CAMPAIGNS));
  }
  if (!localStorage.getItem("kavach_districts")) {
    localStorage.setItem("kavach_districts", JSON.stringify(SEEDED_DISTRICTS));
  }
  if (!localStorage.getItem("kavach_audit_log")) {
    localStorage.setItem("kavach_audit_log", JSON.stringify([]));
  }
}

initLocalStorage();

// Database getters and setters
function getCases() {
  return JSON.parse(localStorage.getItem("kavach_cases"));
}
function setCases(cases) {
  localStorage.setItem("kavach_cases", JSON.stringify(cases));
}
function getCampaigns() {
  return JSON.parse(localStorage.getItem("kavach_campaigns"));
}
function setCampaigns(campaigns) {
  localStorage.setItem("kavach_campaigns", JSON.stringify(campaigns));
}
function getDistricts() {
  return JSON.parse(localStorage.getItem("kavach_districts"));
}
function setDistricts(districts) {
  localStorage.setItem("kavach_districts", JSON.stringify(districts));
}
function getAuditLog() {
  return JSON.parse(localStorage.getItem("kavach_audit_log"));
}
function setAuditLog(log) {
  localStorage.setItem("kavach_audit_log", JSON.stringify(log));
}

// Calculate priority scores for districts dynamically
function computePriorityScores() {
  const districts = getDistricts();
  const cases = getCases();

  // Find max complaints and max loss to normalize
  let maxComplaints = 1;
  let maxLoss = 1;

  districts.forEach(d => {
    if (d.complaint_count > maxComplaints) maxComplaints = d.complaint_count;
    if (d.estimated_loss > maxLoss) maxLoss = d.estimated_loss;
  });

  return districts.map(d => {
    // Count campaigns originating in this district
    const districtCases = cases.filter(c => c.district && c.district.toLowerCase() === d.name.toLowerCase());
    const campaignIds = new Set(districtCases.map(c => c.campaign_id).filter(id => id !== null && id !== undefined));
    const campaignsCount = campaignIds.size;

    // Growth indicator calculation (complaint count compared to seeded base)
    // Formula components: Volume (40%), Impact/Financial Loss (40%), Campaign density (20%)
    const volumeScore = (d.complaint_count / maxComplaints) * 40;
    const lossScore = (d.estimated_loss / maxLoss) * 40;
    const campaignScore = (campaignsCount > 0 ? (campaignsCount / 3) * 20 : 0);

    const priorityScore = Math.min(100, Math.round(volumeScore + lossScore + campaignScore));

    return {
      ...d,
      campaigns_count: campaignsCount,
      priority_score: priorityScore
    };
  });
}

// Simulated Client APIs
export const apiClient = {
  // Fetch cases
  async getCases() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(getCases());
      }, 300);
    });
  },

  // Fetch campaign list
  async getCampaigns() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(getCampaigns());
      }, 300);
    });
  },

  // Fetch districts list with calculated priority scores
  async getDistricts() {
    return new Promise((resolve) => {
      setTimeout(() => {
        const computed = computePriorityScores();
        resolve(computed);
      }, 300);
    });
  },

  // Fetch graph nodes & links for D3
  async getGraph() {
    return new Promise((resolve) => {
      setTimeout(() => {
        const cases = getCases();
        const campaigns = getCampaigns();

        // Nodes: cases, colored by campaign
        const nodes = cases.map(c => {
          // calculate degree (number of cases sharing infra with this one)
          const sharedCount = cases.filter(other => 
            other.id !== c.id && 
            other.infra && 
            c.infra && 
            other.infra.some(infraVal => c.infra.includes(infraVal))
          ).length;

          return {
            id: c.id,
            audit_id: c.audit_id,
            label: `Case #${c.id}`,
            fraud_type: c.fraud_type,
            campaign_id: c.campaign_id,
            risk_score: c.risk_score,
            degree: sharedCount + 1,
            district: c.district,
            created_at: c.created_at
          };
        });

        // Links: create edge between cases that share infrastructure
        const links = [];
        for (let i = 0; i < cases.length; i++) {
          for (let j = i + 1; j < cases.length; j++) {
            const caseA = cases[i];
            const caseB = cases[j];
            if (caseA.infra && caseB.infra && caseA.infra.some(val => caseB.infra.includes(val))) {
              links.push({
                source: caseA.id,
                target: caseB.id,
                value: 2 // strength of link
              });
            }
          }
        }

        resolve({ nodes, links, campaigns });
      }, 400);
    });
  },

  // Classify new case
  async classifyCase(text) {
    const startTime = Date.now();
    const auditId = generateUUID();

    // 1. De-identify text
    const { maskedText, tokenMap } = deidentify(text);

    // 2. Perform logging of request before processing
    const auditLogs = getAuditLog();
    auditLogs.push({
      audit_id: auditId,
      event: "classify_attempt",
      request_payload: JSON.stringify({ raw_text_deidentified: maskedText }),
      created_at: new Date().toISOString()
    });
    setAuditLog(auditLogs);

    return new Promise((resolve) => {
      // Artificially wait 1500ms to show the terminal states (ANALYZING...)
      setTimeout(() => {
        const textLower = text.toLowerCase();
        let fraudType = "legitimate";
        let riskScore = 15;
        let confidence = 0.85;
        let verdict = "Clean text. No active indicators of fraud detected.";
        let flags = [];
        let infra = [];
        let district = "Pune"; // default inferred district

        // Determine district
        if (textLower.includes("mumbai")) district = "Mumbai";
        else if (textLower.includes("pune")) district = "Pune";
        else if (textLower.includes("dhanbad") || textLower.includes("jamtara")) district = "Dhanbad";
        else if (textLower.includes("delhi")) district = "Delhi";
        else if (textLower.includes("bengaluru") || textLower.includes("bangalore")) district = "Bengaluru";
        else {
          // Pick random district
          const distIdx = Math.floor(Math.random() * SEEDED_DISTRICTS.length);
          district = SEEDED_DISTRICTS[distIdx].name;
        }

        // Extracted infrastructure mock patterns
        const upiMatch = text.match(/[a-zA-Z0-9.\-_]+@[a-zA-Z]+/g);
        if (upiMatch) {
          infra.push(...upiMatch);
        }

        const phoneMatch = text.match(/(\+91[\-\s]?)?[6-9]\d{9}/g);
        if (phoneMatch) {
          // Hash or format
          infra.push(...phoneMatch.map(p => p.trim()));
        }

        const bankMatch = text.match(/\b\d{9,18}\b/);
        if (bankMatch) {
          infra.push(`*${bankMatch[0].slice(-4)}`);
        }

        // Keyword rules for structured verdict simulation
        if (textLower.includes("manual review") || textLower.includes("error") || textLower.includes("garbage-script-trigger-123")) {
          // Graceful degradation scenario
          fraudType = "needs_manual_review";
          riskScore = null;
          confidence = 0.50;
          verdict = "System could not classify this input reliably. Routed for immediate manual review by analyst.";
          flags = [
            {
              flag_id: "SYS_ERR_001",
              category: "medium",
              evidence: "N/A",
              explanation: "Input content is garbage or contains system manual review triggers."
            }
          ];
        } else if (textLower.includes("digital arrest") || textLower.includes("customs") || textLower.includes("contraband") || textLower.includes("cbi")) {
          fraudType = "digital_arrest";
          riskScore = 94;
          confidence = 0.97;
          verdict = "High probability Digital Arrest threat. Immediate intervention recommended.";
          flags = [
            {
              flag_id: "IMP_OFF_001",
              category: "critical",
              evidence: text.includes("customs") ? "customs" : text.includes("CBI") ? "CBI" : "arrest",
              explanation: "Impersonation of law enforcement/customs official."
            },
            {
              flag_id: "CON_EXT_002",
              category: "critical",
              evidence: text.includes("money") ? "money" : text.includes("transfer") ? "transfer" : "verify",
              explanation: "Financial extortion under duress."
            },
            {
              flag_id: "CAM_SUR_003",
              category: "high",
              evidence: text.includes("camera") ? "camera" : text.includes("Skype") ? "Skype" : "stay on",
              explanation: "Forced camera surveillance to isolate the victim."
            }
          ];
        } else if (textLower.includes("upi") || textLower.includes("qr") || textLower.includes("spoof") || textLower.includes("refund")) {
          fraudType = "upi_spoofing";
          riskScore = 86;
          confidence = 0.92;
          verdict = "UPI Spoofing / QR Code Cashback scam detected.";
          flags = [
            {
              flag_id: "UPI_REQ_001",
              category: "high",
              evidence: text.includes("refund") ? "refund" : "UPI",
              explanation: "Use of reverse payment requests disguised as refunds."
            },
            {
              flag_id: "QR_TRAP_002",
              category: "high",
              evidence: text.includes("QR") ? "QR" : "scan",
              explanation: "Deceptive QR code scan prompting cash outgo."
            }
          ];
        } else if (textLower.includes("investment") || textLower.includes("trading") || textLower.includes("return") || textLower.includes("part-time")) {
          fraudType = "investment_fraud";
          riskScore = 91;
          confidence = 0.94;
          verdict = "Investment fraud / mule account routing indicators found.";
          flags = [
            {
              flag_id: "RET_PRO_001",
              category: "critical",
              evidence: text.includes("returns") ? "returns" : "invest",
              explanation: "Unrealistic guaranteed return scheme."
            },
            {
              flag_id: "MULE_AC_002",
              category: "high",
              evidence: text.includes("account") ? "account" : "transfer",
              explanation: "Routing funds through multiple beneficiary accounts."
            }
          ];
        } else if (textLower.includes("otp") || textLower.includes("sim") || textLower.includes("swap") || textLower.includes("block")) {
          fraudType = "otp_sim_swap";
          riskScore = 88;
          confidence = 0.90;
          verdict = "SIM Swap or OTP phishing attack indicators.";
          flags = [
            {
              flag_id: "OTP_REQ_001",
              category: "critical",
              evidence: text.includes("OTP") ? "OTP" : "code",
              explanation: "Urgent request for 2FA code verification."
            }
          ];
        }

        // 3. De-identify evidence in flags
        flags = flags.map(f => {
          const deidentifiedEvidence = deidentify(f.evidence).maskedText;
          return {
            ...f,
            evidence: deidentifiedEvidence
          };
        });

        // 4. Clustered campaign logic (Louvain / shared infra check)
        const cases = getCases();
        const campaigns = getCampaigns();
        let assignedCampaignId = null;

        // Check for shared infrastructure with existing cases
        if (fraudType !== "legitimate" && fraudType !== "needs_manual_review") {
          // If we found any infra value, check if it's already in use
          if (infra.length > 0) {
            const matchCase = cases.find(c => c.infra && c.infra.some(val => infra.includes(val)));
            if (matchCase && matchCase.campaign_id) {
              assignedCampaignId = matchCase.campaign_id;
            }
          }

          // If no shared infra, but we match a campaign's type, we could optionally cluster
          // For MVP, if it shares infra, it joins. Otherwise, it forms its own unclustered node.
        }

        // 5. Update local case list
        const newId = cases.length + 1;
        const newCase = {
          id: newId,
          audit_id: auditId,
          raw_text_deidentified: maskedText,
          pii_token_map: JSON.stringify(tokenMap),
          fraud_type: fraudType,
          risk_score: riskScore,
          confidence: confidence,
          verdict: verdict,
          reporting_portal: "https://www.cybercrime.gov.in",
          district: district,
          campaign_id: assignedCampaignId,
          status: fraudType === "needs_manual_review" ? "needs_manual_review" : "classified",
          created_at: new Date().toISOString(),
          infra: infra
        };

        const updatedCases = [...cases, newCase];
        setCases(updatedCases);

        // 6. Update campaigns denormalized numbers
        if (assignedCampaignId) {
          const updatedCampaigns = campaigns.map(cam => {
            if (cam.id === assignedCampaignId) {
              // Estimate financial loss (mock addition: 1,50,000 paise per new case)
              return {
                ...cam,
                case_count: cam.case_count + 1,
                total_estimated_loss: cam.total_estimated_loss + 15000000,
                last_clustered_at: new Date().toISOString()
              };
            }
            return cam;
          });
          setCampaigns(updatedCampaigns);
        }

        // 7. Update district complaint counts & estimated losses
        const districts = getDistricts();
        const updatedDistricts = districts.map(d => {
          if (d.name.toLowerCase() === district.toLowerCase()) {
            return {
              ...d,
              complaint_count: d.complaint_count + 1,
              estimated_loss: d.estimated_loss + 15000000 // add ₹1.5 lakh
            };
          }
          return d;
        });
        setDistricts(updatedDistricts);

        // 8. Log success/fail audit log
        const latency = Date.now() - startTime;
        const finalLogs = getAuditLog();
        finalLogs.push({
          audit_id: auditId,
          event: fraudType === "needs_manual_review" ? "classify_failure" : "classify_success",
          request_payload: JSON.stringify({ raw_text_deidentified: maskedText }),
          response_payload: JSON.stringify(newCase),
          latency_ms: latency,
          created_at: new Date().toISOString()
        });
        setAuditLog(finalLogs);

        resolve(newCase);
      }, 1500);
    });
  },

  // Officer feedback loop P2
  async submitFeedback(caseId, verdict) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const cases = getCases();
        const updated = cases.map(c => {
          if (c.id === parseInt(caseId)) {
            return { ...c, status: verdict };
          }
          return c;
        });
        setCases(updated);
        resolve({ success: true, caseId, status: verdict });
      }, 300);
    });
  },

  // Audit log retriever
  async getAuditLogs(auditId) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const logs = getAuditLog();
        const filtered = logs.filter(l => l.audit_id === auditId);
        resolve(filtered);
      }, 300);
    });
  }
};
