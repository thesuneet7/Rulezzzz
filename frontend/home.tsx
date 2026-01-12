
import React, { useState } from 'react';
import axios from 'axios';
import Dropzone from './dropzone';
import Dashboard from './components/Dashboard';
import { Shield, BarChart3, Sparkles } from 'lucide-react';
import './index.css';

const API_BASE = 'http://localhost:8000';

// Interface for compliance results
interface ComplianceResult {
    'Regulatory Clause': string;
    'Compliant with Bank Policy': string;
    'Compliant with System Rules': string;
    'Explanation': string;
}

interface FileInfo {
    regulation: string;
    policy: string;
    system_rules: string;
}

const Home: React.FC = () => {
    const [view, setView] = useState<'input' | 'processing' | 'results'>('input');

    const [regulation, setRegulation] = useState<File | null>(null);
    const [policy, setPolicy] = useState<File | null>(null);
    const [systemRules, setSystemRules] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<ComplianceResult[]>([]);
    const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
    const [processingStatus, setProcessingStatus] = useState<string>('Uploading files...');

    const handleSubmit = async () => {
        if (!regulation || !policy || !systemRules) {
            alert("Please upload all 3 files");
            return;
        }

        setView('processing');
        setError(null);
        setProcessingStatus('Uploading files...');

        try {
            // Step 1: Upload files
            const formData = new FormData();
            formData.append('regulation', regulation);
            formData.append('policy', policy);
            formData.append('system_rules', systemRules);

            await axios.post(`${API_BASE}/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setProcessingStatus('Running compliance analysis...');

            // Step 2: Process files
            const processResponse = await axios.post(`${API_BASE}/process`);

            if (processResponse.data.status !== 'completed') {
                throw new Error(processResponse.data.failed_at || 'Processing failed');
            }

            setProcessingStatus('Fetching results...');

            // Step 3: Get results
            const resultsResponse = await axios.get(`${API_BASE}/results`);
            setResults(resultsResponse.data.results || []);
            setFileInfo({
                regulation: regulation.name,
                policy: policy.name,
                system_rules: systemRules.name
            });

            setView('results');

        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || 'Failed to process files');
            setView('input');
        }
    };

    if (view === 'results') {
        return <Dashboard onBack={() => setView('input')} results={results} fileInfo={fileInfo} />;
    }

    if (view === 'processing') {
        return (
            <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div className="spinner" style={{
                    width: '50px',
                    height: '50px',
                    border: '4px solid #EFF6FF',
                    borderTop: '4px solid #2563EB',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                }}></div>
                <h2 style={{ marginTop: '2rem', color: '#2563EB' }}>Processing Documents...</h2>
                <p style={{ color: '#6B7280' }}>{processingStatus}</p>
                <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    return (
        <div>
            {/* Error Display */}
            {error && (
                <div style={{
                    background: '#FEE2E2',
                    border: '1px solid #EF4444',
                    color: '#DC2626',
                    padding: '1rem',
                    margin: '1rem 2rem',
                    borderRadius: '8px'
                }}>
                    ⚠️ {error}
                </div>
            )}
            {/* Header */}
            <header style={{
                padding: '1rem 2rem',
                borderBottom: '1px solid #E5E7EB',
                background: 'white',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ background: '#2563EB', padding: '6px', borderRadius: '8px', display: 'flex' }}>
                        <Shield color="white" size={20} />
                    </div>
                    <div>
                        <div style={{ fontWeight: '700', fontSize: '1.2rem', color: '#111827', lineHeight: 1 }}>TraceComply</div>
                        <div style={{ fontSize: '0.65rem', color: '#6B7280', letterSpacing: '0.5px', fontWeight: 600 }}>FINTECH REGTECH SUITE</div>
                    </div>
                </div>
                <button className="btn-secondary">
                    <BarChart3 size={16} style={{ marginRight: 6 }} /> Analysis
                </button>
            </header>

            <main className="container" style={{ paddingTop: '4rem' }}>
                <h1>Automated Compliance Traceability</h1>
                <p className="subtitle">
                    Upload your regulatory documents, internal policies, and system configurations to generate an instant gap analysis and traceability matrix.
                </p>

                <div className="card-grid">
                    <Dropzone
                        title="Regulatory Standards"
                        description="Upload official regulations (PDF)"
                        iconType="shield"
                        onFileChange={setRegulation}
                    />
                    <Dropzone
                        title="Internal Policies"
                        description="Upload banking policy documents (DOCX)"
                        iconType="file"
                        onFileChange={setPolicy}
                    />
                    <Dropzone
                        title="System Configs"
                        description="Upload system rules or config exports (XLSX)"
                        iconType="settings"
                        onFileChange={setSystemRules}
                    />
                </div>

                <div style={{ display: 'flex', justifyContent: 'center' }}>
                    <button
                        className="btn-primary"
                        style={{ padding: '1rem 2rem', fontSize: '1.1rem', borderRadius: '12px' }}
                        onClick={handleSubmit}
                    >
                        <Sparkles size={20} /> Generate Traceability Report
                    </button>
                </div>
            </main>
        </div>
    );
};

export default Home;
