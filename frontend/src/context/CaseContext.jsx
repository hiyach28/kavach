import React, { createContext, useState, useEffect, useContext } from 'react';
import { apiClient } from '../api/client';

const CaseContext = createContext();

export const useCase = () => {
  const context = useContext(CaseContext);
  if (!context) {
    throw new Error('useCase must be used within a CaseProvider');
  }
  return context;
};

export const CaseProvider = ({ children }) => {
  const [cases, setCases] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [districts, setDistricts] = useState([]);
  
  // Navigation active tab: 'overview' | 'fraudscope' | 'network' | 'crimemap'
  const [activeTab, setActiveTab] = useState('overview');

  // Shared persistent active context items
  const [activeCase, setActiveCase] = useState(null);
  const [activeCampaign, setActiveCampaign] = useState(null);
  const [activeDistrict, setActiveDistrict] = useState(null);

  const [loading, setLoading] = useState(true);

  // Fetch initial data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [casesData, campaignsData, districtsData] = await Promise.all([
        apiClient.getCases(),
        apiClient.getCampaigns(),
        apiClient.getDistricts()
      ]);
      setCases(casesData);
      setCampaigns(campaignsData);
      setDistricts(districtsData);
      // NOTE: We do NOT auto-select a case on load — FraudScope should start empty
    } catch (err) {
      console.error("Failed to load initial data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Update active selections based on selected case
  const handleSelectCase = (caseObj) => {
    if (!caseObj) {
      setActiveCase(null);
      return;
    }
    
    setActiveCase(caseObj);

    // Auto-select corresponding campaign if present
    if (caseObj.campaign_id) {
      const camp = campaigns.find(c => c.id === caseObj.campaign_id);
      if (camp) setActiveCampaign(camp);
    } else {
      setActiveCampaign(null);
    }

    // Auto-select corresponding district if present
    if (caseObj.district) {
      const dist = districts.find(d => d.name.toLowerCase() === caseObj.district.toLowerCase());
      if (dist) setActiveDistrict(dist);
    }
  };

  // Direct selections
  const handleSelectCampaign = (campId) => {
    const camp = campaigns.find(c => c.id === campId);
    setActiveCampaign(camp || null);
    
    // Select first case in this campaign as active case
    const campaignCases = cases.filter(c => c.campaign_id === campId);
    if (campaignCases.length > 0) {
      setActiveCase(campaignCases[0]);
    }
  };

  const handleSelectDistrict = (distName) => {
    const dist = districts.find(d => d.name.toLowerCase() === distName.toLowerCase());
    setActiveDistrict(dist || null);

    // If there is an active case in this district, keep it, otherwise find the first case in this district
    const districtCases = cases.filter(c => c.district && c.district.toLowerCase() === distName.toLowerCase());
    if (districtCases.length > 0) {
      const activeInDistrict = districtCases.find(c => activeCase && c.id === activeCase.id);
      if (!activeInDistrict) {
        setActiveCase(districtCases[0]);
      }
    }
  };

  // Classify a new case
  const classifyCaseText = async (text) => {
    try {
      const result = await apiClient.classifyCase(text);
      
      // Refresh list from API (local storage updates inside client.js)
      const [casesData, campaignsData, districtsData] = await Promise.all([
        apiClient.getCases(),
        apiClient.getCampaigns(),
        apiClient.getDistricts()
      ]);
      
      setCases(casesData);
      setCampaigns(campaignsData);
      setDistricts(districtsData);

      // Retrieve the newly created case object
      const newestCase = casesData.find(c => c.audit_id === result.audit_id);
      if (newestCase) {
        handleSelectCase(newestCase);
      }
      return result;
    } catch (err) {
      console.error("Classification error", err);
      throw err;
    }
  };

  // Clear active case (called after investigator confirms/clears a case)
  const clearActiveCase = () => {
    setActiveCase(null);
    setActiveCampaign(null);
  };

  // Submit feedback — on 'confirmed', also clear the active dossier so results reset
  const submitFeedback = async (caseId, feedbackType) => {
    try {
      await apiClient.submitFeedback(caseId, feedbackType);
      // Refresh case list
      const casesData = await apiClient.getCases();
      setCases(casesData);
      // After confirming or clearing, close the dossier so FraudScope resets
      if (feedbackType === 'confirmed' || feedbackType === 'false_positive') {
        clearActiveCase();
      } else if (activeCase && activeCase.id === parseInt(caseId)) {
        setActiveCase(prev => ({ ...prev, status: feedbackType }));
      }
    } catch (err) {
      console.error("Feedback submit error", err);
    }
  };

  return (
    <CaseContext.Provider value={{
      cases,
      campaigns,
      districts,
      activeTab,
      setActiveTab,
      activeCase,
      activeCampaign,
      activeDistrict,
      loading,
      selectCase: handleSelectCase,
      selectCampaign: handleSelectCampaign,
      selectDistrict: handleSelectDistrict,
      classifyCase: classifyCaseText,
      submitFeedback,
      clearActiveCase,
      refreshData: fetchData
    }}>
      {children}
    </CaseContext.Provider>
  );
};
