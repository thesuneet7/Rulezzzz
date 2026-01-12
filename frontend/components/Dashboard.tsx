
import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { FileText, Shield, Settings, ArrowLeft, CheckCircle } from 'lucide-react';

// Mock data for charts (as requested by user)
const PIE_DATA = [
    { name: 'MORTGAGE', value: 40, color: '#3B82F6' },
    { name: 'LENDING', value: 20, color: '#0EA5E9' },
    { name: 'CONSUMER_PROTECTION', value: 20, color: '#6366F1' },
    { name: 'KYC_AML', value: 20, color: '#8B5CF6' },
];

const BAR_DATA = [
    { name: 'HIGH', value: 3, fill: '#EF4444' },
    { name: 'MEDIUM', value: 0, fill: '#F59E0B' },
    { name: 'LOW', value: 2, fill: '#10B981' },
];

// Interface for compliance results from backend
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

interface DashboardProps {
    onBack: () => void;
    results?: ComplianceResult[];
    fileInfo?: FileInfo | null;
}

// Helper function to determine status based on compliance
function getStatus(policyCompliant: string, systemCompliant: string): string {
    if (policyCompliant === 'Yes' && systemCompliant === 'Yes') {
        return 'Compliant';
    } else if (policyCompliant === 'No' && systemCompliant === 'No') {
        return 'Critical Risk';
    } else {
        return 'Partial Risk';
    }
}

const Dashboard: React.FC<DashboardProps> = ({ onBack, results = [], fileInfo }) => {
    // Map backend results to table format
    const tableData = results.map((row, idx) => ({
        id: `REG-${String(idx + 1).padStart(3, '0')}`,
        req: row['Regulatory Clause'] || 'N/A',
        policy: row['Compliant with Bank Policy'] === 'Yes' ? '✓ Policy' : '✗ Policy',
        rule: row['Compliant with System Rules'] === 'Yes' ? '✓ System' : '✗ System',
        status: getStatus(row['Compliant with Bank Policy'], row['Compliant with System Rules']),
        gap: row['Explanation'] || 'No details available'
    }));

    // Get current date for display
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    return (
        <div className="container">
            {/* Header / Nav */}
            <div style={{ marginBottom: '2rem' }}>
                <button onClick={onBack} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <ArrowLeft size={16} /> Back to Upload
                </button>
            </div>

            <div style={{ marginBottom: '2rem' }}>
                <h1 style={{ textAlign: 'left', fontSize: '2rem' }}>Analysis Results</h1>
                <div style={{ color: '#6B7280', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>🕒 {dateStr}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '-40px', gap: '1rem' }}>
                    <span className="badge compliant" style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '1rem', padding: '0.5rem 1rem' }}>
                        <CheckCircle size={16} /> Analysis Complete
                    </span>
                    <button className="btn-primary">Download CSV</button>
                </div>
            </div>

            {/* Summary Cards - Show uploaded file names */}
            <div className="card-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
                <div className="chart-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: '#EFF6FF', padding: '10px', borderRadius: '8px' }}><FileText color="#3B82F6" /></div>
                    <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#9CA3AF', marginBottom: '2px' }}>REGULATORY DOC</div>
                        <div style={{ fontWeight: '600' }}>{fileInfo?.regulation || 'regulation.pdf'}</div>
                    </div>
                </div>
                <div className="chart-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: '#EFF6FF', padding: '10px', borderRadius: '8px' }}><FileText color="#3B82F6" /></div>
                    <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#9CA3AF', marginBottom: '2px' }}>POLICY DOC</div>
                        <div style={{ fontWeight: '600' }}>{fileInfo?.policy || 'policy.docx'}</div>
                    </div>
                </div>
                <div className="chart-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: '#EFF6FF', padding: '10px', borderRadius: '8px' }}><FileText color="#3B82F6" /></div>
                    <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#9CA3AF', marginBottom: '2px' }}>SYSTEM CONFIG</div>
                        <div style={{ fontWeight: '600' }}>{fileInfo?.system_rules || 'system_rules.xlsx'}</div>
                    </div>
                </div>
            </div>

            {/* Charts - Using MOCK data as requested */}
            <div className="dashboard-grid">
                <div className="chart-card">
                    <h3>By Category</h3>
                    <div style={{ height: 300 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                                    {PIE_DATA.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                        {/* Legend */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', justifyContent: 'center', fontSize: '0.8rem', marginTop: '10px' }}>
                            {PIE_DATA.map(d => (
                                <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                    <div style={{ width: 10, height: 10, background: d.color }}></div> {d.name}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="chart-card">
                    <h3>By Risk Level</h3>
                    <div style={{ height: 300 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={BAR_DATA}>
                                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                                <YAxis axisLine={false} tickLine={false} />
                                <Tooltip />
                                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                    {BAR_DATA.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Table - Using REAL data from backend */}
            <div className="chart-card" style={{ padding: '0', overflow: 'hidden' }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid #E5E7EB' }}>
                    <h3 style={{ margin: 0 }}>Gap Analysis Matrix</h3>
                    <p style={{ margin: '5px 0 0 0', color: '#6B7280', fontSize: '0.9rem' }}>
                        Generated compliance traceability report ({tableData.length} rules analyzed)
                    </p>
                </div>
                <table className="gap-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Regulatory Clause</th>
                            <th>Policy</th>
                            <th>System</th>
                            <th>Status</th>
                            <th>Gap Analysis</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tableData.length > 0 ? (
                            tableData.map((row, idx) => (
                                <tr key={idx}>
                                    <td style={{ color: '#6B7280' }}>{row.id}</td>
                                    <td style={{ color: '#374151', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.req}</td>
                                    <td style={{ color: row.policy.includes('✓') ? '#10B981' : '#EF4444' }}>{row.policy}</td>
                                    <td style={{ color: row.rule.includes('✓') ? '#10B981' : '#EF4444' }}>{row.rule}</td>
                                    <td>
                                        <span className={`badge ${row.status === 'Compliant' ? 'compliant' : row.status === 'Critical Risk' ? 'high' : 'medium'}`}>
                                            {row.status === 'Compliant' && <CheckCircle size={12} style={{ marginRight: 4, verticalAlign: 'text-bottom' }} />}
                                            {row.status}
                                        </span>
                                    </td>
                                    <td style={{ color: '#4B5563', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.gap}</td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#6B7280' }}>
                                    No compliance data available. Please run the analysis first.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Dashboard;
